"""Series (book-set) layer that sits above individual book projects.

A *series* groups several books that ship as a set (for example a three-book
"A Visual Introduction to Volcanoes" progressing basic -> mid -> advanced).
Each book remains a normal, independent project under ``projects/<id>/`` with
its own ``state.json``, approvals, freezes, and release gates. This module never
weakens or bypasses those per-book gates; it only records the shared plan and
the cross-book links so a book knows what its siblings cover.

Canonical authority for the set is ``series/<series-id>/series.yaml``. Each book
carries a back-reference under ``project.yaml`` ``series`` block. The two are
kept consistent here so neither side silently drifts.

The module is deterministic and offline: no network and no side effects beyond
writing the series manifest, its event log, and (via ``init_project``) the newly
created book project. It performs no external writes, approvals, freezes, or
releases.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ValidationFailure
from .events import append_event, read_events
from .paths import ProjectPaths, SeriesPaths
from .project import init_project, sync_catalog, validate_file_data
from .util import (
    atomic_write_yaml,
    load_json,
    load_yaml,
    parse_csv,
    project_lock,
    slugify,
    utc_now,
)


SCHEMA_VERSION = "1.1"

# Default product-framework values used when a slot/manifest does not name one.
# These replace the grafted novel-framework defaults ("nonfiction", ["epub"],
# "middle-grade-9-12") that were never valid product vocabulary.
DEFAULT_PRODUCT_TYPE = "puzzle-book"
DEFAULT_FORMATS = ["paperback"]
DEFAULT_AUDIENCE = "adult-general"

# Best-effort map from the legacy 1.0 novel-framework enums to the product
# vocabulary, used only for in-memory migration of an existing 1.0 manifest.
# Unknown legacy values fall back to the product defaults above.
_LEGACY_AUDIENCE_MAP = {
    "early-reader-6-8": "kids-6-10",
    "middle-grade-9-12": "tween-8-12",
    "teen-13-17": "teen-13-17",
    "adult-general": "adult-general",
    "adult-specialist": "adult-general",
}
_PRODUCT_AUDIENCES = {
    "kids-4-8",
    "kids-6-10",
    "tween-8-12",
    "teen-13-17",
    "adult-general",
    "senior-large-print",
}
_PRODUCT_TYPES = {
    "puzzle-book",
    "activity-book",
    "coloring-book",
    "guided-journal",
    "workbook",
    "planner",
    "digital-printable",
}
_LEGACY_TYPE_MAP = {
    "activity-book": "activity-book",
    "picture-book": "coloring-book",
}
_LEGACY_FORMAT_MAP = {
    "epub": "digital-pdf",
    "fixed-layout-epub": "digital-pdf",
    "paperback": "paperback",
    "hardcover": "hardcover",
    # audiobook / read-along have no product-framework equivalent -> dropped.
}
_PRODUCT_FORMATS = {"paperback", "hardcover", "digital-pdf"}


def _migrate_audience(value: Any) -> str | None:
    if value in _PRODUCT_AUDIENCES:
        return value
    return _LEGACY_AUDIENCE_MAP.get(value, DEFAULT_AUDIENCE) if value else None


def _migrate_product_type(value: Any) -> str | None:
    if value in _PRODUCT_TYPES:
        return value
    return _LEGACY_TYPE_MAP.get(value, DEFAULT_PRODUCT_TYPE) if value else None


def _migrate_formats(value: Any) -> list[str] | None:
    if not value:
        return None
    mapped: list[str] = []
    for fmt in value:
        if fmt in _PRODUCT_FORMATS:
            candidate = fmt
        else:
            candidate = _LEGACY_FORMAT_MAP.get(fmt)
        if candidate and candidate not in mapped:
            mapped.append(candidate)
    return mapped or None


def _migrate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Return a product-vocabulary copy of ``manifest`` (in memory, non-destructive).

    A 1.0 manifest carries novel-framework enums and a ``book_type`` field; this
    maps them to the product vocabulary and renames ``book_type`` -> ``product_type``
    so every downstream reader sees one consistent schema. A 1.1 manifest is
    returned essentially unchanged (idempotent). The on-disk file is NOT rewritten
    here; migration happens on read (see rule 5: no destructive rewrite).
    """
    migrated = dict(manifest)
    audience = _migrate_audience(migrated.get("audience"))
    if audience:
        migrated["audience"] = audience
    # Fold the deprecated top-level book_type into product_type.
    legacy_type = migrated.pop("book_type", None)
    resolved_type = _migrate_product_type(migrated.get("product_type") or legacy_type)
    if resolved_type:
        migrated["product_type"] = resolved_type

    books: list[dict[str, Any]] = []
    for slot in migrated.get("books", []):
        slot = dict(slot)
        slot_aud = slot.get("audience")
        if slot_aud:
            slot["audience"] = _migrate_audience(slot_aud)
        slot_legacy = slot.pop("book_type", None)
        slot_type = slot.get("product_type") or slot_legacy
        if slot_type:
            slot["product_type"] = _migrate_product_type(slot_type)
        slot_formats = _migrate_formats(slot.get("formats"))
        if slot_formats is not None:
            slot["formats"] = slot_formats
        elif "formats" in slot:
            del slot["formats"]
        books.append(slot)
    migrated["books"] = books
    return migrated


