#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
for value in (str(HERE), str(SCRIPTS)):
    if value not in sys.path:
        sys.path.insert(0, value)

from hooklib import active_project, append_audit, project_root, read_input, structured_ask, structured_deny
from publishing_house.util import ensure_within, utc_now


# CLI-owned state under projects/<id>/: writes to these paths bypass the
# deterministic scripts that are the sole authority for state, artifacts,
# and approvals (rule 01-workflow-state, rule 03-artifact-provenance). Hard deny.
CLI_OWNED_STATE_PATTERNS = [
    re.compile(r"^projects/[^/]+/state\.json$"),
    re.compile(r"^projects/[^/]+/artifacts/manifest\.json$"),
    re.compile(r"^projects/[^/]+/approvals(/|$)"),
    re.compile(r"^projects/[^/]+/events\.ndjson$"),
]

# Shared harness/security configuration. Hard deny.
PROTECTED_CONFIG_FILES = {".claude/settings.json", ".mcp.json"}

# Previously hard-denied; downgraded to ask per the new posture (option 1:
# only CLI-owned state + harness config + sanctioned-egress stay hard).
PROTECTED_PARTS = {".git", ".env", "secrets", "credentials"}
PROTECTED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}

TEMP_DIR_PATTERNS = [
    r"/tmp/",
    r"/var/tmp/",
    r"/private/tmp/",
    r"/private/var/folders/",
    r"\$TMPDIR",
    r"\bTMPDIR\b",
    r"(^|/)\.tmp(/|$)",
    r"(^|/)tmp(/|$)",
]


def _is_temp_path_only(command: str) -> bool:
    """True if every rm target in the command looks like a temp path."""
    targets = re.findall(r"\brm\s+(?:-[A-Za-z-]+\s+)*([^\n;&|]+)", command, flags=re.IGNORECASE)
    if not targets:
        return False
    for target_group in targets:
        for token in shlex.split(target_group, posix=True):
            if token.startswith("-"):
                continue
            if not any(re.search(pattern, token) for pattern in TEMP_DIR_PATTERNS):
                return False
    return True


# Sanctioned-egress + external-publish verbs: these remain hard deny even
# under the relaxed posture (rule 11-external-side-effects).
HARD_DENY_PATTERNS = [
    (r"\byt-dlp\b(?![^\n]*--publishing-house-approved)", "yt-dlp is only permitted with an explicit reviewed flag"),
    (r"\b(kdp|amazon|ebay|apple)\b[^\n]*(submit|publish|upload|list|activate|purchase)", "marketplace publication must use an approved connector and release authorization"),
]

# External-writes soft net (only when PUBLISHING_EXTERNAL_WRITES != enabled).
# The sanctioned local CLI performs no external write, so it is exempt.
_PH_CLI_RE = re.compile(r"\bph_cli\.py\b")
# Scrub --operation/--op flag values (e.g. `--operation submit`) so a legitimate
# CLI operation name is not read as an external verb.
_OPERATION_VALUE_RE = re.compile(r"--op(?:eration)?[=\s]+\S+", re.IGNORECASE)
# Genuine external-publish verbs, bounded so they do NOT match inside a flag name
# or value (e.g. `spend` inside `--maximum-external-spend`, or a hyphenated flag).
_EXTERNAL_VERB_RE = re.compile(
    r"(?<![\w-])(submit|publish|upload|activate|purchase|spend|create-listing)(?![\w-])",
    re.IGNORECASE,
)

# General-risk operations: previously hard-denied, now escalate to the user
# for confirmation instead of failing outright.
ASK_PATTERNS = [
    (r"\bsudo\b", "this command requests privilege escalation (sudo)"),
    (r"\bgit\s+push\b", "this command pushes to a remote Git repository"),
    (r"\bgit\s+reset\s+--hard\b", "this command performs a destructive Git reset"),
    (r"\bgit\s+clean\s+-[^\n]*f", "this command performs a destructive Git clean"),
    (r"\b(curl|wget)\b[^\n]*(--data|-d\s|--request\s+(POST|PUT|PATCH|DELETE)|-X\s*(POST|PUT|PATCH|DELETE))", "this command performs an unreviewed network write"),
    (r"\b(aws|gcloud|az|terraform|kubectl)\b[^\n]*(apply|delete|destroy|create|deploy|publish|upload|put-object)", "this command performs a cloud infrastructure or upload write"),
    (r"\b(npm|pip|uv|brew|apt|apt-get|dnf|yum)\s+(publish|install|uninstall|remove)\b", "this command changes installed dependencies or packages"),
]


