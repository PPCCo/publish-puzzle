from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, RefResolver

from .util import load_json, load_yaml

def schema_store(root: Path) -> dict[str, Any]:
    store: dict[str, Any] = {}
    schema_dir = root / ".claude" / "schemas"
    for path in schema_dir.glob("*.schema.json"):
        schema = load_json(path)
        store[path.name] = schema
        store[path.as_uri()] = schema
        if "$id" in schema:
            store[schema["$id"]] = schema
    return store


def validate_data(root: Path, data: Any, schema_name: str) -> list[str]:
    schema_path = root / ".claude" / "schemas" / schema_name
    schema = load_json(schema_path)
    resolver = RefResolver(base_uri=schema_path.as_uri(), referrer=schema, store=schema_store(root))
    validator = Draft202012Validator(schema, resolver=resolver, format_checker=Draft202012Validator.FORMAT_CHECKER)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))
    output: list[str] = []
    for error in errors:
        location = "/".join(str(part) for part in error.absolute_path) or "$"
        output.append(f"{location}: {error.message}")
    return output


def validate_file(root: Path, path: Path, schema_name: str) -> list[str]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = load_yaml(path)
    else:
        data = load_json(path)
    return validate_data(root, data, schema_name)


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError(f"Unclosed frontmatter: {path}")
    raw = text[4:end]
    return yaml.safe_load(raw) or {}, text[end + 5 :]


def validate_framework(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        ".claude/CLAUDE.md",
        ".claude/settings.json",
        ".mcp.json",
        ".claude/scripts/ph_cli.py",
        ".claude/config/workflow_states.json",
        ".claude/config/quality_gates.json",
    ]
    for rel in required:
        if not (root / rel).is_file():
            errors.append(f"Missing required file: {rel}")

    for path in list((root / ".claude" / "config").rglob("*.json")) + list((root / ".claude" / "schemas").glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Invalid JSON {path.relative_to(root)}: {exc}")

    try:
        settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        env = settings.get("env", {})
        if env.get("PUBLISHING_EXTERNAL_WRITES") != "disabled":
            errors.append("PUBLISHING_EXTERNAL_WRITES must default to disabled")
        if env.get("CLAUDE_CODE_MCP_ALLOWLIST_ENV") != "1":
            errors.append("CLAUDE_CODE_MCP_ALLOWLIST_ENV must be enabled")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid project settings: {exc}")

    try:
        mcp = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))
        server = mcp.get("mcpServers", {}).get("publishing-house", {})
        args = server.get("args", [])
        if not any("${CLAUDE_PROJECT_DIR:-.}" in str(value) for value in args):
            errors.append("Project MCP args must use a CLAUDE_PROJECT_DIR fallback")
        if server.get("env", {}).get("PUBLISHING_EXTERNAL_WRITES") != "disabled":
            errors.append("Publishing MCP external writes must default to disabled")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Invalid MCP configuration: {exc}")

    agent_names: set[str] = set()
    for path in (root / ".claude" / "agents").rglob("*.md"):
        if path.name in {"README.md", "CATALOG.md"}:
            continue
        try:
            fm, _ = parse_frontmatter(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            continue
        for key in ("name", "description"):
            if not fm.get(key):
                errors.append(f"Agent {path.relative_to(root)} missing {key}")
        name = fm.get("name")
        if name in agent_names:
            errors.append(f"Duplicate agent name: {name}")
        agent_names.add(name)

    skill_names: set[str] = set()
    for path in (root / ".claude" / "skills").glob("*/SKILL.md"):
        try:
            fm, body = parse_frontmatter(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))
            continue
        name = fm.get("name") or path.parent.name
        if name in skill_names:
            errors.append(f"Duplicate skill name: {name}")
        skill_names.add(name)
        if not fm.get("description"):
            errors.append(f"Skill {name} missing description")
        if len(body.splitlines()) > 500:
            warnings.append(f"Skill {name} exceeds 500 body lines")

    # Only skills that perform or record an irreversible / outward-facing action stay
    # locked to human invocation. Approval/authorization gate skills are model-invocable
    # by design: the assistant presents the gate interactively and records the human's
    # explicit decision, bound to exact artifact hashes (human authority is preserved by
    # the hash binding, not by forcing a typed command).
    locked_skills = {
        "product-submit", "product-incident", "product-freeze",
    }
    approval_skills = {
        "product-approve-niche", "product-approve-interior", "product-approve-cover",
        "product-approve-compliance", "product-approve-listing",
        "product-release-authorize",
    }
    for name in locked_skills:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        if not path.exists():
            errors.append(f"Missing locked skill: {name}")
            continue
        fm, _ = parse_frontmatter(path)
        if fm.get("disable-model-invocation") is not True:
            errors.append(f"External-effect skill is model-invocable: {name}")
    for name in approval_skills:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        if not path.exists():
            errors.append(f"Missing approval skill: {name}")
            continue
        fm, _ = parse_frontmatter(path)
        if fm.get("disable-model-invocation") is True:
            errors.append(
                f"Approval gate skill must stay model-invocable for the interactive "
                f"flow: {name}"
            )

    if len(agent_names) < 30:
        errors.append(f"Expected at least 30 agents, found {len(agent_names)}")
    if len(skill_names) < 30:
        errors.append(f"Expected at least 30 skills, found {len(skill_names)}")

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "agents": len(agent_names),
            "skills": len(skill_names),
            "workflows": len(list((root / ".claude" / "workflows").glob("*.js"))),
            "schemas": len(list((root / ".claude" / "schemas").glob("*.json"))),
        },
    }