def _load_manifest(path: Path) -> dict[str, Any]:
    """Load a series manifest and migrate legacy vocabulary in memory."""
    return _migrate_manifest(load_yaml(path))


def generate_series_id(title: str) -> str:
    return f"series-{slugify(title, 48)}"


def _book_slot(entry: dict[str, Any]) -> dict[str, Any]:
    """Normalise one planned-book entry into a schema-valid slot."""
    if not entry.get("working_title"):
        raise ValidationFailure("Each planned book needs a working_title")
    if not entry.get("topic"):
        raise ValidationFailure("Each planned book needs a topic")
    if not entry.get("scope"):
        raise ValidationFailure(
            "Each planned book needs a scope describing what it covers"
        )
    slot: dict[str, Any] = {
        "position": int(entry["position"]),
        "working_title": entry["working_title"],
        "topic": entry["topic"],
        "scope": entry["scope"],
    }
    if entry.get("audience"):
        slot["audience"] = entry["audience"]
    # product_type is canonical; book_type is a deprecated alias for one release.
    slot_type = entry.get("product_type") or entry.get("book_type")
    if slot_type:
        slot["product_type"] = slot_type
    formats = entry.get("formats")
    if formats:
        slot["formats"] = parse_csv(formats) if isinstance(formats, str) else list(formats)
    assumes = entry.get("assumes_prior_positions")
    if assumes:
        slot["assumes_prior_positions"] = sorted({int(x) for x in assumes})
    slot["project_id"] = entry.get("project_id")
    return slot


