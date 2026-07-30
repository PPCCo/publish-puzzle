from __future__ import annotations

from pathlib import Path
from typing import Any

from .paths import ProjectPaths
from .util import atomic_write_json, load_json, load_yaml, utc_now
from .validation import validate_data


def audit_metadata(root: Path, project_id: str) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    target = paths.directory / "metadata" / "book.json"
    issues: list[str] = []
    warnings: list[str] = []
    if not target.exists():
        issues.append("Missing metadata/book.json")
        metadata: dict[str, Any] = {}
    else:
        try:
            metadata = load_json(target)
            issues.extend(validate_data(root, metadata, "metadata.schema.json"))
        except Exception as exc:  # noqa: BLE001
            metadata = {}
            issues.append(str(exc))
    project = load_yaml(paths.config)
    if metadata:
        comparisons = {
            "project_id": project_id,
            "language": project.get("language"),
            "edition": project.get("edition"),
        }
        for field, expected in comparisons.items():
            if metadata.get(field) != expected:
                issues.append(f"Metadata {field}={metadata.get(field)!r} does not match project {expected!r}")
        project_formats = set(project.get("formats", []))
        metadata_formats = set(metadata.get("formats", []))
        missing = sorted(project_formats - metadata_formats)
        if missing:
            issues.append("Metadata is missing project format(s): " + ", ".join(missing))
        if len(metadata.get("title", "")) > 200:
            warnings.append("Title exceeds 200 characters; verify every target channel manually")
        if not metadata.get("short_description"):
            warnings.append("Short description is absent")
        if not metadata.get("identifiers"):
            warnings.append("No identifiers recorded; verify whether each format/channel requires an ISBN or other identifier")
        if not metadata.get("disclosures"):
            warnings.append("No production or AI-assistance disclosures recorded; evaluate current channel requirements")
    result = {
        "schema_version": "1.0",
        "project_id": project_id,
        "evaluated_at": utc_now(),
        "decision": "PASS" if not issues else "FAIL",
        "issues": issues,
        "warnings": warnings,
        "metadata_path": "metadata/book.json",
    }
    atomic_write_json(paths.directory / "metadata" / "validation-report.json", result)
    return result
