#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
for value in (str(HERE), str(SCRIPTS)):
    if value not in sys.path:
        sys.path.insert(0, value)

from hooklib import active_project, project_root, read_input
from publishing_house.events import append_event
from publishing_house.paths import ProjectPaths
from publishing_house.util import sha256_path, utc_now


def main() -> int:
    payload = read_input()
    root = project_root(payload)
    project_id = active_project(payload, root)
    if not project_id:
        return 0
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    path_value = tool_input.get("file_path") or tool_input.get("path")
    path_str = None
    digest = None
    if path_value:
        path = Path(str(path_value))
        if not path.is_absolute():
            path = root / path
        try:
            if path.exists() and path.is_file():
                digest, _ = sha256_path(path)
                path_str = str(path.resolve())
        except OSError:
            pass
    try:
        paths = ProjectPaths(root, project_id).require()
        append_event(paths.events, project_id, "CLAUDE_TOOL_USED", "claude-code", {"tool": tool, "path": path_str, "sha256": digest})
    except Exception:  # noqa: BLE001
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