def _order_books(books: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positions = [book["position"] for book in books]
    if len(set(positions)) != len(positions):
        raise ValidationFailure("Duplicate book positions in series plan")
    return sorted(books, key=lambda book: book["position"])


def init_series(
    root: Path,
    series_title: str,
    premise: str,
    books: list[dict[str, Any]],
    audience: str = DEFAULT_AUDIENCE,
    language: str = "en-US",
    series_id: str | None = None,
    product_type: str | None = None,
    progression: str | None = None,
    shared_canon: dict[str, Any] | None = None,
    created_by: str = "human",
    create_first_book: bool = True,
) -> dict[str, Any]:
    """Create a series manifest from an approved plan.

    ``books`` is the ordered plan produced by the series workshop. By default the
    first planned book is created immediately as its own project (manifest-first,
    book-1-now); later books are created on demand with :func:`add_book`.
    """
    series_id = slugify(series_id or generate_series_id(series_title), 80)
    paths = SeriesPaths(root, series_id)
    if paths.directory.exists():
        raise ValidationFailure(f"Series already exists: {series_id}")
    if not books:
        raise ValidationFailure("A series needs at least one planned book")

    slots = _order_books([_book_slot(book) for book in books])
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "series_id": series_id,
        "series_title": series_title,
        "premise": premise,
        "audience": audience,
        "language": language,
        "created_at": utc_now(),
        "created_by": created_by,
        "books": slots,
    }
    if product_type:
        manifest["product_type"] = product_type
    if progression:
        manifest["progression"] = progression
    if shared_canon:
        manifest["shared_canon"] = shared_canon
    manifest["status_notes"] = ""

    errors = validate_file_data(root, manifest, "series.schema.json")
    if errors:
        raise ValidationFailure("Invalid series manifest: " + "; ".join(errors))

    paths.directory.mkdir(parents=True, exist_ok=True)
    atomic_write_yaml(paths.manifest, manifest)
    paths.events.touch()
    append_event(
        paths.events,
        series_id,
        "SERIES_CREATED",
        created_by,
        {"series_title": series_title, "planned_books": len(slots)},
    )
    sync_series_catalog(root)

    created_book: dict[str, Any] | None = None
    if create_first_book:
        created_book = add_book(
            root,
            series_id,
            position=slots[0]["position"],
            created_by=created_by,
        )["book"]

    return {
        "series": _load_manifest(paths.manifest),
        "path": paths.directory.as_posix(),
        "created_book": created_book,
    }


def _prior_project_ids(manifest: dict[str, Any], slot: dict[str, Any]) -> list[str]:
    """Resolve created sibling project IDs a book may assume as prior context.

    Defaults to every lower-positioned book when ``assumes_prior_positions`` is
    not set, so a linear progression links backwards automatically. Only books
    that already exist as projects are linked.
    """
    by_position = {book["position"]: book for book in manifest["books"]}
    if slot.get("assumes_prior_positions"):
        wanted = sorted(set(slot["assumes_prior_positions"]))
    else:
        wanted = sorted(p for p in by_position if p < slot["position"])
    prior: list[str] = []
    for position in wanted:
        sibling = by_position.get(position)
        if sibling and sibling.get("project_id"):
            prior.append(sibling["project_id"])
    return prior


def add_book(
    root: Path,
    series_id: str,
    position: int,
    project_id: str | None = None,
    formats: list[str] | str | None = None,
    audience: str | None = None,
    product_type: str | None = None,
    created_by: str = "human",
) -> dict[str, Any]:
    """Create the planned book at ``position`` as its own project and link it.

    Craft parameters are derived per book by ``init_project`` from that book's
    audience and type (a book may progress to a different band than the series
    default). The link is written in both directions: the manifest slot records
    the new ``project_id`` and the project's ``series`` block records its
    position and prior siblings.
    """
    paths = SeriesPaths(root, series_id).require()
    with project_lock(paths.lock):
        manifest = _load_manifest(paths.manifest)
        by_position = {book["position"]: book for book in manifest["books"]}
        slot = by_position.get(int(position))
        if slot is None:
            raise ValidationFailure(
                f"No planned book at position {position} in series {series_id}"
            )
        if slot.get("project_id"):
            raise ValidationFailure(
                f"Book at position {position} already created as "
                f"project {slot['project_id']}"
            )

        book_audience = audience or slot.get("audience") or manifest["audience"]
        # product_type is canonical; slot/manifest may still carry the deprecated
        # book_type alias, already folded into product_type by _load_manifest.
        resolved_type = (
            product_type
            or slot.get("product_type")
            or manifest.get("product_type")
            or DEFAULT_PRODUCT_TYPE
        )
        book_formats = formats or slot.get("formats") or list(DEFAULT_FORMATS)
        prior = _prior_project_ids(manifest, slot)

        result = init_project(
            root,
            topic=slot["topic"],
            audience=book_audience,
            product_type=resolved_type,
            formats=book_formats,
            project_id=project_id,
            language=manifest["language"],
            working_title=slot["working_title"],
            created_by=created_by,
        )
        new_project_id = result["project"]["project_id"]

        # Write the back-reference into the book project's config.
        book_paths = ProjectPaths(root, new_project_id).require()
        project = load_yaml(book_paths.config)
        project["series"] = {
            "series_id": series_id,
            "position": int(position),
            "total_planned": len(manifest["books"]),
            "prior_project_ids": prior,
        }
        proj_errors = validate_file_data(root, project, "project.schema.json")
        if proj_errors:
            raise ValidationFailure(
                "Series back-reference invalidated project: " + "; ".join(proj_errors)
            )
        atomic_write_yaml(book_paths.config, project)
        append_event(
            book_paths.events,
            new_project_id,
            "SERIES_LINKED",
            created_by,
            {"series_id": series_id, "position": int(position), "prior_project_ids": prior},
        )

        # Record the created project in the manifest slot.
        slot["project_id"] = new_project_id
        errors = validate_file_data(root, manifest, "series.schema.json")
        if errors:
            raise ValidationFailure("Invalid series manifest: " + "; ".join(errors))
        atomic_write_yaml(paths.manifest, manifest)
        append_event(
            paths.events,
            series_id,
            "SERIES_BOOK_CREATED",
            created_by,
            {"position": int(position), "project_id": new_project_id},
        )
    # Keep both catalogs consistent in one operation: series.json gains the new
    # member + slot roll-up, products.json gains the product's series back-ref.
    sync_series_catalog(root)
    sync_catalog(root)
    resolved_formats = (
        parse_csv(book_formats) if isinstance(book_formats, str) else list(book_formats)
    )
    return {
        "series_id": series_id,
        "position": int(position),
        "book": {
            "project_id": new_project_id,
            "path": result["path"],
            "prior_project_ids": prior,
            "audience": book_audience,
            "product_type": resolved_type,
            "book_type": resolved_type,  # deprecated alias, one release
            "formats": resolved_formats,
        },
    }


