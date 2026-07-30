from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Callable


IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            return text[end + 5 :]
    return text


def chapter_title(text: str, fallback: str) -> str:
    for line in strip_frontmatter(text).splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def inline_markup(value: str, image_resolver: Callable[[str], str] | None = None) -> str:
    placeholders: list[str] = []

    def image(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1), quote=True)
        source = match.group(2).strip()
        source = image_resolver(source) if image_resolver else source
        token = f"\x00IMG{len(placeholders)}\x00"
        placeholders.append(f'<img src="{html.escape(source, quote=True)}" alt="{alt}"/>')
        return token

    value = IMAGE_RE.sub(image, value)
    escaped = html.escape(value, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = html.escape(match.group(2), quote=True)
        return f'<a href="{href}">{label}</a>'

    escaped = LINK_RE.sub(link, escaped)
    for index, fragment in enumerate(placeholders):
        escaped = escaped.replace(html.escape(f"\x00IMG{index}\x00"), fragment)
        escaped = escaped.replace(f"\x00IMG{index}\x00", fragment)
    return escaped


def markdown_to_xhtml(text: str, image_resolver: Callable[[str], str] | None = None) -> str:
    lines = strip_frontmatter(text).replace("\r\n", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    in_ul = False
    in_ol = False
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            content = " ".join(part.strip() for part in paragraph if part.strip())
            if content:
                output.append(f"<p>{inline_markup(content, image_resolver)}</p>")
            paragraph = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            output.append("</ul>")
            in_ul = False
        if in_ol:
            output.append("</ol>")
            in_ol = False

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            close_lists()
            if in_code:
                output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            close_lists()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_lists()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or f"h-{len(output)}"
            output.append(f'<h{level} id="{anchor}">{inline_markup(title, image_resolver)}</h{level}>')
            continue
        unordered = re.match(r"^\s*[-*+]\s+(.+)$", line)
        if unordered:
            flush_paragraph()
            if in_ol:
                output.append("</ol>")
                in_ol = False
            if not in_ul:
                output.append("<ul>")
                in_ul = True
            output.append(f"<li>{inline_markup(unordered.group(1), image_resolver)}</li>")
            continue
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if ordered:
            flush_paragraph()
            if in_ul:
                output.append("</ul>")
                in_ul = False
            if not in_ol:
                output.append("<ol>")
                in_ol = True
            output.append(f"<li>{inline_markup(ordered.group(1), image_resolver)}</li>")
            continue
        if line.startswith("> "):
            flush_paragraph()
            close_lists()
            output.append(f"<blockquote><p>{inline_markup(line[2:].strip(), image_resolver)}</p></blockquote>")
            continue
        if line.startswith("---"):
            flush_paragraph()
            close_lists()
            output.append("<hr/>")
            continue
        paragraph.append(line)

    flush_paragraph()
    close_lists()
    if in_code:
        output.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(output)


def image_references(text: str) -> list[str]:
    return [match.group(2).strip() for match in IMAGE_RE.finditer(text)]


def manuscript_files(project_dir: Path) -> list[Path]:
    chapters = sorted((project_dir / "manuscript" / "chapters").glob("*.md"))
    if chapters:
        return chapters
    revisions = sorted((project_dir / "manuscript" / "revisions").glob("*.md"))
    if revisions:
        return revisions
    return sorted((project_dir / "manuscript").glob("*.md"))
