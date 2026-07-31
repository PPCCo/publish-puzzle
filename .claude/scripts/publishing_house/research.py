"""Offline category-research pipeline: scaffold, validate, merge, show, log.

Network-free (rule 18). The actual retrieval is performed by the quarantined
``publishing_house.net.fetch`` module (invoked via ``fetch`` CLI commands) and by
the ``/research`` skill's ladder. This module only manages the on-disk research
workspace under ``research/<category>/``:

* ``findings.json``       — normalized evidence claims (validated).
* ``pipeline.json``       — the product backlog keyed by PRODUCT_ID (validated).
* ``report.md``           — human-readable summary (skill-authored; not touched here).
* ``research-log.ndjson`` — append-only run/fetch/ingest history.
* ``queries.md`` / ``inbox/`` — only created by the skill when a manual tier is needed.

Nothing here writes under ``projects/`` or mutates workflow state, gates, or
approvals. Craft literals in the pipeline are advisory only (rule 20); the
design-policy engine is authoritative at ``project init``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .util import atomic_write_json, atomic_write_text, load_json, slugify, utc_now
from .validation import validate_data

_FINDINGS_SCHEMA = "research-findings.schema.json"
_PIPELINE_SCHEMA = "pipeline.schema.json"

# The pipeline product_type enum mirrors the `project init` --product-type choices.
_PRODUCT_TYPES = ("puzzle-book", "coloring-book", "guided-journal", "digital-printable")
_AUDIENCE_BANDS = (
    "kids-4-8", "kids-6-10", "tween-8-12", "teen-13-17", "adult-general", "senior-large-print",
)


# --- paths -----------------------------------------------------------------


def _research_root(root: Path) -> Path:
    # Generated category workspaces live under research/pipeline/ so they never
    # intermix with the human-authored source notes at the top of research/.
    return root / "research" / "pipeline"


def category_dir(root: Path, category: str) -> Path:
    return _research_root(root) / slugify(category)


def _findings_path(root: Path, slug: str) -> Path:
    return category_dir(root, slug) / "findings.json"


def _pipeline_path(root: Path, slug: str) -> Path:
    return category_dir(root, slug) / "pipeline.json"


def _log_path(root: Path, slug: str) -> Path:
    return category_dir(root, slug) / "research-log.ndjson"


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


# --- init ------------------------------------------------------------------


def init_research(root: Path, category: str) -> dict[str, Any]:
    """Scaffold ``research/<slug>/`` with empty (schema-valid) findings + pipeline.

    Idempotent: never clobbers an existing findings.json or pipeline.json.
    """
    slug = slugify(category)
    directory = category_dir(root, slug)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "inbox").mkdir(exist_ok=True)

    created: list[str] = []
    now = utc_now()

    findings_path = _findings_path(root, slug)
    if not findings_path.is_file():
        findings = {
            "schema_version": "1.0",
            "category": slug,
            "generated_at": now,
            "evidence_mode": "none",
            "findings": [],
        }
        _write_findings(root, slug, findings)
        created.append(_rel(root, findings_path))

    pipeline_path = _pipeline_path(root, slug)
    if not pipeline_path.is_file():
        pipeline = {
            "schema_version": "1.0",
            "category": slug,
            "generated_at": now,
            "evidence_mode": "none",
            "category_overview": {},
            "products": {},
        }
        _write_pipeline(root, slug, pipeline)
        created.append(_rel(root, pipeline_path))

    log_path = _log_path(root, slug)
    if not log_path.is_file():
        log_path.write_text("", encoding="utf-8")
        created.append(_rel(root, log_path))

    log_event(root, slug, "init", {"created": created})
    return {
        "status": "ok",
        "category": slug,
        "dir": _rel(root, directory),
        "created": created,
        "already_present": not created,
    }


# --- read/write helpers (validated) ----------------------------------------


def _write_findings(root: Path, slug: str, data: dict[str, Any]) -> None:
    errors = validate_data(root, data, _FINDINGS_SCHEMA)
    if errors:
        raise ValueError(f"findings.json invalid: {'; '.join(errors)}")
    atomic_write_json(_findings_path(root, slug), data)


def _write_pipeline(root: Path, slug: str, data: dict[str, Any]) -> None:
    errors = validate_data(root, data, _PIPELINE_SCHEMA)
    if errors:
        raise ValueError(f"pipeline.json invalid: {'; '.join(errors)}")
    atomic_write_json(_pipeline_path(root, slug), data)


def _load_findings(root: Path, slug: str) -> dict[str, Any]:
    path = _findings_path(root, slug)
    if not path.is_file():
        raise FileNotFoundError(f"No findings.json for category {slug!r}; run `research init {slug}` first.")
    return load_json(path)


def _load_pipeline(root: Path, slug: str) -> dict[str, Any]:
    path = _pipeline_path(root, slug)
    if not path.is_file():
        raise FileNotFoundError(f"No pipeline.json for category {slug!r}; run `research init {slug}` first.")
    return load_json(path)


# --- validate --------------------------------------------------------------


def validate_research(root: Path, category: str) -> dict[str, Any]:
    """Schema-validate findings + pipeline, then check evidence-ref resolution
    and audience/product_type enums beyond what the schema alone catches."""
    slug = slugify(category)
    errors: list[str] = []

    findings = _load_findings(root, slug)
    pipeline = _load_pipeline(root, slug)

    errors.extend(f"findings.json: {e}" for e in validate_data(root, findings, _FINDINGS_SCHEMA))
    errors.extend(f"pipeline.json: {e}" for e in validate_data(root, pipeline, _PIPELINE_SCHEMA))

    known_ids = {f.get("id") for f in findings.get("findings", [])}

    # Every evidence_ref (in products and in category_overview) must resolve.
    def _check_refs(refs: Any, where: str) -> None:
        for ref in refs or []:
            if ref and ref not in known_ids:
                errors.append(f"pipeline.json: {where} references unknown evidence id {ref!r}")

    overview = pipeline.get("category_overview", {})
    for key in ("trending_types", "categories"):
        for entry in overview.get(key, []):
            ref = entry.get("evidence_ref")
            if ref:
                _check_refs([ref], f"category_overview.{key}")
    for key in ("seo", "size_norms"):
        ref = overview.get(key, {}).get("evidence_ref")
        if ref:
            _check_refs([ref], f"category_overview.{key}")

    for pid, product in pipeline.get("products", {}).items():
        _check_refs(product.get("evidence_refs"), f"products.{pid}.evidence_refs")
        if product.get("audience") not in _AUDIENCE_BANDS:
            errors.append(f"pipeline.json: products.{pid}.audience {product.get('audience')!r} not a valid band")
        if product.get("product_type") not in _PRODUCT_TYPES:
            errors.append(f"pipeline.json: products.{pid}.product_type {product.get('product_type')!r} not a valid type")
        if product.get("product_id") != pid:
            errors.append(f"pipeline.json: products.{pid}.product_id must equal its key")

    products = pipeline.get("products", {})
    return {
        "status": "pass" if not errors else "fail",
        "valid": not errors,
        "category": slug,
        "errors": errors,
        "counts": {
            "findings": len(findings.get("findings", [])),
            "products": len(products),
            "candidates": sum(1 for p in products.values() if p.get("status") == "candidate"),
            "promoted": sum(1 for p in products.values() if p.get("status") == "promoted"),
        },
    }


# --- pipeline-add (merge one product entry, no clobber of promoted) --------


def pipeline_add(root: Path, category: str, entry: Any) -> dict[str, Any]:
    """Validate and merge a single product entry into pipeline.json.

    Refuses to overwrite an entry whose status is already ``promoted`` (that would
    silently detach a live project from its backlog record). New/candidate entries
    merge in and the whole pipeline is re-validated before writing.
    """
    slug = slugify(category)
    if not isinstance(entry, dict):
        raise ValueError("pipeline entry must be a JSON object")
    pid = entry.get("product_id")
    if not pid:
        raise ValueError("pipeline entry must include product_id")

    pipeline = _load_pipeline(root, slug)
    products = pipeline.setdefault("products", {})

    existing = products.get(pid)
    if existing and existing.get("status") == "promoted":
        raise ValueError(
            f"product {pid!r} is already promoted (project {existing.get('promoted_project_id')!r}); "
            "refusing to overwrite. Edit the project directly or add a new product_id."
        )

    entry.setdefault("status", "candidate")
    products[pid] = entry
    pipeline["generated_at"] = utc_now()

    _write_pipeline(root, slug, pipeline)  # re-validates the whole file
    log_event(root, slug, "pipeline-add", {"product_id": pid, "status": entry["status"]})
    return {"status": "ok", "category": slug, "product_id": pid, "product_status": entry["status"],
            "products": len(products)}


def promote(root: Path, category: str, product_id: str, project_id: str) -> dict[str, Any]:
    """Flip a candidate entry to ``promoted`` and record its project id.

    Used by ``/product-new`` after it creates the DISCOVERY project. Does NOT touch
    the project itself — pure backlog bookkeeping.
    """
    slug = slugify(category)
    pipeline = _load_pipeline(root, slug)
    product = pipeline.get("products", {}).get(product_id)
    if product is None:
        raise ValueError(f"unknown product_id {product_id!r} in category {slug!r}")
    if product.get("status") == "promoted" and product.get("promoted_project_id") not in (None, project_id):
        raise ValueError(
            f"product {product_id!r} already promoted to {product.get('promoted_project_id')!r}"
        )
    product["status"] = "promoted"
    product["promoted_project_id"] = project_id
    pipeline["generated_at"] = utc_now()
    _write_pipeline(root, slug, pipeline)
    log_event(root, slug, "promote", {"product_id": product_id, "project_id": project_id})
    return {"status": "ok", "category": slug, "product_id": product_id, "promoted_project_id": project_id}


# --- show ------------------------------------------------------------------


def show_research(root: Path, category: str, product_id: str | None = None) -> dict[str, Any]:
    """Print the pipeline (or one product entry). ``/product-new`` reads one entry."""
    slug = slugify(category)
    pipeline_path = _pipeline_path(root, slug)
    if not pipeline_path.is_file():
        return {"status": "absent", "category": slug,
                "note": f"No pipeline for {slug!r}. Run `/research \"{category}\"` first."}
    pipeline = load_json(pipeline_path)
    products = pipeline.get("products", {})

    if product_id is not None:
        product = products.get(product_id)
        if product is None:
            return {
                "status": "not-found", "category": slug, "product_id": product_id,
                "available_ids": sorted(products.keys()),
                "note": f"No product {product_id!r} in category {slug!r}.",
            }
        # Resolve the entry's evidence refs inline so /product-new can cite them.
        findings = load_json(_findings_path(root, slug)) if _findings_path(root, slug).is_file() else {"findings": []}
        by_id = {f["id"]: f for f in findings.get("findings", [])}
        evidence = [by_id[r] for r in product.get("evidence_refs", []) if r in by_id]
        return {"status": "ok", "category": slug, "product": product, "evidence": evidence}

    return {
        "status": "ok",
        "category": slug,
        "evidence_mode": pipeline.get("evidence_mode"),
        "generated_at": pipeline.get("generated_at"),
        "category_overview": pipeline.get("category_overview", {}),
        "product_ids": sorted(products.keys()),
        "counts": {
            "products": len(products),
            "candidates": sum(1 for p in products.values() if p.get("status") == "candidate"),
            "promoted": sum(1 for p in products.values() if p.get("status") == "promoted"),
        },
        "products": products,
    }


# --- log -------------------------------------------------------------------


def log_event(root: Path, category: str, event: str, detail: Any = None) -> dict[str, Any]:
    """Append one line to research-log.ndjson (append-only history)."""
    slug = slugify(category)
    directory = category_dir(root, slug)
    directory.mkdir(parents=True, exist_ok=True)
    record = {"at": utc_now(), "event": event, "detail": detail if detail is not None else {}}
    line = json.dumps(record, ensure_ascii=False, sort_keys=False)
    log_path = _log_path(root, slug)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return {"status": "logged", "category": slug, "event": event}
