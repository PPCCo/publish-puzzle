from __future__ import annotations

from pathlib import Path
from typing import Any

from .approvals import verify_release_authorization
from .errors import ApprovalError
from .events import append_event
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, random_token, sha256_file, utc_now


def record_submission(root: Path, project_id: str, channel: str, evidence: str, external_id: str | None, status: str, actor: str) -> dict[str, Any]:
    if status not in {"submitted", "accepted", "published", "rejected", "withdrawn", "unknown"}:
        raise ValueError(f"Unsupported submission status: {status}")
    paths = ProjectPaths(root, project_id).require()
    manifest_path = paths.directory / "outputs" / "packages" / channel / "package-manifest.json"
    if not manifest_path.exists():
        raise ApprovalError(f"Current package manifest missing for channel: {channel}")
    manifest_hash = sha256_file(manifest_path)
    verification = verify_release_authorization(root, project_id, channel=channel, operation="submit", hashes=[manifest_hash])
    if not verification["valid"]:
        raise ApprovalError(verification["reason"])
    record = {
        "submission_id": f"sub-{channel}-{random_token(12)}",
        "project_id": project_id,
        "channel": channel,
        "status": status,
        "external_id": external_id,
        "evidence": evidence,
        "recorded_at": utc_now(),
        "recorded_by": actor,
        "external_write_performed_by_framework": False,
        "authorization_id": verification["authorization"]["authorization_id"],
    }
    path = paths.directory / "release" / f"submission-{record['submission_id']}.json"
    atomic_write_json(path, record)
    append_event(paths.events, project_id, "EXTERNAL_SUBMISSION_RECORDED", actor, record)
    return record


def create_dry_run(root: Path, project_id: str, channel: str, actor: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    package = paths.directory / "outputs" / "packages" / channel
    manifest_path = package / "package-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Package manifest missing for {channel}")
    manifest = load_json(manifest_path)
    record = {
        "dry_run_id": f"dry-{channel}-{random_token(12)}",
        "project_id": project_id,
        "channel": channel,
        "created_at": utc_now(),
        "created_by": actor,
        "package_manifest": manifest_path.relative_to(paths.directory).as_posix(),
        "package_status": manifest.get("preflight_status"),
        "external_write_performed": False,
        "notice": "Review the package and current platform requirements. This record performs no network request.",
    }
    path = paths.directory / "release" / f"{record['dry_run_id']}.json"
    atomic_write_json(path, record)
    append_event(paths.events, project_id, "SUBMISSION_DRY_RUN_CREATED", actor, record)
    return record
