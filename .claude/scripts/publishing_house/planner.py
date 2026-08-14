"""Deterministic state -> plan mapping for autonomous-between-gates orchestration.

``plan_next`` reads the current workflow state and returns the single recommended
forward action, backed by data (``config/state_playbook.json``) rather than prose.
It never mutates state and never grants, freezes, or authorizes anything. When the
recommended forward transition is a human gate, it flags ``is_human_gate`` and
recommends assembling and presenting an approval packet instead of transitioning.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .state import (
    allowed_transitions,
    next_actions,
    required_gate,
    transition_blockers,
    workflow_config,
)
from .util import load_json, load_yaml

# autonomy_action values. STOP_AT_GATE is the canonical human-gate stop token,
# matching tests/test_gate_integrity.py and docs/ARCHITECTURE.md. Autonomy must
# never emit PROCEED for a human-gate edge.
PROCEED = "PROCEED"
STOP_AT_GATE = "STOP_AT_GATE"
BLOCKED = "BLOCKED"
TERMINAL = "TERMINAL"


def load_playbook(root: Path) -> dict[str, Any]:
    return load_json(root / ".claude" / "config" / "state_playbook.json")


# Main-path state at/after which a product is "done enough" that advancing the
# SET (creating the next volume) becomes the natural next step. Off-path states
# (PAUSED/CANCELLED/ERROR) never trigger it.
_SERIES_ADVANCE_FROM_STATE = "RELEASE_AUTHORIZATION"
_OFF_PATH_STATES = frozenset({"PAUSED", "CANCELLED", "ERROR"})


def _series_next_advisory(
    root: Path, paths: ProjectPaths, current: str
) -> dict[str, Any] | None:
    """Advisory-only 'create the next volume in the set' hint.

    Returns ``None`` (the common case) unless ALL hold:
      * the project carries a ``series`` back-reference (it is in a set);
      * the current main-path state is at/after ``RELEASE_AUTHORIZATION``
        (off-path states never qualify);
      * the series manifest has a higher-positioned slot with no project yet.

    It never auto-creates a volume, never bypasses a gate, and never alters the
    caller's ``all_forward_options`` or ``blockers``. Non-series projects and
    early-stage projects get ``None`` so they are wholly unaffected.
    """
    project = load_yaml(paths.config, default={}) or {}
    link = project.get("series")
    if not isinstance(link, dict) or not link.get("series_id"):
        return None

    order = workflow_config(root).get("states", [])
    if current in _OFF_PATH_STATES or current not in order:
        return None
    if _SERIES_ADVANCE_FROM_STATE not in order:
        return None
    if order.index(current) < order.index(_SERIES_ADVANCE_FROM_STATE):
        return None

    # Lazy import keeps planner free of a load-time dependency on series.py.
    from .paths import SeriesPaths
    from .series import _load_manifest

    series_id = link["series_id"]
    series_paths = SeriesPaths(root, series_id)
    if not series_paths.manifest.exists():
        return None
    manifest = _load_manifest(series_paths.manifest)
    position = link.get("position")
    if position is None:
        return None
    later_uncreated = sorted(
        (
            slot
            for slot in manifest.get("books", [])
            if slot.get("position", 0) > position and not slot.get("project_id")
        ),
        key=lambda slot: slot["position"],
    )
    if not later_uncreated:
        return None
    nxt = later_uncreated[0]
    return {
        "series_id": series_id,
        "next_position": nxt["position"],
        "next_working_title": nxt.get("working_title"),
        "suggested_command": (
            f"series add-book {series_id} --position {nxt['position']}"
        ),
    }


def _project_formats(paths: ProjectPaths) -> list[str]:
    project = load_yaml(paths.config, default={}) or {}
    formats = project.get("formats") or project.get("sales_channels") or []
    if isinstance(formats, str):
        return [formats]
    return [str(f) for f in formats]


def _select_target(
    root: Path,
    current: str,
    entry: dict[str, Any],
    permitted_targets: list[str],
    formats: list[str],
) -> str | None:
    """Choose the recommended forward target for ``current``.

    Prefers the playbook's ``forward_target``. Honours a format-conditional
    alternate (e.g. route through AUDIO_PRODUCTION only when the project has an
    audiobook/read-along format). Never returns PAUSED/CANCELLED/ERROR or a
    backward edge; only forward states listed in the playbook are eligible.
    """
    playbook_states: dict[str, Any] = load_playbook(root)["states"]
    forward = entry.get("forward_target")

    # Format-conditional alternate routing (e.g. LAYOUT -> AUDIO_PRODUCTION).
    for alt_state, _reason in (entry.get("alternate_targets") or {}).items():
        alt_entry = playbook_states.get(alt_state, {})
        conditional = alt_entry.get("conditional_on_formats")
        if conditional and any(fmt in formats for fmt in conditional):
            if alt_state in allowed_transitions(root, current):
                return alt_state

    if forward and forward in allowed_transitions(root, current):
        return forward
    # Fall back to the first permitted forward edge that the playbook knows.
    for target in permitted_targets:
        if target in playbook_states:
            return target
    return None


def plan_next(root: Path, project_id: str) -> dict[str, Any]:
    """Return the single recommended next action for a project.

    Read-only. Shape:
        {
          project_id, current_state, target_state, required_gate|None,
          is_human_gate: bool, autonomy_action, recommended_action,
          recommended_agents, recommended_skills, recommended_workflows,
          entry_criteria, acceptance, gate_report_path, blockers,
          human_gate_command|None, all_forward_options
        }
    """
    paths = ProjectPaths(root, project_id).require()
    state = load_json(paths.state)
    current = str(state["current_state"])
    playbook = load_playbook(root)
    entry: dict[str, Any] = playbook["states"].get(current, {})
    formats = _project_formats(paths)

    actions = next_actions(root, project_id)["actions"]
    permitted_targets = [a["target"] for a in actions if a["permitted"]]

    result: dict[str, Any] = {
        "project_id": project_id,
        "current_state": current,
        "target_state": None,
        "required_gate": None,
        "is_human_gate": False,
        "autonomy_action": BLOCKED,
        "recommended_action": "",
        "recommended_agents": list(entry.get("recommended_agents", [])),
        "recommended_skills": list(entry.get("recommended_skills", [])),
        "human_only_skill": entry.get("human_only_skill"),
        "recommended_workflows": list(entry.get("recommended_workflows", [])),
        "entry_criteria": entry.get("entry_criteria", ""),
        "acceptance": entry.get("acceptance", ""),
        "gate_report_path": entry.get("gate_report_path"),
        "blockers": [],
        "human_gate_command": None,
        "all_forward_options": actions,
        "series_next": None,
    }
    # Advisory series hint, attached to every return path. Never affects
    # all_forward_options, blockers, or the autonomy decision below.
    result["series_next"] = _series_next_advisory(root, paths, current)

    # Terminal / out-of-scope states.
    if not entry or current in set(workflow_config(root).get("terminal_states", [])):
        result["autonomy_action"] = TERMINAL
        result["recommended_action"] = (
            f"State {current} has no autonomous forward action in the playbook; a human decides the next step."
        )
        return result
    if entry.get("autonomy_terminal"):
        result["target_state"] = entry.get("forward_target")
        result["autonomy_action"] = TERMINAL
        result["recommended_action"] = entry.get("acceptance", "")
        return result

    target = _select_target(root, current, entry, permitted_targets, formats)
    result["target_state"] = target

    if target is None:
        # No forward edge the playbook understands (e.g. only PAUSED/CANCELLED left).
        blocked = [a for a in actions if not a["permitted"]]
        result["blockers"] = sorted(
            {b for a in blocked for b in a.get("blockers", [])}
        )
        result["recommended_action"] = (
            "No autonomous forward transition is available. Resolve blockers or await a human decision."
        )
        return result

    gate = required_gate(root, current, target)
    is_human_gate = bool(entry.get("human_gate")) or gate is not None
    result["required_gate"] = gate
    result["is_human_gate"] = is_human_gate
    result["blockers"] = transition_blockers(root, project_id, current, target)

    if is_human_gate:
        gate_name = gate or entry.get("gate")
        gate_skill = playbook.get("human_gate_skills", {}).get(gate_name or "")
        result["autonomy_action"] = STOP_AT_GATE
        result["human_gate_command"] = f"/{gate_skill}" if gate_skill else None
        packet_hint = (
            f"approvals/packets/gate-packet-{gate_name}-latest.json" if gate_name else "an approval packet"
        )
        result["recommended_action"] = (
            f"HUMAN GATE. Assemble and present the approval packet "
            f"(.venv/bin/python3 .claude/scripts/ph_cli.py approval packet {project_id} --gate {gate_name}) "
            f"then STOP. A human must record approval via {result['human_gate_command'] or 'the human-only approval skill'}. "
            f"Never auto-approve. Packet will be written to {packet_hint}."
        )
        return result

    # Autonomous forward step.
    if result["blockers"]:
        result["autonomy_action"] = BLOCKED
        result["recommended_action"] = (
            f"Blocked from {current} -> {target}. Produce the missing artifact and clear: "
            + "; ".join(result["blockers"])
        )
    else:
        result["autonomy_action"] = PROCEED
        skills = ", ".join(result["recommended_skills"]) or "(no skill mapped)"
        result["recommended_action"] = (
            f"Run stage {current}: delegate bounded work to {skills}; register artifacts, "
            f"run deterministic validators/gates, then transition to {target}."
        )
    return result
