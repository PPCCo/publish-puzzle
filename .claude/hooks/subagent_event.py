#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
for value in (str(HERE), str(SCRIPTS)):
    if value not in sys.path:
        sys.path.insert(0, value)

from hooklib import active_project, append_audit, project_root, read_input
from publishing_house.events import append_event
from publishing_house.paths import ProjectPaths
from publishing_house.util import utc_now


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "event"
    payload = read_input()
    root = project_root(payload)
    project_id = active_project(payload, root)
    agent_type = payload.get("agent_type") or payload.get("subagent_type") or payload.get("agent_name") or "unknown"
    record = {
        "time": utc_now(),
        "event": f"SUBAGENT_{action.upper()}",
        "session_id": payload.get("session_id"),
        "agent_id": payload.get("agent_id"),
        "agent_type": agent_type,
        "project_id": project_id,
    }
    append_audit(root, record)
    if project_id:
        try:
            paths = ProjectPaths(root, project_id).require()
            append_event(paths.events, project_id, record["event"], "claude-code", {"agent_id": record.get("agent_id"), "agent_type": agent_type})
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
