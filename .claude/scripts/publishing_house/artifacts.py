from __future__ import annotations

from pathlib import Path
from typing import Any

from .events import append_event
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, project_lock, relative_to, sha256_path, slugify, utc_now
from .validation import validate_data

# Artifact types that are pure downstream build outputs. Re-registering one of these
# with a new hash MUST NOT invalidate an upstream gate approval, because approvals bind
# to the SOURCE content/design/metadata hashes (see gate_packet._GATE_ARTIFACT_TYPES),
# never to the rebuilt PDF or channel package. Belt-and-braces guard so the fix holds
# even if a future gate accidentally binds one of these types.
_DOWNSTREAM_BUILD_TYPES = {
    "interior-pdf",
    "interior-proof",
    "cover-pdf",
    "cover-proof",
    "platform-package-kdp",
    "platform-package-etsy",
    "platform-package-gumroad",
    "platform-package-generic",
    "launch-guide",
    "marketing-kit",
}


def list_artifacts(root: Path, project_id: str) -> list[dict[str, Any]]:
    paths = ProjectPaths(root, project_id).require()
    return load_json(paths.artifact_manifest, {"artifacts": []}).get("artifacts", [])


def get_artifact_by_hash(root: Path, project_id: str, digest: str) -> dict[str, Any] | None:
    return next((item for item in list_artifacts(root, project_id) if item.get("sha256") == digest), None)


def resolve_hash(root: Path, project_id: str, path_or_hash: str) -> str:
    if path_or_hash.startswith("sha256:"):
        if not get_artifact_by_hash(root, project_id, path_or_hash):
            raise ValueError(f"Unregistered artifact hash: {path_or_hash}")
        return path_or_hash
    paths = ProjectPaths(root, project_id).require()
    path = paths.resolve_inside(path_or_hash)
    digest, _ = sha256_path(path)
    registered = get_artifact_by_hash(root, project_id, digest)
    if not registered:
        raise ValueError(f"Artifact is not registered: {path_or_hash} ({digest})")
    return digest


def register_artifact(
    root: Path,
    project_id: str,
    path: str | Path,
    artifact_type: str,
    stage: str,
    actor: str,
    rights_status: str = "pending",
    validation_status: str = "not-run",
    source_artifact_ids: list[str] | None = None,
    provenance: dict[str, Any] | None = None,
    active: bool = True,
) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    absolute = paths.resolve_inside(path)
    if not absolute.exists():
        raise FileNotFoundError(absolute)
    digest, size = sha256_path(absolute)
    rel = relative_to(absolute, paths.directory)
    with project_lock(paths.lock):
        manifest = load_json(paths.artifact_manifest, {"schema_version": "1.0", "project_id": project_id, "artifacts": []})
        for existing in manifest["artifacts"]:
            if existing["sha256"] == digest and existing["path"] == rel and existing["type"] == artifact_type:
                return existing
        versions = [item["version"] for item in manifest["artifacts"] if item["type"] == artifact_type]
        artifact = {
            "artifact_id": f"art-{slugify(artifact_type, 20)}-{digest.split(':')[1][:12]}",
            "project_id": project_id,
            "type": artifact_type,
            "stage": stage,
            "version": max(versions, default=0) + 1,
            "path": rel,
            "sha256": digest,
            "size_bytes": size,
            "created_at": utc_now(),
            "created_by": actor,
            "source_artifact_ids": source_artifact_ids or [],
            "provenance": provenance or {},
            "rights_status": rights_status,
            "validation_status": validation_status,
            "supersedes": None,
            "frozen": False,
        }
        previous_hash = None
        if active:
            state = load_json(paths.state)
            previous_hash = state.get("active_artifacts", {}).get(artifact_type)
            if previous_hash and previous_hash != digest:
                previous = next((x for x in manifest["artifacts"] if x["sha256"] == previous_hash), None)
                if previous:
                    artifact["supersedes"] = previous["artifact_id"]
            state.setdefault("active_artifacts", {})[artifact_type] = digest
            state["updated_at"] = utc_now()
            state["updated_by"] = actor
            atomic_write_json(paths.state, state)
        errors = validate_data(root, artifact, "artifact.schema.json")
        if errors:
            raise ValueError("Artifact schema validation failed: " + "; ".join(errors))
        manifest["artifacts"].append(artifact)
        atomic_write_json(paths.artifact_manifest, manifest)
        append_event(paths.events, project_id, "ARTIFACT_REGISTERED", actor, {"artifact_id": artifact["artifact_id"], "type": artifact_type, "path": rel, "sha256": digest, "active": active})
        if previous_hash and previous_hash != digest and artifact_type not in _DOWNSTREAM_BUILD_TYPES:
            from .approvals import invalidate_approvals_for_hashes
            invalidate_approvals_for_hashes(root, project_id, [previous_hash], actor, f"Superseded by {digest}")
        return artifact


def freeze_artifacts(root: Path, project_id: str, hashes: list[str], actor: str) -> list[str]:
    paths = ProjectPaths(root, project_id).require()
    with project_lock(paths.lock):
        manifest = load_json(paths.artifact_manifest)
        frozen: list[str] = []
        for item in manifest["artifacts"]:
            if item["sha256"] in hashes:
                item["frozen"] = True
                frozen.append(item["sha256"])
        missing = sorted(set(hashes) - set(frozen))
        if missing:
            raise ValueError(f"Cannot freeze unregistered hashes: {missing}")
        atomic_write_json(paths.artifact_manifest, manifest)
        append_event(paths.events, project_id, "ARTIFACTS_FROZEN", actor, {"hashes": frozen})
        return frozen
