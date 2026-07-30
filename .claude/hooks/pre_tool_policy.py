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

from hooklib import active_project, append_audit, project_root, read_input, structured_deny
from publishing_house.util import ensure_within, utc_now


PROTECTED_PARTS = {".git", ".env", "secrets", "credentials"}
PROTECTED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
HIGH_RISK_PATTERNS = [
    (r"\brm\s+-[^\n]*r[^\n]*f\b|\brm\s+-rf\b", "recursive forced deletion is prohibited"),
    (r"\bsudo\b", "privilege escalation is prohibited"),
    (r"\bgit\s+push\b", "remote Git writes require direct human execution"),
    (r"\bgit\s+reset\s+--hard\b", "destructive Git reset is prohibited"),
    (r"\bgit\s+clean\s+-[^\n]*f", "destructive Git cleaning is prohibited"),
    (r"\b(curl|wget)\b[^\n]*(--data|-d\s|--request\s+(POST|PUT|PATCH|DELETE)|-X\s*(POST|PUT|PATCH|DELETE))", "unreviewed network writes are prohibited"),
    (r"\b(aws|gcloud|az|terraform|kubectl)\b[^\n]*(apply|delete|destroy|create|deploy|publish|upload|put-object)", "cloud infrastructure or upload writes are prohibited"),
    (r"\b(npm|pip|uv|brew|apt|apt-get|dnf|yum)\s+(publish|install|uninstall|remove)\b", "dependency or package changes require explicit human control"),
    (r"\b(kdp|amazon|ebay|apple)\b[^\n]*(submit|publish|upload|list|activate|purchase)", "marketplace publication must use an approved connector and release authorization"),
]


def _file_path(tool_input: dict, root: Path) -> Path | None:
    value = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path")
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _protected(path: Path, root: Path) -> str | None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return "writes outside the repository are prohibited"
    lowered = [part.lower() for part in relative.parts]
    if ".git" in lowered:
        return "direct edits inside .git are prohibited"
    if any(part.startswith(".env") for part in lowered):
        return "environment and secret files are protected"
    if any(part in PROTECTED_PARTS for part in lowered):
        return "secret or credential directories are protected"
    if path.suffix.lower() in PROTECTED_SUFFIXES:
        return "private key and certificate files are protected"
    if relative.as_posix() in {".claude/settings.json", ".mcp.json"}:
        return "shared security configuration requires direct human editing or a reviewed change request"
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

    if tool in {"Write", "Edit", "NotebookEdit"}:
        path = _file_path(tool_input, root)
        if path:
            reason = _protected(path, root)
            if reason:
                record.update({"decision": "deny", "reason": reason, "path": str(path)})
                if project_id:
                    append_audit(root, record)
                structured_deny(reason)
            record["path"] = str(path)

    if tool == "Bash":
        command = str(tool_input.get("command") or "")
        record["command"] = command[:1000]
        for pattern, reason in HIGH_RISK_PATTERNS:
            if re.search(pattern, command, flags=re.IGNORECASE):
                record.update({"decision": "deny", "reason": reason})
                if project_id:
                    append_audit(root, record)
                structured_deny(reason)
        if os.environ.get("PUBLISHING_EXTERNAL_WRITES", "disabled").lower() != "enabled":
            if re.search(r"\b(submit|publish|upload|activate|purchase|spend|create-listing)\b", command, re.IGNORECASE):
                reason = "external writes are disabled; create a package or dry-run record instead"
                record.update({"decision": "deny", "reason": reason})
                if project_id:
                    append_audit(root, record)
                structured_deny(reason)

    if tool.startswith("mcp__") and re.search(r"(?:create|update|delete|publish|submit|upload|purchase|send|post)", tool, re.IGNORECASE):
        reason = "write-capable MCP tools are not approved by the baseline framework"
        record.update({"decision": "deny", "reason": reason})
        if project_id:
            append_audit(root, record)
        structured_deny(reason)

    if project_id:
        record["decision"] = "no-objection"
        append_audit(root, record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
