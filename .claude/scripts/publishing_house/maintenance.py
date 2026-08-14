"""Occasional-use framework-maintenance: scan logs + memory, promote durable
learnings into the framework, prune the source memory only after the learning is
verifiably embedded.

Rationale: durable learnings currently live in machine-local memory
(``~/.claude/projects/.../memory/*.md``), which is NOT part of the repository or
``.claude/`` and so does not travel to another machine. This module PROMOTES a
learning into the framework (a deterministic check, an auto-registration, a test)
and then PRUNES the now-redundant memory file — but only after
``verify_promotion`` confirms the durable fix is actually present.

Hard invariants (enforced by construction, not convention):

- ``events.ndjson`` is the append-only product audit trail. This module NEVER
  reads it for signals beyond gate-decision extraction, and NEVER truncates,
  rotates, or deletes it. ``rotate_hooks_log`` only accepts the hooks log path,
  so rotating ``events.ndjson`` is impossible.
- "Already embedded?" is decided by exact sentinel substrings in named framework
  files (deterministic), never by an LLM.
- ``prune_memory`` refuses unless the learning's registry status is ``applied``
  AND ``verify_promotion`` passes, and it removes only that one ``.md`` file plus
  its single ``MEMORY.md`` index line.

The module is stdlib + local-import only, deterministic, and performs no network.
Reports are written under a repo-root ``maintenance/`` directory (a sibling of
``projects/``), which is outside the pre-tool hook's CLI-owned state patterns.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .util import atomic_write_json, atomic_write_text, load_json, sha256_file, utc_now
from .validation import parse_frontmatter, validate_data

# Default machine-local memory directory. Absent on other machines / in tests;
# every caller degrades gracefully to an empty result when it does not exist.
DEFAULT_MEMORY_DIR = Path(
    "~/.claude/projects/-Users-qaiser-abbas-Dev-my-repos-pub-pub-clr/memory"
).expanduser()

_REGISTRY_REL = ".claude/config/framework_learnings.json"
_REGISTRY_SCHEMA = "framework-learnings.schema.json"

# A hook deny/ask whose command names the sanctioned local CLI is a candidate
# false positive: ph_cli.py is the framework's own offline entry point and must
# never be blocked by the external-writes soft net.
_PH_CLI_RE = re.compile(r"\bph_cli\.py\b")
# The external-writes soft net's own verbs (mirrors pre_tool_policy). A deny whose
# reason mentions external writes AND whose command is a ph_cli.py invocation is a
# false-positive signal worth surfacing.
_EXTERNAL_WRITE_REASON_RE = re.compile(r"external writes are disabled", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# NDJSON reading (tolerant)
# --------------------------------------------------------------------------- #
def _iter_ndjson(path: Path) -> list[dict[str, Any]]:
    """Read an NDJSON file, skipping blank/malformed lines. Never raises."""
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict):
            records.append(obj)
    return records


def _hooks_log_path(root: Path, hooks_log: Path | None) -> Path:
    return hooks_log if hooks_log is not None else root / ".claude" / "logs" / "hooks.ndjson"


# --------------------------------------------------------------------------- #
# Signal scan (logs)
# --------------------------------------------------------------------------- #
def scan_signals(
    root: Path,
    *,
    hooks_log: Path | None = None,
    project_events: list[Path] | None = None,
) -> dict[str, Any]:
    """Read-only aggregate over the hooks log + project events.

    Surfaces: ranked hook deny/ask reasons, likely FALSE-POSITIVE denies (a deny
    whose command is a ``ph_cli.py`` invocation with an external-writes reason),
    late-stage gate FAILs, and repeated manual ``artifact register`` workarounds.
    Never writes NDJSON; tolerates malformed/heterogeneous lines.
    """
    hooks_path = _hooks_log_path(root, hooks_log)
    hook_records = _iter_ndjson(hooks_path)

    deny_reasons: dict[str, int] = {}
    ask_reasons: dict[str, int] = {}
    false_positive_denies: list[dict[str, Any]] = []
    for rec in hook_records:
        decision = str(rec.get("decision") or "")
        reason = str(rec.get("reason") or "")
        command = str(rec.get("command") or "")
        if decision == "deny":
            deny_reasons[reason] = deny_reasons.get(reason, 0) + 1
            # A deny of the sanctioned local CLI for an external-writes reason is
            # a false positive: ph_cli.py performs no external write.
            if _PH_CLI_RE.search(command) and _EXTERNAL_WRITE_REASON_RE.search(reason):
                false_positive_denies.append(
                    {"command": command[:300], "reason": reason, "project_id": rec.get("project_id")}
                )
        elif decision == "ask":
            ask_reasons[reason] = ask_reasons.get(reason, 0) + 1

    # Project events: late-stage gate FAILs and manual artifact-register workarounds.
    if project_events is None:
        projects_dir = root / "projects"
        project_events = sorted(projects_dir.glob("*/events.ndjson")) if projects_dir.is_dir() else []
    late_gate_fails: list[dict[str, Any]] = []
    manual_registers: dict[str, int] = {}
    for events_path in project_events:
        for rec in _iter_ndjson(events_path):
            event = str(rec.get("event") or "")
            detail = rec.get("detail") or {}
            if isinstance(detail, dict) and str(detail.get("decision")).upper() == "FAIL":
                late_gate_fails.append(
                    {
                        "project_id": rec.get("project_id"),
                        "event": event,
                        "detail": {k: detail.get(k) for k in ("decision", "issues", "unlinked", "blocked")},
                    }
                )
            if event == "ARTIFACT_REGISTERED" and isinstance(detail, dict):
                atype = str(detail.get("type") or "")
                if atype in {"rights-gate", "rights-ledger", "accessibility-gate"}:
                    manual_registers[atype] = manual_registers.get(atype, 0) + 1

    return {
        "hooks_log": _rel(root, hooks_path),
        "hook_record_count": len(hook_records),
        "deny_reasons": _rank(deny_reasons),
        "ask_reasons": _rank(ask_reasons),
        "false_positive_denies": false_positive_denies,
        "late_stage_gate_fails": late_gate_fails,
        "compliance_artifact_registrations": manual_registers,
    }


def _rank(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"reason": reason, "count": count}
        for reason, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Registry helpers
# --------------------------------------------------------------------------- #
def _registry_path(root: Path) -> Path:
    return root / _REGISTRY_REL


def load_registry(root: Path) -> dict[str, Any]:
    return load_json(_registry_path(root), {"schema_version": "1.0", "learnings": []})


def _find_learning(registry: dict[str, Any], learning_id: str) -> dict[str, Any] | None:
    return next((entry for entry in registry.get("learnings", []) if entry.get("id") == learning_id), None)


def _write_registry(root: Path, registry: dict[str, Any]) -> None:
    errors = validate_data(root, registry, _REGISTRY_SCHEMA)
    if errors:
        raise ValueError("framework_learnings registry failed schema validation: " + "; ".join(errors))
    atomic_write_json(_registry_path(root), registry)


# --------------------------------------------------------------------------- #
# Memory scan
# --------------------------------------------------------------------------- #
def scan_memories(root: Path, memory_dir: Path | None = None) -> list[dict[str, Any]]:
    """Parse each memory ``.md`` and classify it against the promotion registry.

    Classifications:
      - ``already-embedded-prunable`` — registry entry is ``applied`` and its
        durable fix verifies present; the memory is now redundant and prunable.
      - ``promotable-auto`` — a mapped ``auto_apply`` learning not yet embedded.
      - ``promotable-manual`` — a mapped learning that changes gate/policy
        semantics; must be presented to a human, never auto-applied.
      - ``unmapped`` — no registry entry references this memory.
    Degrades to an empty list when the memory directory is absent.
    """
    memory_dir = (memory_dir or DEFAULT_MEMORY_DIR)
    if not memory_dir.is_dir():
        return []
    registry = load_registry(root)
    results: list[dict[str, Any]] = []
    for md in sorted(memory_dir.glob("*.md")):
        if md.name == "MEMORY.md":
            continue
        try:
            fm, _body = parse_frontmatter(md)
        except Exception:  # noqa: BLE001
            fm = {}
        name = str(fm.get("name") or md.stem)
        entry = next(
            (e for e in registry.get("learnings", []) if name in e.get("matches_memory", [])),
            None,
        )
        if entry is None:
            results.append({"memory": md.name, "name": name, "classification": "unmapped", "learning_id": None})
            continue
        verification = verify_promotion(root, entry["id"])
        if entry.get("status") == "applied" and verification["verified"]:
            classification = "already-embedded-prunable"
        elif not entry.get("auto_apply", False):
            classification = "promotable-manual"
        else:
            classification = "promotable-auto"
        results.append(
            {
                "memory": md.name,
                "name": name,
                "classification": classification,
                "learning_id": entry["id"],
                "status": entry.get("status"),
                "verified": verification["verified"],
            }
        )
    return results


# --------------------------------------------------------------------------- #
# Compose + persist a scan
# --------------------------------------------------------------------------- #
def scan(
    root: Path,
    *,
    memory_dir: Path | None = None,
    hooks_log: Path | None = None,
    write: bool = True,
) -> dict[str, Any]:
    signals = scan_signals(root, hooks_log=hooks_log)
    memories = scan_memories(root, memory_dir)
    registry = load_registry(root)
    result = {
        "schema_version": "1.0",
        "kind": "framework-maintenance-scan",
        "generated_at": utc_now(),
        "signals": signals,
        "memories": memories,
        "registry_summary": [
            {"id": e.get("id"), "status": e.get("status"), "auto_apply": e.get("auto_apply")}
            for e in registry.get("learnings", [])
        ],
    }
    if write:
        atomic_write_json(root / "maintenance" / "scan-latest.json", result)
        _append_log(root, {"action": "scan", "memories": len(memories), "false_positive_denies": len(signals["false_positive_denies"])})
    return result


# --------------------------------------------------------------------------- #
# Verify a promotion (deterministic)
# --------------------------------------------------------------------------- #
def verify_promotion(root: Path, learning_id: str) -> dict[str, Any]:
    """Confirm every sentinel substring is present in its file and the test exists."""
    registry = load_registry(root)
    entry = _find_learning(registry, learning_id)
    if entry is None:
        return {"learning_id": learning_id, "verified": False, "error": "unknown learning id"}
    missing_sentinels: list[dict[str, str]] = []
    for sentinel in entry.get("sentinels", []):
        file_path = root / sentinel["file"]
        contains = sentinel["contains"]
        present = False
        if file_path.is_file():
            try:
                present = contains in file_path.read_text(encoding="utf-8")
            except Exception:  # noqa: BLE001
                present = False
        if not present:
            missing_sentinels.append(sentinel)
    test_rel = entry.get("test")
    test_present = bool(test_rel) and (root / test_rel).is_file() if test_rel else True
    verified = not missing_sentinels and test_present
    return {
        "learning_id": learning_id,
        "verified": verified,
        "missing_sentinels": missing_sentinels,
        "test": test_rel,
        "test_present": test_present,
    }


# --------------------------------------------------------------------------- #
# Promote
# --------------------------------------------------------------------------- #
def promote(root: Path, learning_id: str, *, apply: bool = False, actor: str = "framework-maintenance") -> dict[str, Any]:
    """Record a promotion.

    ``apply=False`` records the proposal (status ``reported``) and the sentinels a
    human/skill would check. ``apply=True`` re-verifies the durable fix is present
    (the code edits themselves land through the ordinary edit workflow + tests, not
    through this function) and, only for ``auto_apply`` entries, stamps the registry
    ``applied`` with the changed-file hashes. Idempotent by id.
    """
    registry = load_registry(root)
    entry = _find_learning(registry, learning_id)
    if entry is None:
        raise ValueError(f"Unknown learning id: {learning_id}")

    verification = verify_promotion(root, learning_id)
    if not apply:
        if entry.get("status") == "reported":
            entry.setdefault("proposed_at", utc_now())
        _write_registry(root, registry)
        _append_log(root, {"action": "promote-report", "learning_id": learning_id, "verified": verification["verified"]})
        return {"learning_id": learning_id, "mode": "report", "status": entry.get("status"), "verification": verification}

    if not entry.get("auto_apply", False):
        raise ValueError(
            f"Learning {learning_id} is not auto_apply; it changes gate/policy semantics and must be "
            "presented to a human, never auto-applied."
        )
    if not verification["verified"]:
        raise ValueError(
            f"Cannot mark {learning_id} applied: durable fix not verifiably present "
            f"(missing sentinels: {verification['missing_sentinels']}, test_present={verification['test_present']}). "
            "Land the framework edit + test first."
        )
    changed_files = []
    for sentinel in entry.get("sentinels", []):
        file_path = root / sentinel["file"]
        if file_path.is_file():
            digest = sha256_file(file_path)
            if not any(cf["path"] == sentinel["file"] for cf in changed_files):
                changed_files.append({"path": sentinel["file"], "sha256": digest})
    entry["status"] = "applied"
    entry["changed_files"] = changed_files
    entry["applied_at"] = entry.get("applied_at") or utc_now()
    entry["applied_by"] = actor
    entry["verified_at"] = utc_now()
    _write_registry(root, registry)
    _append_log(root, {"action": "promote-apply", "learning_id": learning_id, "changed_files": len(changed_files)})
    return {"learning_id": learning_id, "mode": "apply", "status": "applied", "changed_files": changed_files, "verification": verification}


# --------------------------------------------------------------------------- #
# Prune (memory removal, only after verified promotion)
# --------------------------------------------------------------------------- #
def prune_memory(root: Path, learning_id: str, *, memory_dir: Path | None = None) -> dict[str, Any]:
    """Remove the memory file(s) for a learning, but ONLY when it is verifiably
    embedded in the framework.

    Preconditions (all required): registry status ``applied`` AND
    ``verify_promotion`` passes. Removes only the mapped ``.md`` file(s) and their
    single ``MEMORY.md`` index line each. NEVER touches ``events.ndjson`` — it is
    not in this function's reach by construction (it operates only inside
    ``memory_dir``).
    """
    memory_dir = (memory_dir or DEFAULT_MEMORY_DIR)
    registry = load_registry(root)
    entry = _find_learning(registry, learning_id)
    if entry is None:
        raise ValueError(f"Unknown learning id: {learning_id}")
    if entry.get("status") != "applied":
        raise ValueError(
            f"Refusing to prune {learning_id}: registry status is {entry.get('status')!r}, not 'applied'. "
            "A memory is pruned only after its learning is verifiably embedded."
        )
    verification = verify_promotion(root, learning_id)
    if not verification["verified"]:
        raise ValueError(
            f"Refusing to prune {learning_id}: durable fix not verifiably present "
            f"(missing sentinels: {verification['missing_sentinels']})."
        )
    if not memory_dir.is_dir():
        return {"learning_id": learning_id, "pruned_files": [], "note": "memory directory absent; nothing to prune", "index_lines_removed": 0}

    removed_files: list[str] = []
    index_lines_removed = 0
    memory_names = set(entry.get("matches_memory", []))
    for md in sorted(memory_dir.glob("*.md")):
        if md.name == "MEMORY.md":
            continue
        try:
            fm, _body = parse_frontmatter(md)
        except Exception:  # noqa: BLE001
            fm = {}
        name = str(fm.get("name") or md.stem)
        if name in memory_names:
            md.unlink()
            removed_files.append(md.name)

    # Remove only the index lines that reference a removed file, from MEMORY.md.
    index_path = memory_dir / "MEMORY.md"
    if index_path.is_file() and removed_files:
        lines = index_path.read_text(encoding="utf-8").splitlines()
        kept: list[str] = []
        for line in lines:
            if any(f"({fname})" in line or f"]({fname})" in line for fname in removed_files):
                index_lines_removed += 1
                continue
            kept.append(line)
        atomic_write_text(index_path, "\n".join(kept) + ("\n" if kept else ""))

    entry["status"] = "pruned"
    entry["pruned_at"] = utc_now()
    _write_registry(root, registry)
    _append_log(root, {"action": "prune", "learning_id": learning_id, "removed_files": removed_files, "index_lines_removed": index_lines_removed})
    return {
        "learning_id": learning_id,
        "pruned_files": removed_files,
        "index_lines_removed": index_lines_removed,
        "note": "events.ndjson never touched; only memory .md + MEMORY.md index lines removed.",
    }


# --------------------------------------------------------------------------- #
# Rotate the hooks log (never events.ndjson)
# --------------------------------------------------------------------------- #
def rotate_hooks_log(root: Path, *, hooks_log: Path | None = None) -> dict[str, Any]:
    """Copy the hooks NDJSON log to a timestamped ``.bak`` and truncate the live
    file. Only the hooks log is a parameter, so rotating ``events.ndjson`` is
    impossible by construction. Refuses defensively if pointed at events.ndjson.
    """
    hooks_path = _hooks_log_path(root, hooks_log)
    if hooks_path.name == "events.ndjson":
        raise ValueError("rotate_hooks_log refuses to touch events.ndjson (append-only product audit trail).")
    if not hooks_path.is_file():
        return {"rotated": False, "note": "no hooks log present", "hooks_log": _rel(root, hooks_path)}
    stamp = utc_now().replace(":", "").replace("-", "")
    backup = hooks_path.with_suffix(hooks_path.suffix + f".{stamp}.bak")
    content = hooks_path.read_text(encoding="utf-8")
    atomic_write_text(backup, content)
    atomic_write_text(hooks_path, "")
    _append_log(root, {"action": "rotate-hooks", "backup": _rel(root, backup), "bytes": len(content)})
    return {"rotated": True, "backup": _rel(root, backup), "hooks_log": _rel(root, hooks_path), "bytes_archived": len(content)}


# --------------------------------------------------------------------------- #
# Append-only maintenance audit trail (distinct from events.ndjson)
# --------------------------------------------------------------------------- #
def _append_log(root: Path, record: dict[str, Any]) -> None:
    log_path = root / "maintenance" / "maintenance-log.ndjson"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"time": utc_now(), **record}
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