def link_book(
    root: Path,
    series_id: str,
    position: int,
    project_id: str,
    created_by: str = "human",
) -> dict[str, Any]:
    """Attach an already-existing project to a planned series slot.

    Use this when a standalone book was created first and later folded into a
    set. It does not change the book's craft parameters or state; it only writes
    the bidirectional link.
    """
    paths = SeriesPaths(root, series_id).require()
    book_paths = ProjectPaths(root, project_id).require()
    with project_lock(paths.lock):
        manifest = _load_manifest(paths.manifest)
        by_position = {book["position"]: book for book in manifest["books"]}
        slot = by_position.get(int(position))
        if slot is None:
            raise ValidationFailure(
                f"No planned book at position {position} in series {series_id}"
            )
        if slot.get("project_id") and slot["project_id"] != project_id:
            raise ValidationFailure(
                f"Position {position} already linked to {slot['project_id']}"
            )
        for other in manifest["books"]:
            if other["position"] != int(position) and other.get("project_id") == project_id:
                raise ValidationFailure(
                    f"Project {project_id} already linked at position {other['position']}"
                )

        prior = _prior_project_ids(manifest, slot)
        project = load_yaml(book_paths.config)
        project["series"] = {
            "series_id": series_id,
            "position": int(position),
            "total_planned": len(manifest["books"]),
            "prior_project_ids": prior,
        }
        proj_errors = validate_file_data(root, project, "project.schema.json")
        if proj_errors:
            raise ValidationFailure(
                "Series back-reference invalidated project: " + "; ".join(proj_errors)
            )
        atomic_write_yaml(book_paths.config, project)
        append_event(
            book_paths.events,
            project_id,
            "SERIES_LINKED",
            created_by,
            {"series_id": series_id, "position": int(position), "prior_project_ids": prior},
        )

        slot["project_id"] = project_id
        errors = validate_file_data(root, manifest, "series.schema.json")
        if errors:
            raise ValidationFailure("Invalid series manifest: " + "; ".join(errors))
        atomic_write_yaml(paths.manifest, manifest)
        append_event(
            paths.events,
            series_id,
            "SERIES_BOOK_LINKED",
            created_by,
            {"position": int(position), "project_id": project_id},
        )
    # Fold-in also touches both catalogs (series membership + product back-ref).
    sync_series_catalog(root)
    sync_catalog(root)
    return {"series_id": series_id, "position": int(position), "project_id": project_id}


