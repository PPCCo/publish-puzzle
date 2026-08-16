from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .util import executable, load_json
from .validation import validate_framework

# Where the ComfyUI MCP bridge is installed next to ComfyUI (the deployed copy
# the .mcp.json points at). The reviewed source of truth lives in-repo at
# .claude/mcp/connectors/comfyui_mcp_bridge.py; doctor reports drift between the
# two by sha256. Overridable for non-default installs.
_INSTALLED_BRIDGE_ENV = "COMFYUI_BRIDGE_PATH"
_DEFAULT_INSTALLED_BRIDGE = "../image-tools/ComfyUI/comfyui_mcp_bridge.py"


def _sha256_bytes(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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

    # --- Image generation (offline core; never network-required) -------------
    # These checks read config + the local font registry only. mode is
    # informational: `manual-only` (the ships-by-default value) is expected, so
    # it is never a required failure. Auto mode without the live env flag is a
    # warning, not a failure — the manual path still works.
    try:
        from . import image_gen  # lazy: avoid importing Pillow-adjacent code at module load

        image_cfg = image_gen.image_generation_config(root)
        mode = image_cfg.get("mode", "manual-only")
        providers = image_gen.provider_registry(root)
        verified = [p for p in providers if p.get("commercial_rights_verified")]
        live_env = image_cfg.get("live_enabled_env", "IMAGE_GEN_LIVE_ENABLED")
        live_on = os.environ.get(live_env) == "1"
        add(
            "image-gen:mode",
            "pass" if mode == "manual-only" else ("warn" if mode == "auto" and not live_on else "pass"),
            f"mode={mode}; {len(providers)} providers ({len(verified)} rights-verified); {live_env}={'1' if live_on else 'unset'}",
            False,
        )
    except Exception as exc:  # noqa: BLE001
        add("image-gen:mode", "warn", f"image-gen config unavailable: {exc}", False)

    # --- Font clearance registry --------------------------------------------
    # cleared iff embedding_allowed AND commercial_use_verified. A registry with
    # zero cleared fonts is a warning (compositor would hard-fail on any font),
    # not a required failure, since a project may never composite text.
    try:
        from . import dependencies

        fonts = dependencies.font_registry(root)
        cleared = [f for f in fonts if dependencies.font_is_clearable(f)]
        add(
            "fonts:clearance",
            "pass" if cleared else ("warn" if fonts else "optional-missing"),
            f"{len(cleared)}/{len(fonts)} font families clearable (embedding + commercial-use verified)",
            False,
        )
    except Exception as exc:  # noqa: BLE001
        add("fonts:clearance", "warn", f"font registry unavailable: {exc}", False)

    # --- ComfyUI MCP bridge (best-effort; offline drift check) ---------------
    # The reviewed bridge lives in-repo; the deployed copy sits next to ComfyUI.
    # We report sha256 drift between the two. No network probe — ComfyUI
    # reachability is confirmed in-session via the comfyui-mcp health_check, not
    # from this offline command. Missing files are informational, never failures.
    connector = root / ".claude" / "mcp" / "connectors" / "comfyui_mcp_bridge.py"
    installed_raw = os.environ.get(_INSTALLED_BRIDGE_ENV) or _DEFAULT_INSTALLED_BRIDGE
    installed = Path(installed_raw)
    if not installed.is_absolute():
        installed = (root / installed_raw).resolve()
    connector_hash = _sha256_bytes(connector) if connector.is_file() else None
    installed_hash = _sha256_bytes(installed) if installed.is_file() else None
    if connector_hash is None:
        add("bridge:connector", "optional-missing", "reviewed bridge connector not present in-repo yet", False)
    elif installed_hash is None:
        add("bridge:connector", "optional-missing", f"connector present; deployed copy not found at {installed_raw}", False)
    elif connector_hash == installed_hash:
        add("bridge:connector", "pass", f"connector matches deployed copy ({connector_hash[:14]}…)", False)
    else:
        add("bridge:connector", "warn", f"DRIFT: connector {connector_hash[:14]}… != deployed {installed_hash[:14]}…", False)

    failures = [item for item in checks if item["required"] and item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] in {"warn", "optional-missing"}]
    return {
        "status": "pass" if not failures else "fail",
        "root": root.as_posix(),
        "checks": checks,
        "required_failures": len(failures),
        "warnings": len(warnings),
    }
