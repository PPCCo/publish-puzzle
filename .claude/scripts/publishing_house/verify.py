"""Independent verification of generated content.

``verify_content`` reads every generated batch under the project (or one content
type) and runs each item through its INDEPENDENT validator --- the validator
re-derives correctness from the serialized item alone and never trusts the
generator. Results are written to
``verification/content-verification-latest.json`` (material evidence for the
interior gate), the state's ``content_verification`` summary is updated, and each
verified batch artifact's ``validation_status`` is stamped in the manifest.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .events import append_event
from .generators import registry
from .paths import ProjectPaths
from .util import atomic_write_json, load_json, utc_now

_CONTENT_DIRS = ["content/puzzles", "content/journal", "content/printable", "content/coloring"]


def _iter_batches(paths: ProjectPaths) -> list[Path]:
    batches: list[Path] = []
    for rel in _CONTENT_DIRS:
        directory = paths.directory / rel
        if directory.is_dir():
            batches.extend(sorted(directory.glob("*-batch.json")))
    return batches


def _verify_batch(batch: dict[str, Any]) -> dict[str, Any]:
    content_type = batch.get("content_type", "")
    try:
        ctype = registry.get(content_type)
    except KeyError as exc:
        return {
            "content_type": content_type,
            "passed": False,
            "verifiable": False,
            "item_count": len(batch.get("items", [])),
            "failed_items": [],
            "error": str(exc),
        }
    item_results = [ctype.validate(item).to_dict() for item in batch.get("items", [])]
    failed = [r for r in item_results if not r["passed"]]
    return {
        "content_type": content_type,
        "family": ctype.family,
        "verifiable": ctype.verifiable,
        "item_count": len(item_results),
        "passed_count": len(item_results) - len(failed),
        "passed": not failed,
        "failed_items": [{"index": r["index"], "errors": r["errors"]} for r in failed],
    }


def _stamp_manifest(paths: ProjectPaths, batch_hashes: dict[str, str]) -> None:
    """Stamp each verified batch artifact's validation_status in the manifest."""
    manifest_path = paths.artifact_manifest
    if not manifest_path.exists():
        return
    manifest = load_json(manifest_path)
    changed = False
    for artifact in manifest.get("artifacts", []):
        status = batch_hashes.get(artifact.get("type", ""))
        if status and not artifact.get("frozen", False):
            artifact["validation_status"] = status
            changed = True
    if changed:
        atomic_write_json(manifest_path, manifest)


def verify_content(root: Path, project_id: str, content_type: str | None = None) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    batch_paths = _iter_batches(paths)
    batch_reports: list[dict[str, Any]] = []
    per_type_status: dict[str, str] = {}
    for path in batch_paths:
        try:
            batch = load_json(path)
        except Exception:  # noqa: BLE001
            batch_reports.append({"content_type": path.stem, "passed": False, "error": "unreadable batch"})
            continue
        if content_type and batch.get("content_type") != content_type:
            continue
        report = _verify_batch(batch)
        report["source"] = path.relative_to(paths.directory).as_posix()
        batch_reports.append(report)
        per_type_status[f"content-{report['content_type']}"] = "pass" if report["passed"] else "fail"

    total = sum(r.get("item_count", 0) for r in batch_reports)
    failed_batches = [r for r in batch_reports if not r.get("passed")]
    decision = "PASS" if batch_reports and not failed_batches else "FAIL"
    if not batch_reports:
        decision = "FAIL"
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "decision": decision,
        "batch_count": len(batch_reports),
        "item_count": total,
        "failed_batch_count": len(failed_batches),
        "batches": batch_reports,
        "note": "Each item re-verified independently of its generator (code verifies code).",
    }
    out = paths.directory / "verification" / "content-verification-latest.json"
    atomic_write_json(out, result)
    _stamp_manifest(paths, per_type_status)

    state = load_json(paths.state)
    state["content_verification"] = {
        "decision": decision,
        "evaluated_at": result["evaluated_at"],
        "item_count": total,
        "failed_batches": len(failed_batches),
    }
    state["updated_at"] = utc_now()
    state["updated_by"] = "content-verifier"
    atomic_write_json(paths.state, state)
    append_event(paths.events, project_id, "CONTENT_VERIFIED", "content-verifier", {"decision": decision, "item_count": total})
    return result