def list_series(root: Path) -> list[dict[str, Any]]:
    series_dir = root / "series"
    output: list[dict[str, Any]] = []
    if not series_dir.exists():
        return output
    for manifest_path in sorted(series_dir.glob("*/series.yaml")):
        try:
            manifest = _load_manifest(manifest_path)
            books = _order_books(list(manifest.get("books", [])))
            slots: list[dict[str, Any]] = []
            member_project_ids: list[str] = []
            for slot in books:
                project_id = slot.get("project_id")
                state: str | None = None
                if project_id:
                    member_project_ids.append(project_id)
                    try:
                        state = load_json(ProjectPaths(root, project_id).state).get(
                            "current_state"
                        )
                    except Exception:  # noqa: BLE001
                        state = "ERROR"
                slots.append(
                    {"position": slot["position"], "project_id": project_id, "state": state}
                )
            output.append(
                {
                    "series_id": manifest["series_id"],
                    "series_title": manifest["series_title"],
                    "audience": manifest.get("audience"),
                    "product_type": manifest.get("product_type"),
                    "planned_books": len(books),
                    "created_books": len(member_project_ids),
                    "created_at": manifest.get("created_at"),
                    "member_project_ids": member_project_ids,
                    "slots": slots,
                }
            )
        except Exception as exc:  # noqa: BLE001
            output.append({"series_id": manifest_path.parent.name, "error": str(exc)})
    return output


def series_status(root: Path, series_id: str) -> dict[str, Any]:
    """Roll up each book's state, gates, and open findings without mutation."""
    from .project import project_status

    paths = SeriesPaths(root, series_id).require()
    manifest = _load_manifest(paths.manifest)
    books: list[dict[str, Any]] = []
    for slot in _order_books(list(manifest.get("books", []))):
        entry: dict[str, Any] = {
            "position": slot["position"],
            "working_title": slot["working_title"],
            "scope": slot["scope"],
            "assumes_prior_positions": slot.get("assumes_prior_positions"),
            "project_id": slot.get("project_id"),
            "created": bool(slot.get("project_id")),
        }
        if slot.get("project_id"):
            try:
                status = project_status(root, slot["project_id"])
                entry["state"] = status["state"]["current_state"]
                entry["open_findings"] = status["open_findings"]
                entry["validation"] = status["validation"]["status"]
            except Exception as exc:  # noqa: BLE001
                entry["state"] = "ERROR"
                entry["error"] = str(exc)
        books.append(entry)
    return {
        "series_id": series_id,
        "series_title": manifest["series_title"],
        "audience": manifest.get("audience"),
        "progression": manifest.get("progression"),
        "planned_books": len(books),
        "created_books": sum(1 for b in books if b["created"]),
        "books": books,
        "recent_events": read_events(paths.events, limit=10),
    }


def sibling_context(root: Path, project_id: str) -> dict[str, Any]:
    """Read-only view of a book's series siblings, for outline/draft context.

    Returns what earlier books cover (so this book does not re-teach it) and the
    shared canon the set must keep consistent. Never mutates a sibling.
    """
    book_paths = ProjectPaths(root, project_id).require()
    project = load_yaml(book_paths.config)
    link = project.get("series")
    if not link:
        return {"project_id": project_id, "in_series": False}
    series_paths = SeriesPaths(root, link["series_id"]).require()
    manifest = _load_manifest(series_paths.manifest)
    by_position = {book["position"]: book for book in manifest.get("books", [])}
    priors: list[dict[str, Any]] = []
    for prior_id in link.get("prior_project_ids", []):
        slot = next((b for b in manifest["books"] if b.get("project_id") == prior_id), None)
        priors.append(
            {
                "project_id": prior_id,
                "position": slot.get("position") if slot else None,
                "working_title": slot.get("working_title") if slot else None,
                "scope": slot.get("scope") if slot else None,
            }
        )
    later = [
        {
            "position": b["position"],
            "working_title": b["working_title"],
            "scope": b["scope"],
            "project_id": b.get("project_id"),
        }
        for b in sorted(by_position.values(), key=lambda b: b["position"])
        if b["position"] > link["position"]
    ]
    return {
        "project_id": project_id,
        "in_series": True,
        "series_id": link["series_id"],
        "series_title": manifest["series_title"],
        "position": link["position"],
        "total_planned": link.get("total_planned"),
        "progression": manifest.get("progression"),
        "shared_canon": manifest.get("shared_canon", {}),
        "covers_earlier": priors,
        "covered_later": later,
    }


