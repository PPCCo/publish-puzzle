from __future__ import annotations

import importlib.util
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .util import executable, load_json
from .validation import validate_framework


def _version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (result.stdout or result.stderr or "").strip().splitlines()
    return text[0] if text else None


def run_doctor(root: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, status: str, detail: str, required: bool = False) -> None:
        checks.append({"name": name, "status": status, "detail": detail, "required": required})

    py_ok = sys.version_info >= (3, 11)
    add("python", "pass" if py_ok else "fail", platform.python_version(), True)

    for module, required in [("yaml", True), ("jsonschema", True), ("PIL", True), ("reportlab", True), ("mcp", False)]:
        found = importlib.util.find_spec(module) is not None
        add(f"python:{module}", "pass" if found else ("fail" if required else "optional-missing"), "installed" if found else "not installed", required)

    settings_path = root / ".claude" / "settings.json"
    try:
        settings = load_json(settings_path)
        add("settings", "pass", "valid JSON", True)
        writes = settings.get("env", {}).get("PUBLISHING_EXTERNAL_WRITES")
        add("external-writes-default", "pass" if writes == "disabled" else "warn", str(writes), True)
    except Exception as exc:  # noqa: BLE001
        add("settings", "fail", str(exc), True)

    claude = executable("claude")
    if claude:
        version = _version([claude, "--version"]) or "installed"
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        status = "pass"
        if match and tuple(map(int, match.groups())) < (2, 1, 211):
            status = "fail"
        add("claude-code", status, version, True)
    else:
        add("claude-code", "fail", "claude executable not found", True)

    optional_tools = {
        "git": ["git", "--version"],
        "epubcheck": ["epubcheck", "--version"],
        "ffmpeg": ["ffmpeg", "-version"],
        "ffprobe": ["ffprobe", "-version"],
        "pandoc": ["pandoc", "--version"],
        "vivliostyle": ["vivliostyle", "--version"],
        "imagemagick": ["magick", "-version"],
    }
    for name, command in optional_tools.items():
        installed = executable(command[0]) is not None
        add(f"tool:{name}", "pass" if installed else "optional-missing", _version(command) or "not installed", False)

    framework = validate_framework(root)
    add("framework", "pass" if framework.get("status") == "pass" else "fail", f"{sum(framework.get('counts', {}).values())} framework components; {len(framework.get('errors', []))} errors", True)

    mcp_config = root / ".mcp.json"
    try:
        data = load_json(mcp_config)
        configured = "publishing-house" in data.get("mcpServers", {})
        add("mcp-config", "pass" if configured else "fail", "publishing-house server configured" if configured else "server missing", True)
    except Exception as exc:  # noqa: BLE001
        add("mcp-config", "fail", str(exc), True)

    failures = [item for item in checks if item["required"] and item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] in {"warn", "optional-missing"}]
    return {
        "status": "pass" if not failures else "fail",
        "root": root.as_posix(),
        "checks": checks,
        "required_failures": len(failures),
        "warnings": len(warnings),
    }