def _file_path(tool_input: dict, root: Path) -> Path | None:
    value = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _hard_denied_write(path: Path, root: Path) -> str | None:
    """CLI-owned state and harness config: never writable by the agent."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None
    as_posix = relative.as_posix()
    if as_posix in PROTECTED_CONFIG_FILES:
        return "shared harness/security configuration (.claude/settings.json, .mcp.json) is CLI/human-owned and cannot be written by the agent"
    for pattern in CLI_OWNED_STATE_PATTERNS:
        if pattern.search(as_posix):
            return "this path is CLI-owned workflow state/artifacts/approvals; only .claude/scripts/ph_cli.py may write it"
    return None


def _ask_worthy_write(path: Path, root: Path) -> str | None:
    """Previously hard-denied secret/.git-adjacent writes: now ask, not deny."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return "this write targets a path outside the repository"
    lowered = [part.lower() for part in relative.parts]
    if ".git" in lowered:
        return "this writes directly inside .git"
    if any(part.startswith(".env") for part in lowered):
        return "this writes to an environment/secret file"
    if any(part in PROTECTED_PARTS for part in lowered):
        return "this writes inside a secret or credential directory"
    if path.suffix.lower() in PROTECTED_SUFFIXES:
        return "this writes a private key or certificate file"
    return None


def main() -> int:
    payload = read_input()
    root = project_root(payload)
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    project_id = active_project(payload, root)
    record = {
        "time": utc_now(),
        "event": "PRE_TOOL_USE",
        "session_id": payload.get("session_id"),
        "tool": tool,
        "project_id": project_id,
    }

    def deny(reason: str) -> None:
        record.update({"decision": "deny", "reason": reason})
        if project_id:
            append_audit(root, record)
        structured_deny(reason)

    def ask(reason: str) -> None:
        record.update({"decision": "ask", "reason": reason})
        if project_id:
            append_audit(root, record)
        structured_ask(reason)

    if tool in {"Write", "Edit", "NotebookEdit"}:
        path = _file_path(tool_input, root)
        if path:
            record["path"] = str(path)
            hard_reason = _hard_denied_write(path, root)
            if hard_reason:
                deny(hard_reason)
            ask_reason = _ask_worthy_write(path, root)
            if ask_reason:
                ask(ask_reason)

    if tool == "Bash":
        command = str(tool_input.get("command") or "")
        record["command"] = command[:1000]

        for pattern, reason in HARD_DENY_PATTERNS:
            if re.search(pattern, command, flags=re.IGNORECASE):
                deny(reason)

        if os.environ.get("PUBLISHING_EXTERNAL_WRITES", "disabled").lower() != "enabled":
            # This soft net catches genuine external-publish verbs. Two refinements
            # keep it from false-positiving on the sanctioned local CLI and on flag
            # names/values that merely CONTAIN a verb:
            #   1. ph_cli.py is the framework's own offline entry point (it performs
            #      no external write; release-authorize only records a local
            #      authorization). Skip the net entirely for it.
            #   2. Match verbs only as genuine tokens, not inside flags like
            #      --maximum-external-spend or values like --operation submit. We
            #      first scrub --operation/--op values, then require the verb to be
            #      bounded by non-[word|dash] on both sides so `spend` does not match
            #      inside `--maximum-external-spend`.
            if not _PH_CLI_RE.search(command):
                scrubbed = _OPERATION_VALUE_RE.sub(" ", command)
                if _EXTERNAL_VERB_RE.search(scrubbed):
                    deny("external writes are disabled; create a package or dry-run record instead")

        if re.search(r"\brm\s+-[^\n]*r[^\n]*f\b|\brm\s+-rf\b", command, flags=re.IGNORECASE):
            if not _is_temp_path_only(command):
                ask("this command recursively force-deletes path(s) outside a temp directory")
            # else: recursive rm confined to temp paths — allow, no interception.

        for pattern, reason in ASK_PATTERNS:
            if re.search(pattern, command, flags=re.IGNORECASE):
                ask(f"{reason} and needs your confirmation")

    if tool.startswith("mcp__") and re.search(r"(?:create|update|delete|publish|submit|upload|purchase|send|post)", tool, re.IGNORECASE):
        ask("this write-capable MCP tool call needs your confirmation")

    if project_id:
        record["decision"] = "no-objection"
        append_audit(root, record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