# States that sit off the linear production path; their order index is not a
# meaningful measure of "progress toward a milestone".
_OFF_PATH_STATES = frozenset({"PAUSED", "CANCELLED", "ERROR"})


def series_milestone(
    root: Path,
    series_id: str,
    target_state: str = "PUBLISHED",
) -> dict[str, Any]:
    """Report how far the whole set is toward a target lifecycle state.

    Pure reporting: reads each book's ``state.json`` and answers "has every
    created book reached at least ``target_state`` on the linear production
    path?" It creates no gate, grants nothing, and mutates no state. A milestone
    is ``reached`` only when every PLANNED book exists AND every book is at or
    beyond the target on the main path. Off-path books (paused/cancelled/error)
    are reported separately and always hold the milestone open.
    """
    paths = SeriesPaths(root, series_id).require()
    manifest = _load_manifest(paths.manifest)
    order = load_json(root / ".claude" / "config" / "workflow_states.json").get("states", [])
    if target_state not in order:
        raise ValidationFailure(f"Unknown target state: {target_state}")
    target_index = order.index(target_state)

    books: list[dict[str, Any]] = []
    all_created = True
    all_reached = True
    for slot in _order_books(list(manifest.get("books", []))):
        entry: dict[str, Any] = {
            "position": slot["position"],
            "working_title": slot["working_title"],
            "project_id": slot.get("project_id"),
        }
        if not slot.get("project_id"):
            all_created = False
            all_reached = False
            entry.update({"created": False, "state": None, "reached": False, "off_path": False})
            books.append(entry)
            continue
        entry["created"] = True
        try:
            state = load_json(ProjectPaths(root, slot["project_id"]).state).get("current_state")
        except Exception as exc:  # noqa: BLE001
            entry.update({"state": "ERROR", "reached": False, "off_path": True, "error": str(exc)})
            all_reached = False
            books.append(entry)
            continue
        off_path = state in _OFF_PATH_STATES
        reached = (not off_path) and state in order and order.index(state) >= target_index
        entry.update({"state": state, "reached": reached, "off_path": off_path})
        if not reached:
            all_reached = False
        books.append(entry)

    return {
        "series_id": series_id,
        "series_title": manifest["series_title"],
        "target_state": target_state,
        "planned_books": len(books),
        "created_books": sum(1 for b in books if b["created"]),
        "books_reached": sum(1 for b in books if b["reached"]),
        "off_path_books": [b for b in books if b.get("off_path")],
        "all_books_created": all_created,
        "milestone_reached": all_created and all_reached,
        "books": books,
    }


