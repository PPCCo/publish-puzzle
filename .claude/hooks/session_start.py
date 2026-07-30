#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
for value in (str(HERE), str(SCRIPTS)):
    if value not in sys.path:
        sys.path.insert(0, value)

from hooklib import project_root, read_input
from publishing_house.project import list_projects
from publishing_house.util import load_json


def main() -> int:
    payload = read_input()
    root = project_root(payload)
    settings = load_json(root / ".claude" / "settings.json", {})
    projects = list_projects(root)
    active = [item for item in projects if item.get("state") not in {"PUBLISHED", "ERROR"}]
    print(
        "Publishing House session context:\n"
        f"- Repository: {root}\n"
        f"- Required model pin: {settings.get('model', 'unknown')}\n"
        f"- External writes: {settings.get('env', {}).get('PUBLISHING_EXTERNAL_WRITES', 'unknown')}\n"
        f"- Projects: {len(projects)} total, {len(active)} active\n"
        "- Run /product-status or /product-resume with a project ID before modifying a product.\n"
        "- Human approvals, release authorization, spending, legal acceptance, and public publication cannot be inferred."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
