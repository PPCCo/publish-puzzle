from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import list_artifacts, register_artifact
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, utc_now
from .validation import validate_data

RIGHTS_REQUIRED_TYPES = {
    "cover", "image", "illustration", "line-art", "coloring-page", "clipart",
    "diagram", "map", "font", "photo", "dataset", "word-list", "visual-asset",
    "puzzle-content", "printable-asset",
}


def add_rights_record(root: Path, project_id: str, record: dict[str, Any]) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    errors = validate_data(root, record, "rights-record.schema.json")
    if errors:
        raise ValueError("Invalid rights record: " + "; ".join(errors))
    ledger = load_json(paths.rights_ledger, {"schema_version": "1.0", "project_id": project_id, "records": []})
    if any(item.get("rights_id") == record["rights_id"] for item in ledger["records"]):
        raise ValueError(f"Duplicate rights ID: {record['rights_id']}")
    ledger["records"].append(record)
    atomic_write_json(paths.rights_ledger, ledger)
    return record


def check_rights(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    artifacts = list_artifacts(root, project_id)
    ledger = load_json(paths.rights_ledger, {"records": []})
    by_hash: dict[str, list[dict[str, Any]]] = {}
    for record in ledger.get("records", []):
        by_hash.setdefault(record.get("asset_hash", ""), []).append(record)
    unlinked: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    warnings: list[str] = []
    cleared: list[str] = []
    for artifact in artifacts:
        if artifact.get("type") not in RIGHTS_REQUIRED_TYPES:
            continue
        records = by_hash.get(artifact["sha256"], [])
        if not records:
            unlinked.append({"artifact_id": artifact["artifact_id"], "path": artifact["path"], "sha256": artifact["sha256"], "type": artifact["type"]})
            continue
        usable = [record for record in records if record.get("clearance_status") in {"cleared", "excluded"}]
        if not usable:
            blocked.append({"artifact_id": artifact["artifact_id"], "path": artifact["path"], "records": [{"rights_id": r.get("rights_id"), "status": r.get("clearance_status")} for r in records]})
        else:
            cleared.append(artifact["artifact_id"])
            for record in usable:
                if record.get("term_end"):
                    warnings.append(f"Rights term must be monitored for {record['rights_id']}: {record['term_end']}")
    decision = "PASS" if not unlinked and not blocked else "FAIL"
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "decision": decision,
        "cleared_artifact_ids": cleared,
        "unlinked_artifacts": unlinked,
        "blocked_artifacts": blocked,
        "warnings": warnings,
    }
    atomic_write_json(paths.directory / "rights" / "gate-latest.json", result)

    # Auto-register the compliance-bound artifacts so the compliance packet has
    # the exact TYPES gate_packet._GATE_ARTIFACT_TYPES["compliance"] binds, with no
    # manual `artifact register`. These are not downstream-build types, and
    # register_artifact dedups an unchanged report on re-run, so this is safe and
    # idempotent. register_artifact updates active_artifacts in state, so it runs
    # BEFORE the rights_gate summary write below (which re-reads state).
    register_artifact(
        root, project_id, "rights/gate-latest.json", "rights-gate", "RIGHTS_CLEARANCE",
        "rights-gate", rights_status="not-applicable", validation_status="pass" if decision == "PASS" else "fail",
    )
    if paths.rights_ledger.exists():
        register_artifact(
            root, project_id, "rights/ledger.json", "rights-ledger", "RIGHTS_CLEARANCE",
            "rights-manager", rights_status="not-applicable", validation_status="not-run",
        )

    state = load_json(paths.state)
    state["rights_gate"] = {"decision": decision, "evaluated_at": result["evaluated_at"], "unlinked": len(unlinked), "blocked": len(blocked)}
    state["updated_at"] = utc_now()
    state["updated_by"] = "rights-gate"
    atomic_write_json(paths.state, state)
    return result
