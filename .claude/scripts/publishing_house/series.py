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
from .project import init_project, validate_file_data
from .util import (
    atomic_write_yaml,
    load_json,
    load_yaml,
    parse_csv,
    project_lock,
    slugify,
    utc_now,
)


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
    for optional in ("audience", "book_type"):
        if entry.get(optional):
            slot[optional] = entry[optional]
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
    audience: str = "middle-grade-9-12",
    language: str = "en-US",
    series_id: str | None = None,
    book_type: str | None = None,
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
        "schema_version": "1.0",
        "series_id": series_id,
        "series_title": series_title,
        "premise": premise,
        "audience": audience,
        "language": language,
        "created_at": utc_now(),
        "created_by": created_by,
        "books": slots,
    }
    if book_type:
        manifest["book_type"] = book_type
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
        "series": load_yaml(paths.manifest),
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
    book_type: str | None = None,
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
        manifest = load_yaml(paths.manifest)
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
        resolved_type = (
            book_type or slot.get("book_type") or manifest.get("book_type") or "nonfiction"
        )
        book_formats = formats or slot.get("formats") or ["epub"]
        prior = _prior_project_ids(manifest, slot)

        result = init_project(
            root,
            topic=slot["topic"],
            audience=book_audience,
            book_type=resolved_type,
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
    sync_series_catalog(root)
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
            "book_type": resolved_type,
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
        manifest = load_yaml(paths.manifest)
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
    sync_series_catalog(root)
    return {"series_id": series_id, "position": int(position), "project_id": project_id}


def list_series(root: Path) -> list[dict[str, Any]]:
    series_dir = root / "series"
    output: list[dict[str, Any]] = []
    if not series_dir.exists():
        return output
    for manifest_path in sorted(series_dir.glob("*/series.yaml")):
        try:
            manifest = load_yaml(manifest_path)
            books = manifest.get("books", [])
            output.append(
                {
                    "series_id": manifest["series_id"],
                    "series_title": manifest["series_title"],
                    "audience": manifest.get("audience"),
                    "planned_books": len(books),
                    "created_books": sum(1 for b in books if b.get("project_id")),
                    "created_at": manifest.get("created_at"),
                }
            )
        except Exception as exc:  # noqa: BLE001
            output.append({"series_id": manifest_path.parent.name, "error": str(exc)})
    return output


def series_status(root: Path, series_id: str) -> dict[str, Any]:
    """Roll up each book's state, gates, and open findings without mutation."""
    from .project import project_status

    paths = SeriesPaths(root, series_id).require()
    manifest = load_yaml(paths.manifest)
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
    manifest = load_yaml(series_paths.manifest)
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
    manifest = load_yaml(paths.manifest)
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


def sync_series_catalog(root: Path) -> dict[str, Any]:
    from .util import atomic_write_json

    catalog = {"schema_version": "1.0", "series": list_series(root)}
    (root / "catalog").mkdir(parents=True, exist_ok=True)
    atomic_write_json(root / "catalog" / "series.json", catalog)
    return catalog