def series_recommend(
    root: Path,
    series_id: str,
    target_state: str = "PUBLISHED",
) -> dict[str, Any]:
    """Return the single 'next actionable volume' for a set (read-only).

    Deterministic priority:
      1. the first planned-but-uncreated slot -> recommend ``series add-book``;
      2. otherwise the lowest-position CREATED volume not yet at ``target_state``
         (skipping off-path volumes) -> return that volume's ``plan_next``;
      3. otherwise the set is complete for this target -> ``done``.

    Wraps :func:`series_status` and :func:`series_milestone`; grants nothing,
    creates nothing, mutates no state. The ``/hi`` router calls this for
    ``/hi series <id>``.
    """
    from .planner import plan_next

    milestone = series_milestone(root, series_id, target_state)
    status = series_status(root, series_id)
    by_position = {b["position"]: b for b in status["books"]}

    result: dict[str, Any] = {
        "series_id": series_id,
        "series_title": milestone["series_title"],
        "target_state": target_state,
        "milestone_reached": milestone["milestone_reached"],
        "recommendation": None,
    }

    # 1. First planned-but-uncreated slot.
    uncreated = sorted(
        (b for b in milestone["books"] if not b.get("created")),
        key=lambda b: b["position"],
    )
    if uncreated:
        nxt = uncreated[0]
        result["recommendation"] = {
            "kind": "create_volume",
            "position": nxt["position"],
            "working_title": nxt.get("working_title"),
            "suggested_command": f"series add-book {series_id} --position {nxt['position']}",
        }
        return result

    # 2. Lowest-position created volume not yet at target (skip off-path).
    behind = sorted(
        (
            b
            for b in milestone["books"]
            if b.get("created") and not b.get("reached") and not b.get("off_path")
        ),
        key=lambda b: b["position"],
    )
    if behind:
        vol = behind[0]
        project_id = vol["project_id"]
        slot = by_position.get(vol["position"], {})
        result["recommendation"] = {
            "kind": "advance_volume",
            "position": vol["position"],
            "project_id": project_id,
            "state": vol.get("state"),
            "working_title": slot.get("working_title"),
            "plan_next": plan_next(root, project_id),
        }
        return result

    # 2b. Off-path volumes hold the set open but need a human, not an auto-step.
    off_path = [b for b in milestone["books"] if b.get("off_path")]
    if off_path:
        result["recommendation"] = {
            "kind": "resolve_off_path",
            "off_path_volumes": off_path,
        }
        return result

    # 3. Every volume created and at/beyond target.
    result["recommendation"] = {
        "kind": "done",
        "detail": f"All volumes created and at or beyond {target_state}.",
    }
    return result


def _difficulty_rank(entry: dict[str, Any]) -> int:
    """Coarse ordering hint from a pipeline entry's difficulty tier (low -> high)."""
    tier = str((entry.get("difficulty") or {}).get("tier", "")).lower()
    order = ["intro", "easy", "beginner", "gentle", "medium", "intermediate", "hard", "advanced", "expert", "master"]
    for index, name in enumerate(order):
        if name in tier:
            return index
    return len(order)  # unknown tiers sort last, stable


def _suggestion_sort_key(item: tuple[str, dict[str, Any]]) -> tuple[Any, ...]:
    """Order candidates by explicit series position, then priority, then difficulty.

    Deterministic and total: falls back to the product_id so equal ranks stay stable.
    """
    product_id, entry = item
    grouping = entry.get("series_grouping") or {}
    position = grouping.get("position")
    # Entries with an explicit position lead, in position order; then by priority
    # (lower number = higher priority), then difficulty tier, then id.
    has_position = 0 if position is not None else 1
    priority = entry.get("priority", 10_000)
    return (has_position, position if position is not None else 0, priority, _difficulty_rank(entry), product_id)


