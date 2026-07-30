"""Deterministic content generation orchestration.

``generate_content`` is a thin layer over the ``generators`` registry: it derives
a stable per-project seed (unless one is supplied), produces ``count`` items of a
content type, writes them under the project's content directory, and registers
the batch as an artifact so downstream gates bind to its exact hash. Generation
is pure and reproducible --- rerunning with the same seed reproduces byte-identical
content.
"""
from __future__ import annotations

import zlib
from pathlib import Path
from typing import Any

from .events import append_event
from .generators import registry
from .generators.base import derive_seed
from .paths import ProjectPaths
from .util import atomic_write_json, load_yaml, utc_now

# Which project subdirectory each content family writes into.
_FAMILY_DIR = {
    "puzzle": "content/puzzles",
    "activity": "content/puzzles",
    "journal": "content/journal",
    "printable": "content/printable",
    "coloring": "content/coloring",
}


def _project_base_seed(project_id: str, content_type: str) -> int:
    """A stable base seed derived from the project id when none is supplied."""
    return zlib.adler32(f"{project_id}:{content_type}".encode("utf-8"))


def generate_content(
    root: Path,
    project_id: str,
    content_type: str,
    count: int = 1,
    difficulty: str = "mixed",
    seed: int | None = None,
    params: dict[str, Any] | None = None,
    actor: str = "content-generator",
) -> dict[str, Any]:
    paths = ProjectPaths(root, project_id).require()
    ctype = registry.get(content_type)  # raises KeyError with known keys on miss
    params = params or {}
    base_seed = seed if seed is not None else _project_base_seed(project_id, content_type)

    items: list[dict[str, Any]] = []
    for index in range(count):
        item_seed = derive_seed(base_seed, content_type, index)
        item = ctype.generate(item_seed, difficulty, index, params)
        items.append(item.to_dict())

    family_dir = _FAMILY_DIR.get(ctype.family, "content/puzzles")
    out_dir = paths.directory / family_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    batch = {
        "schema_version": "1.0",
        "project_id": project_id,
        "content_type": content_type,
        "family": ctype.family,
        "label": ctype.label,
        "difficulty": difficulty,
        "base_seed": base_seed,
        "count": len(items),
        "verifiable": ctype.verifiable,
        "generated_at": utc_now(),
        "generated_by": actor,
        "params": params,
        "items": items,
    }
    out_path = out_dir / f"{content_type}-batch.json"
    atomic_write_json(out_path, batch)

    # Register the batch so verification and the interior gate bind to its hash.
    project = load_yaml(paths.config, default={}) or {}
    from .artifacts import register_artifact

    artifact = register_artifact(
        root,
        project_id,
        out_path,
        artifact_type=f"content-{content_type}",
        stage="CONTENT_GENERATION",
        actor=actor,
        rights_status="not-applicable" if ctype.family != "coloring" else "pending",
        validation_status="not-run",
        provenance={
            "content_type": content_type,
            "family": ctype.family,
            "base_seed": base_seed,
            "difficulty": difficulty,
            "audience": project.get("audience"),
        },
    )
    append_event(
        paths.events,
        project_id,
        "CONTENT_GENERATED",
        actor,
        {"content_type": content_type, "count": len(items), "artifact_id": artifact["artifact_id"]},
    )
    return {
        "project_id": project_id,
        "content_type": content_type,
        "count": len(items),
        "path": out_path.relative_to(paths.directory).as_posix(),
        "artifact_id": artifact["artifact_id"],
        "sha256": artifact["sha256"],
        "base_seed": base_seed,
    }
