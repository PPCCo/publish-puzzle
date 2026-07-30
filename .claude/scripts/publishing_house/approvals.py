from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from .errors import ApprovalError
from .events import append_event
from .paths import ProjectPaths
from .util import (
    atomic_write_json,
    load_company_config,
    load_json,
    parse_csv,
    parse_time,
    random_token,
    sha256_file,
    utc_now,
)
from .validation import validate_data


def list_approvals(root: Path, project_id: str) -> list[dict[str, Any]]:
    paths = ProjectPaths(root, project_id).require()
    records: list[dict[str, Any]] = []
    for path in sorted(paths.directory.glob("approvals/*.json")):
        try:
            records.append(load_json(path))
        except Exception:  # noqa: BLE001
            continue
    return records


def approval_is_current(record: dict[str, Any]) -> bool:
    if record.get("decision") != "APPROVED" or record.get("invalidated_at"):
        return False
    expires = record.get("expires_at")
    return not expires or parse_time(expires) > parse_time(utc_now())


def has_valid_approval(root: Path, project_id: str, gate: str) -> bool:
    return any(record.get("gate") == gate and approval_is_current(record) for record in list_approvals(root, project_id))


def grant_approval(
    root: Path,
    project_id: str,
    gate: str,
    approver: str,
    approver_role: str,
    artifacts: list[str],
    scope: str,
    decision: str = "APPROVED",
    exclusions: list[str] | None = None,
    notes: str = "",
    expires_at: str | None = None,
) -> dict[str, Any]:
    if gate not in {"niche", "interior", "cover", "compliance", "listing", "release"}:
        raise ApprovalError(f"Unknown approval gate: {gate}")
    if gate == "release":
        raise ApprovalError("Use release authorization for the release gate")
    from .artifacts import resolve_hash

    hashes = [resolve_hash(root, project_id, value) for value in artifacts]
    now = utc_now()
    record = {
        "approval_id": f"apr-{gate}-{now.replace(':', '').replace('-', '').lower()}-{random_token(8)}",
        "project_id": project_id,
        "gate": gate,
        "approver": approver,
        "approver_role": approver_role,
        "decision": decision,
        "artifact_hashes": list(dict.fromkeys(hashes)),
        "scope": scope,
        "exclusions": exclusions or [],
        "notes": notes,
        "created_at": now,
        "expires_at": expires_at,
        "invalidated_at": None,
        "invalidation_reason": None,
    }
    errors = validate_data(root, record, "approval.schema.json")
    if errors:
        raise ApprovalError("Invalid approval: " + "; ".join(errors))
    paths = ProjectPaths(root, project_id).require()
    path = paths.directory / "approvals" / f"{record['approval_id']}.json"
    atomic_write_json(path, record)
    append_event(paths.events, project_id, "APPROVAL_RECORDED", approver, {"approval_id": record["approval_id"], "gate": gate, "decision": decision, "artifact_hashes": record["artifact_hashes"], "scope": scope})
    if decision == "APPROVED" and gate == "interior":
        # Interior approval locks the verified content batches: it is the
        # content-freeze point of the puzzle/coloring/journal lifecycle.
        from .artifacts import freeze_artifacts
        freeze_artifacts(root, project_id, record["artifact_hashes"], approver)
    return record


def invalidate_approvals_for_hashes(root: Path, project_id: str, hashes: list[str], actor: str, reason: str) -> list[str]:
    paths = ProjectPaths(root, project_id).require()
    invalidated: list[str] = []
    for path in sorted(paths.directory.glob("approvals/*.json")):
        record = load_json(path)
        if record.get("invalidated_at"):
            continue
        if set(record.get("artifact_hashes", [])) & set(hashes):
            record["invalidated_at"] = utc_now()
            record["invalidation_reason"] = reason
            atomic_write_json(path, record)
            invalidated.append(record["approval_id"])
    if invalidated:
        state = load_json(paths.state)
        existing = state.setdefault("invalidated_approvals", [])
        existing.extend(item for item in invalidated if item not in existing)
        state["updated_at"] = utc_now()
        state["updated_by"] = actor
        atomic_write_json(paths.state, state)
        append_event(paths.events, project_id, "APPROVALS_INVALIDATED", actor, {"approval_ids": invalidated, "hashes": hashes, "reason": reason})
    return invalidated


def release_authorizations(root: Path, project_id: str) -> list[dict[str, Any]]:
    paths = ProjectPaths(root, project_id).require()
    output: list[dict[str, Any]] = []
    for path in sorted(paths.directory.glob("release/release-authorization-*.json")):
        try:
            output.append(load_json(path))
        except Exception:  # noqa: BLE001
            continue
    return output