def suggest_series_from_research(root: Path, category: str) -> dict[str, Any]:
    """Propose series plans from a category's research backlog (READ-ONLY).

    Groups the category's ``candidate`` pipeline entries into one or more proposed
    series and returns, for each group, a ready-to-run ``series init`` payload
    (title, premise, audience, product_type, and a ``books`` array shaped for
    ``--books-json``). Grouping rule:

      * entries sharing a ``series_grouping.series_slug`` (or ``set``) form a group;
      * remaining ungrouped candidates are grouped by (audience, product_type).

    Within a group, volumes are ordered by explicit ``series_grouping.position``,
    then ``priority``, then difficulty tier. Only groups with >= 2 volumes are
    proposed (a series needs at least two).

    This SUGGESTS only. It does not create a series, does not promote pipeline
    entries, and does not mutate research state. The caller (the add-book skill or
    the ``/hi`` router) presents the plan to a human and runs the create flow.
    """
    from .research import _load_pipeline  # lazy: keep series import-light
    from .util import slugify as _slugify

    slug = _slugify(category)
    pipeline = _load_pipeline(root, slug)  # raises FileNotFoundError if absent
    products: dict[str, Any] = pipeline.get("products", {})

    candidates = {
        pid: entry
        for pid, entry in products.items()
        if entry.get("status") == "candidate"
    }

    # Bucket by explicit series grouping first, else by (audience, product_type).
    groups: dict[str, dict[str, Any]] = {}
    ungrouped: list[tuple[str, dict[str, Any]]] = []
    for pid, entry in candidates.items():
        grouping = entry.get("series_grouping") or {}
        key = grouping.get("series_slug") or grouping.get("set")
        if key:
            bucket = groups.setdefault(
                f"explicit:{key}", {"key": key, "explicit": True, "items": []}
            )
            bucket["items"].append((pid, entry))
        else:
            ungrouped.append((pid, entry))
    for pid, entry in ungrouped:
        key = f"{entry.get('audience')}|{entry.get('product_type')}"
        bucket = groups.setdefault(
            f"auto:{key}", {"key": key, "explicit": False, "items": []}
        )
        bucket["items"].append((pid, entry))

    suggestions: list[dict[str, Any]] = []
    for group in sorted(groups.values(), key=lambda g: (not g["explicit"], g["key"])):
        items = sorted(group["items"], key=_suggestion_sort_key)
        if len(items) < 2:
            continue  # a series needs at least two volumes
        first_entry = items[0][1]
        audience = first_entry.get("audience")
        product_type = first_entry.get("product_type")
        books: list[dict[str, Any]] = []
        for index, (pid, entry) in enumerate(items, start=1):
            grouping = entry.get("series_grouping") or {}
            position = grouping.get("position") or index
            book: dict[str, Any] = {
                "position": position,
                "working_title": entry.get("working_title") or pid,
                "topic": entry.get("working_title") or pid,
                "scope": entry.get("positioning")
                or (entry.get("difficulty") or {}).get("tier")
                or f"Volume {position} of the {category} set",
                "product_type": entry.get("product_type") or product_type,
                "audience": entry.get("audience") or audience,
                "formats": entry.get("formats") or list(DEFAULT_FORMATS),
                # Kept for the skill to drive `research promote` after create;
                # NOT part of the series schema, stripped before series init.
                "source_product_id": pid,
            }
            books.append(book)
        # Renumber positions to be unique/contiguous if the backlog had gaps/dupes.
        for new_position, book in enumerate(sorted(books, key=lambda b: b["position"]), start=1):
            book["position"] = new_position
        title = group["key"] if group["explicit"] else f"{category} {product_type} set"
        suggestions.append(
            {
                "proposed_series_title": title,
                "grouping": "explicit" if group["explicit"] else "audience+product_type",
                "audience": audience,
                "product_type": product_type,
                "premise": f"A {audience} {product_type} set derived from {category} research.",
                "books": books,
                "series_init_payload": {
                    "title": title,
                    "premise": f"A {audience} {product_type} set derived from {category} research.",
                    "audience": audience,
                    "product_type": product_type,
                    # Schema-shaped books (source_product_id retained for promotion;
                    # _book_slot ignores unknown keys, so this stays valid).
                    "books": books,
                },
            }
        )

    return {
        "category": slug,
        "candidate_count": len(candidates),
        "suggested_series_count": len(suggestions),
        "suggestions": suggestions,
        "note": (
            "Read-only suggestion. Creates nothing. To act: run `series init` with a "
            "chosen payload, then `research promote` each created volume."
        ),
    }


def sync_series_catalog(root: Path) -> dict[str, Any]:
    from .util import atomic_write_json

    catalog = {"schema_version": SCHEMA_VERSION, "series": list_series(root)}
    errors = validate_file_data(root, catalog, "series-catalog.schema.json")
    if errors:
        raise ValidationFailure("Invalid series catalog: " + "; ".join(errors))
    (root / "catalog").mkdir(parents=True, exist_ok=True)
    atomic_write_json(root / "catalog" / "series.json", catalog)
    return catalog
