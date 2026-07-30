#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
for value in (str(HERE), str(SCRIPTS)):
    if value not in sys.path:
        sys.path.insert(0, value)

from hooklib import append_audit, project_root, read_input
from publishing_house.util import utc_now


def main() -> int:
    payload = read_input()
    root = project_root(payload)
    changed: list[str] = []
    try:
        result = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=5, check=False)
        changed = [line for line in result.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    append_audit(root, {
        "time": utc_now(),
        "event": "SESSION_TURN_STOP",
        "session_id": payload.get("session_id"),
        "changed_file_count": len(changed),
        "changed_files": changed[:200],
        "stop_hook_active": bool(payload.get("stop_hook_active")),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