def authorization_is_current(record: dict[str, Any]) -> bool:
    if record.get("used_at"):
        return False
    try:
        return parse_time(record["expires_at"]) > parse_time(utc_now())
    except Exception:  # noqa: BLE001
        return False


def has_valid_release_authorization(root: Path, project_id: str) -> bool:
    return any(authorization_is_current(item) for item in release_authorizations(root, project_id))


def create_release_authorization(
    root: Path,
    project_id: str,
    approvers: list[str],
    channels: list[str] | str,
    products: list[str] | str,
    territories: list[str] | str,
    artifacts: list[str],
    operations: list[str] | str,
    maximum_external_spend: float = 0.0,
    currency: str = "USD",
    expires_at: str | None = None,
    pricing_scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from .artifacts import resolve_hash
    from .project import project_status

    company = load_company_config(root)
    required = int(company.get("human_gates", {}).get("release", 1))
    distinct = list(dict.fromkeys(x.strip() for x in approvers if x.strip()))
    if len(distinct) < required:
        raise ApprovalError(f"Release authorization requires {required} distinct approver(s); received {len(distinct)}")
    if not has_valid_approval(root, project_id, "listing"):
        raise ApprovalError("Current listing approval is required")
    hashes = [resolve_hash(root, project_id, value) for value in artifacts]
    requested_channels = parse_csv(channels)
    paths = ProjectPaths(root, project_id).require()
    package_manifest_hashes: dict[str, str] = {}
    for channel in requested_channels:
        manifest_path = paths.directory / "outputs" / "packages" / channel / "package-manifest.json"
        if not manifest_path.exists():
            raise ApprovalError(f"Missing package manifest for channel: {channel}")
        manifest = load_json(manifest_path)
        if str(manifest.get("preflight_status", "")).lower() not in {"pass", "warning"}:
            raise ApprovalError(f"Channel package has not passed preflight: {channel}")
        package_manifest_hashes[channel] = sha256_file(manifest_path)
    missing_package_hashes = sorted(set(package_manifest_hashes.values()) - set(hashes))
    if missing_package_hashes:
        raise ApprovalError("Release authorization must include every current channel package manifest hash: " + ", ".join(missing_package_hashes))
    now = utc_now()
    if expires_at is None:
        expires_at = (parse_time(now) + timedelta(days=7)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if parse_time(expires_at) <= parse_time(now):
        raise ApprovalError("Release authorization expiry must be in the future")
    project = project_status(root, project_id)["project"]
    record = {
        "authorization_id": f"rel-{project_id}-{random_token(12)}",
        "project_id": project_id,
        "edition": int(project.get("edition", 1)),
        "channels": requested_channels,
        "product_types": parse_csv(products),
        "territories": parse_csv(territories),
        "artifact_hashes": list(dict.fromkeys(hashes)),
        "package_manifest_hashes": package_manifest_hashes,
        "pricing_scope": pricing_scope or {},
        "permitted_operations": parse_csv(operations),
        "maximum_external_spend": float(maximum_external_spend),
        "currency": currency,
        "approvers": distinct,
        "nonce": random_token(32),
        "created_at": now,
        "expires_at": expires_at,
        "used_at": None,
    }
    errors = validate_data(root, record, "release-authorization.schema.json")
    if errors:
        raise ApprovalError("Invalid release authorization: " + "; ".join(errors))
    paths = ProjectPaths(root, project_id).require()
    path = paths.directory / "release" / f"release-authorization-{record['authorization_id']}.json"
    atomic_write_json(path, record)
    append_event(paths.events, project_id, "RELEASE_AUTHORIZED", ",".join(distinct), {"authorization_id": record["authorization_id"], "channels": record["channels"], "operations": record["permitted_operations"], "artifact_hashes": record["artifact_hashes"], "expires_at": expires_at})
    return record


def verify_release_authorization(root: Path, project_id: str, channel: str | None = None, operation: str | None = None, hashes: list[str] | None = None) -> dict[str, Any]:
    candidates = [item for item in release_authorizations(root, project_id) if authorization_is_current(item)]
    for record in reversed(candidates):
        if channel and channel not in record.get("channels", []):
            continue
        if operation and operation not in record.get("permitted_operations", []):
            continue
        if hashes and not set(hashes).issubset(set(record.get("artifact_hashes", []))):
            continue
        return {"valid": True, "authorization": record}
    return {"valid": False, "authorization": None, "reason": "No current authorization matches the requested scope"}
