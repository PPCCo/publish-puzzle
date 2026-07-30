from __future__ import annotations

from pathlib import Path
from typing import Any

from .approvals import has_valid_approval, has_valid_release_authorization
from .errors import StateTransitionError
from .events import append_event
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, project_lock, utc_now


def workflow_config(root: Path) -> dict[str, Any]:
    return load_json(root / ".claude" / "config" / "workflow_states.json")


def allowed_transitions(root: Path, current: str) -> list[str]:
    return list(workflow_config(root).get("transitions", {}).get(current, []))


def required_gate(root: Path, current: str, target: str) -> str | None:
    """Return the human-gate name (if any) guarding the ``current -> target`` edge.

    Config-driven: reads ``gate_edges`` from ``workflow_states.json`` so the
    lifecycle can be re-shaped without touching Python. ``gate_edges`` maps a
    ``"FROM->TO"`` edge key to a gate name (brief, prototype, content_freeze,
    final, release, ...). This replaces the hard-coded gate table used in the
    parent books framework (recorded as a bk-pub enhancement candidate).
    """
    edges = workflow_config(root).get("gate_edges", {})
    return edges.get(f"{current}->{target}")


def _gate_reports(root: Path) -> dict[str, Any]:
    """Config-driven blocker rules.

    ``gate_reports`` in ``workflow_states.json`` maps a ``"FROM->TO"`` edge to a
    list of report requirements. Each requirement is either:
      {"path": "verification/gate-latest.json", "decision_in": ["PASS"],
       "message": "..."}  -- a single report that must carry an allowed decision
    or {"glob": "outputs/**/*report.json", "fail_if": "FAIL", "message": "..."}
      -- any matching report with decision==fail_if adds a blocker.
    """
    return workflow_config(root).get("gate_reports", {})


def _report_decision(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = load_json(path)
        return str(data.get("decision") or data.get("status") or "").upper() or None
    except Exception:  # noqa: BLE001
        return "INVALID"


def _gate_approval_blockers(root: Path, project_id: str, gate: str | None) -> list[str]:
    """Human-gate approval / release-authorization blockers for an edge."""
    if gate == "release":
        if not has_valid_release_authorization(root, project_id):
            return ["valid release authorization required"]
        return []
    if gate and not has_valid_approval(root, project_id, gate):
        return [f"valid {gate} approval required"]
    return []


def _report_rule_blockers(root: Path, paths: ProjectPaths, current: str, target: str) -> list[str]:
    """Config-driven report-decision blockers from ``gate_reports``."""
    blockers: list[str] = []
    requirements = _gate_reports(root).get(f"{current}->{target}", [])
    for rule in requirements:
        message = rule.get("message", "required gate report must pass")
        if "glob" in rule:
            fail_if = str(rule.get("fail_if", "FAIL")).upper()
            for report in sorted(paths.directory.glob(rule["glob"])):
                if _report_decision(report) == fail_if:
                    rel = report.relative_to(paths.directory).as_posix()
                    blockers.append(f"{message}: {rel}")
        else:
            allowed = {str(x).upper() for x in rule.get("decision_in", ["PASS"])}
            decision = _report_decision(paths.directory / rule["path"])
            if decision not in allowed:
                blockers.append(message)
    return blockers


def _channel_package_blockers(paths: ProjectPaths) -> list[str]:
    """Every configured sales channel needs a passing/warning package manifest."""
    blockers: list[str] = []
    project = load_yaml(paths.config)
    for channel in project.get("sales_channels", []):
        manifest = paths.directory / "outputs" / "packages" / channel / "package-manifest.json"
        if _report_decision(manifest) not in {"PASS", "WARNING"}:
            blockers.append(f"channel package is missing or failed: {channel}")
    return blockers


def _published_evidence_recorded(paths: ProjectPaths) -> bool:
    for path in (paths.directory / "release").glob("submission-*.json"):
        try:
            if load_json(path).get("status") == "published":
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


def transition_blockers(root: Path, project_id: str, current: str, target: str) -> list[str]:
    """Return the list of reasons the ``current -> target`` edge is not permitted.

    Report-decision rules are config-driven (``gate_reports`` in
    ``workflow_states.json``); structural rules (channel packages, published
    evidence, release authorization at submission time) stay in code because
    they read cross-cutting project state.
    """
    paths = ProjectPaths(root, project_id).require()
    gate = required_gate(root, current, target)
    blockers: list[str] = _gate_approval_blockers(root, project_id, gate)
    blockers.extend(_report_rule_blockers(root, paths, current, target))

    if current == "PLATFORM_PACKAGING" and target == "RELEASE_AUTHORIZATION":
        blockers.extend(_channel_package_blockers(paths))
    if current == "READY_FOR_SUBMISSION" and target == "SUBMISSION":
        if not has_valid_release_authorization(root, project_id):
            blockers.append("current release authorization required at submission time")
    if current == "SUBMISSION" and target == "PUBLISHED" and not _published_evidence_recorded(paths):
        blockers.append("recorded platform evidence with status=published is required")
    return blockers


def transition(root: Path, project_id: str, target: str, actor: str, reason: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    config = workflow_config(root)
    if target not in config["states"]:
        raise StateTransitionError(f"Unknown target state: {target}")
    with project_lock(paths.lock):
        state = load_json(paths.state)
        current = state["current_state"]
        if target not in allowed_transitions(root, current):
            raise StateTransitionError(f"Transition not allowed: {current} -> {target}")
        blockers = transition_blockers(root, project_id, current, target)
        if blockers:
            raise StateTransitionError("; ".join(blockers))
        old = dict(state)
        state["previous_state"] = current
        state["current_state"] = target
        state["blocked_reasons"] = []
        state["updated_at"] = utc_now()
        state["updated_by"] = actor
        atomic_write_json(paths.state, state)
        append_event(paths.events, project_id, "STATE_TRANSITIONED", actor, {"from": current, "to": target, "reason": reason})
        return {"before": old, "after": state}


def next_actions(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    state = load_json(paths.state)
    current = state["current_state"]
    actions: list[dict[str, Any]] = []
    for target in allowed_transitions(root, current):
        gate = required_gate(root, current, target)
        blockers = transition_blockers(root, project_id, current, target)
        actions.append({"target": target, "required_gate": gate, "permitted": not blockers, "blockers": blockers})
    return {"project_id": project_id, "current_state": current, "actions": actions}
