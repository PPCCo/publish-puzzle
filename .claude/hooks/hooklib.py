from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


def read_input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {}


def project_root(payload: dict[str, Any]) -> Path:
    configured = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PUBLISHING_REPO_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    cwd = Path(payload.get("cwd") or os.getcwd()).resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / ".claude" / "CLAUDE.md").is_file():
            return candidate
    return cwd


def project_id_from_path(value: str | None, root: Path) -> str | None:
    if not value:
        return None
    try:
        path = Path(value)
        if not path.is_absolute():
            path = (root / path).resolve()
        relative = path.resolve().relative_to((root / "projects").resolve())
        return relative.parts[0] if relative.parts else None
    except (ValueError, OSError):
        return None


def active_project(payload: dict[str, Any], root: Path) -> str | None:
    env_id = os.environ.get("PUBLISHING_PROJECT_ID")
    if env_id:
        return env_id
    tool_input = payload.get("tool_input") or {}
    for key in ("file_path", "path", "notebook_path"):
        found = project_id_from_path(tool_input.get(key), root)
        if found:
            return found
    command = str(tool_input.get("command") or "")
    match = re.search(r"(?:^|[\s'\"])(?:projects/)?(bk-[a-z0-9-]+)(?:[\s/'\"]|$)", command)
    return match.group(1) if match else None


def append_audit(root: Path, record: dict[str, Any]) -> None:
    target = root / ".claude" / "logs" / "hooks.ndjson"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def deny(reason: str) -> None:
    print(reason, file=sys.stderr)
    raise SystemExit(2)


def structured_deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    raise SystemExit(0)


def structured_ask(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))
    raise SystemExit(0)
