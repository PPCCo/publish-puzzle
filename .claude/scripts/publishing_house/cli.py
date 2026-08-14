from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .accessibility import audit_accessibility
from .approvals import (
    create_release_authorization,
    grant_approval,
    list_approvals,
    release_authorizations,
    verify_release_authorization,
)
from .artifacts import freeze_artifacts, list_artifacts, register_artifact
from .catalog import rebuild_catalog, verify_catalog
from .doctor import run_doctor
from .errors import PublishingHouseError
from .events import read_events
from .gate_packet import build_gate_packet
from .generate import generate_content
from .layout import build_cover, build_interior, build_proof, link_digital_bundle
from .marketing import build_launch_guide, build_listing_kit, build_marketing_kit
from .metadata_audit import audit_metadata
from .niche import assess_niche
from .packages import package_channel
from .planner import plan_next
from .project import init_project, list_projects, project_status, validate_project
from .quality import evaluate_quality
from .rights import add_rights_record, check_rights
from .series import (
    add_book,
    init_series,
    link_book,
    list_series,
    series_milestone,
    series_recommend,
    series_status,
    sibling_context,
    suggest_series_from_research,
)
from .state import next_actions, transition
from .submission import create_dry_run, record_submission
from .util import load_json, repo_root
from .validation import validate_framework
from .verify import verify_content


def _json(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False))


def _load_json_argument(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    path = Path(value)
    if path.exists():
        return load_json(path)
    return json.loads(value)


def _read_stdin_if_dash(value: str | None) -> str | None:
    if value == "-":
        return sys.stdin.read()
    return value


PRODUCT_TYPES = ["puzzle-book", "coloring-book", "guided-journal", "digital-printable"]
AUDIENCE_BANDS = [
    "kids-4-8",
    "kids-6-10",
    "tween-8-12",
    "teen-13-17",
    "adult-general",
    "senior-large-print",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="publishing-house",
        description="Deterministic runtime for the Claude Code puzzle/coloring publishing-house framework.",
    )
    parser.add_argument("--root", help="Repository root. Defaults to auto-detection.")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="Check framework, dependencies, model pin, and optional tools.")
    doctor.add_argument("--probe-plan", action="store_true", help="Print the ordered research connectivity probe plan (offline; no network).")

    connectivity = sub.add_parser("connectivity", help="Read/write the research connectivity manifest (offline; no network).")
    connectivity_sub = connectivity.add_subparsers(dest="connectivity_command", required=True)
    connectivity_sub.add_parser("show", help="Print the connectivity manifest (or an 'unknown' stub if absent).")
    c_write = connectivity_sub.add_parser("write", help="Validate and atomically write the connectivity manifest.")
    c_write.add_argument("--json", required=True, help="Manifest JSON (inline, a file path, or '-' for stdin).")

    fetch = sub.add_parser("fetch", help="Quarantined research fetcher (GET-only, host-allowlisted, cached). Network only with --allow-net or RESEARCH_FETCH_ENABLED=1.")
    fetch.add_argument("--allow-net", action="store_true", help="Enable network for this call (else returns a disabled stub).")
    fetch.add_argument("--no-cache", action="store_true", help="Bypass the on-disk cache (Tier 0).")
    fetch_sub = fetch.add_subparsers(dest="fetch_command", required=True)
    f_search = fetch_sub.add_parser("search", help="Search via an allowlisted HTML endpoint (Tier 2).")
    f_search.add_argument("query")
    f_search.add_argument("--engine", default="ddg")
    f_search.add_argument("--max", type=int, default=10, dest="max_results")
    f_get = fetch_sub.add_parser("get", help="GET one allowlisted URL; body written to cache, path returned (Tier 2).")
    f_get.add_argument("url")
    f_probe = fetch_sub.add_parser("probe", help="Probe Tiers 2->3 for one configured source; report best tier.")
    f_probe.add_argument("source_id")

    research = sub.add_parser("research", help="Offline category-research pipeline (scaffold/validate/merge/show/log). No network.")
    research_sub = research.add_subparsers(dest="research_command", required=True)
    r_init = research_sub.add_parser("init", help="Scaffold research/<category>/ with empty findings + pipeline (idempotent).")
    r_init.add_argument("category")
    r_validate = research_sub.add_parser("validate", help="Schema-validate findings + pipeline; check evidence-ref resolution and enums.")
    r_validate.add_argument("category")
    r_add = research_sub.add_parser("pipeline-add", help="Validate and merge one product entry (never clobbers a promoted entry).")
    r_add.add_argument("category")
    r_add.add_argument("--json", required=True, help="Product entry JSON (inline, a file path, or '-' for stdin).")
    r_promote = research_sub.add_parser("promote", help="Flip a candidate entry to promoted and record its project id (backlog only).")
    r_promote.add_argument("category")
    r_promote.add_argument("--product-id", required=True, dest="product_id")
    r_promote.add_argument("--project-id", required=True, dest="project_id")
    r_show = research_sub.add_parser("show", help="Print the pipeline (or one product entry with resolved evidence).")
    r_show.add_argument("category")
    r_show.add_argument("--product-id", dest="product_id")
    r_log = research_sub.add_parser("log", help="Append one event to research-log.ndjson.")
    r_log.add_argument("category")
    r_log.add_argument("--event", required=True)
    r_log.add_argument("--json", dest="detail_json", help="Event detail JSON (inline, a file path, or '-' for stdin).")

    framework = sub.add_parser("framework", help="Framework-level operations.")
    framework_sub = framework.add_subparsers(dest="framework_command", required=True)
    framework_sub.add_parser("validate", help="Validate agents, skills, workflows, schemas, and settings.")

    project = sub.add_parser("project", help="Product project lifecycle.")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    p_init = project_sub.add_parser("init", help="Create a new puzzle/coloring/journal/printable project.")
    p_init.add_argument("--topic", required=True)
    p_init.add_argument("--audience", default="adult-general")
    p_init.add_argument("--product-type", default="puzzle-book", choices=PRODUCT_TYPES, dest="product_type")
    p_init.add_argument("--formats", default="paperback")
    p_init.add_argument("--project-id")
    p_init.add_argument("--language", default="en-US")
    p_init.add_argument("--working-title")
    p_init.add_argument("--created-by", default="human")
    project_sub.add_parser("list", help="List projects.")
    for name in ("status", "validate", "next", "plan", "recommend"):
        item = project_sub.add_parser(name)
        item.add_argument("project_id")
    p_transition = project_sub.add_parser("transition")
    p_transition.add_argument("project_id")
    p_transition.add_argument("--to", required=True)
    p_transition.add_argument("--actor", required=True)
    p_transition.add_argument("--reason", required=True)

    series = sub.add_parser("series", help="Product-series (multi-volume set) planning and linking.")
    series_sub = series.add_subparsers(dest="series_command", required=True)
    s_init = series_sub.add_parser("init", help="Create a series manifest from an approved plan and (by default) create volume 1.")
    s_init.add_argument("--title", required=True)
    s_init.add_argument("--premise", required=True)
    s_init.add_argument("--books-json", required=True, help="JSON array (or file path) of planned volumes: position, working_title, topic, scope, and optional audience/book_type/formats.")
    s_init.add_argument("--audience", default="adult-general", choices=AUDIENCE_BANDS)
    s_init.add_argument("--language", default="en-US")
    s_init.add_argument("--series-id")
    s_init.add_argument("--product-type", choices=PRODUCT_TYPES, dest="product_type", help="Default product family for the set.")
    s_init.add_argument("--book-type", dest="product_type", choices=PRODUCT_TYPES, help=argparse.SUPPRESS)
    s_init.add_argument("--progression")
    s_init.add_argument("--shared-canon-json")
    s_init.add_argument("--created-by", default="human")
    s_init.add_argument("--no-first-book", action="store_true", help="Create only the manifest; add every volume later with 'series add-book'.")
    series_sub.add_parser("list", help="List series.")
    for name in ("status",):
        item = series_sub.add_parser(name)
        item.add_argument("series_id")
    s_add = series_sub.add_parser("add-book", help="Create the planned volume at a position as its own project and link it.")
    s_add.add_argument("series_id")
    s_add.add_argument("--position", type=int, required=True)
    s_add.add_argument("--project-id")
    s_add.add_argument("--formats")
    s_add.add_argument("--audience", choices=AUDIENCE_BANDS)
    s_add.add_argument("--product-type", choices=PRODUCT_TYPES, dest="product_type", help="Product family for this volume.")
    s_add.add_argument("--book-type", dest="product_type", choices=PRODUCT_TYPES, help=argparse.SUPPRESS)
    s_add.add_argument("--created-by", default="human")
    s_link = series_sub.add_parser("link", help="Attach an already-existing project to a planned series slot.")
    s_link.add_argument("series_id")
    s_link.add_argument("--position", type=int, required=True)
    s_link.add_argument("--project-id", required=True)
    s_link.add_argument("--created-by", default="human")
    s_context = series_sub.add_parser("context", help="Read-only sibling context for a volume (what earlier volumes cover, shared canon).")
    s_context.add_argument("project_id")
    s_milestone = series_sub.add_parser("milestone", help="Report whether every volume in the set has reached a target lifecycle state.")
    s_milestone.add_argument("series_id")
    s_milestone.add_argument("--target-state", default="PUBLISHED")
    s_recommend = series_sub.add_parser("recommend", help="Read-only: the single next actionable volume for the set (create next, or advance the lowest created volume).")
    s_recommend.add_argument("series_id")
    s_recommend.add_argument("--target-state", default="PUBLISHED")
    s_suggest = series_sub.add_parser("suggest-from-research", help="Read-only: propose series plans from a category's research backlog. Suggests only; creates and promotes nothing.")
    s_suggest.add_argument("category")

    event = sub.add_parser("event", help="Read project event history.")
    event_sub = event.add_subparsers(dest="event_command", required=True)
    e_tail = event_sub.add_parser("tail")
    e_tail.add_argument("project_id")
    e_tail.add_argument("--limit", type=int, default=20)

    artifact = sub.add_parser("artifact", help="Artifact registry.")
    artifact_sub = artifact.add_subparsers(dest="artifact_command", required=True)
    a_list = artifact_sub.add_parser("list")
    a_list.add_argument("project_id")
    a_register = artifact_sub.add_parser("register")
    a_register.add_argument("project_id")
    a_register.add_argument("path")
    a_register.add_argument("--type", required=True, dest="artifact_type")
    a_register.add_argument("--stage", required=True)
    a_register.add_argument("--actor", required=True)
    a_register.add_argument("--rights-status", default="pending")
    a_register.add_argument("--validation-status", default="not-run")
    a_register.add_argument("--source-artifact-id", action="append", default=[])
    a_register.add_argument("--provenance-json")
    a_register.add_argument("--inactive", action="store_true")
    a_freeze = artifact_sub.add_parser("freeze")
    a_freeze.add_argument("project_id")
    a_freeze.add_argument("--artifact", action="append", required=True)
    a_freeze.add_argument("--actor", required=True)

    approval = sub.add_parser("approval", help="Human approval and release authorization.")
    approval_sub = approval.add_subparsers(dest="approval_command", required=True)
    ap_packet = approval_sub.add_parser("packet", help="Assemble an approval gate packet (prepares only; grants nothing).")
    ap_packet.add_argument("project_id")
    ap_packet.add_argument("--gate", required=True, choices=["niche", "interior", "cover", "compliance", "listing", "release"])
    ap_list = approval_sub.add_parser("list")
    ap_list.add_argument("project_id")
    ap_grant = approval_sub.add_parser("grant")
    ap_grant.add_argument("project_id")
    ap_grant.add_argument("--gate", required=True, choices=["niche", "interior", "cover", "compliance", "listing"])
    ap_grant.add_argument("--approver", required=True)
    ap_grant.add_argument("--approver-role", default="publisher")
    ap_grant.add_argument("--artifact", action="append", required=True)
    ap_grant.add_argument("--scope", required=True)
    ap_grant.add_argument("--decision", choices=["APPROVED", "REJECTED"], default="APPROVED")
    ap_grant.add_argument("--exclusion", action="append", default=[])
    ap_grant.add_argument("--notes", default="")
    ap_grant.add_argument("--expires-at")
    ap_release = approval_sub.add_parser("release-authorize")
    ap_release.add_argument("project_id")
    ap_release.add_argument("--approver", action="append", required=True)
    ap_release.add_argument("--channel", action="append", required=True)
    ap_release.add_argument("--product", action="append", required=True)
    ap_release.add_argument("--territory", action="append", required=True)
    ap_release.add_argument("--artifact", action="append", required=True)
    ap_release.add_argument("--operation", action="append", default=["submit"])
    ap_release.add_argument("--maximum-external-spend", type=float, default=0.0)
    ap_release.add_argument("--currency", default="USD")
    ap_release.add_argument("--expires-at")
    ap_release.add_argument("--pricing-json")
    ap_auth_list = approval_sub.add_parser("release-list")
    ap_auth_list.add_argument("project_id")
    ap_verify = approval_sub.add_parser("release-verify")
    ap_verify.add_argument("project_id")
    ap_verify.add_argument("--channel")
    ap_verify.add_argument("--operation")
    ap_verify.add_argument("--hash", action="append", default=[])

    quality = sub.add_parser("quality", help="Quality-gate evaluation.")
    quality_sub = quality.add_subparsers(dest="quality_command", required=True)
    q_eval = quality_sub.add_parser("evaluate")
    q_eval.add_argument("project_id")
    q_eval.add_argument("--stage", default="current")

    rights = sub.add_parser("rights", help="Rights ledger and gate.")
    rights_sub = rights.add_subparsers(dest="rights_command", required=True)
    r_check = rights_sub.add_parser("check")
    r_check.add_argument("project_id")
    r_add = rights_sub.add_parser("add")
    r_add.add_argument("project_id")
    r_add.add_argument("--record-json", required=True, help="JSON string or file path.")

    # Content generation: code produces the puzzle/journal/printable content.
    generate = sub.add_parser("generate", help="Generate deterministic content (puzzles, journal pages, printables).")
    generate.add_argument("project_id")
    generate.add_argument("--type", required=True, dest="content_type", help="Content type key (e.g. sudoku, wordsearch, maze, tracker).")
    generate.add_argument("--count", type=int, default=1)
    generate.add_argument("--difficulty", default="mixed")
    generate.add_argument("--seed", type=int, help="Deterministic seed; defaults to a project-derived seed.")
    generate.add_argument("--params-json", help="Extra generator params as JSON string or file path.")
    generate.add_argument("--actor", default="content-generator")

    # Independent verification: code checks what code produced.
    verify = sub.add_parser("verify", help="Independently verify generated content (uniqueness, solvability, answer keys).")
    verify.add_argument("project_id")
    verify.add_argument("--type", dest="content_type", help="Restrict to one content type; default all.")

    audit = sub.add_parser("audit", help="Run deterministic content and production audits.")
    audit_sub = audit.add_subparsers(dest="audit_command", required=True)
    for name in ("metadata", "accessibility"):
        item = audit_sub.add_parser(name)
        item.add_argument("project_id")

    build = sub.add_parser("build", help="Build print-ready and digital deliverables.")
    build_sub = build.add_subparsers(dest="build_command", required=True)
    b_interior = build_sub.add_parser("interior", help="Assemble the print interior PDF (even pages, back-only solutions).")
    b_interior.add_argument("project_id")
    b_interior.add_argument("--binding", choices=["paperback", "hardcover"], default="paperback")
    b_cover = build_sub.add_parser("cover", help="Build the print cover wrap (spine width from page count and paper).")
    b_cover.add_argument("project_id")
    b_cover.add_argument("--binding", choices=["paperback", "hardcover"], default="paperback")
    b_digital = build_sub.add_parser("digital", help="Assemble a digital printable bundle (PDF + linked pages).")
    b_digital.add_argument("project_id")
    b_proof = build_sub.add_parser("proof", help="Produce a pre-flight proof report for the built interior/cover.")
    b_proof.add_argument("project_id")

    package = sub.add_parser("package", help="Prepare a sales-channel package.")
    package.add_argument("project_id")
    package.add_argument("--channel", required=True, choices=["kdp", "etsy", "gumroad", "generic"])

    submission = sub.add_parser("submission", help="Dry-run or record external human/platform activity.")
    submission_sub = submission.add_subparsers(dest="submission_command", required=True)
    s_dry = submission_sub.add_parser("dry-run")
    s_dry.add_argument("project_id")
    s_dry.add_argument("--channel", required=True)
    s_dry.add_argument("--actor", required=True)
    s_record = submission_sub.add_parser("record")
    s_record.add_argument("project_id")
    s_record.add_argument("--channel", required=True)
    s_record.add_argument("--evidence", required=True)
    s_record.add_argument("--external-id")
    s_record.add_argument("--status", required=True, choices=["submitted", "accepted", "published", "rejected", "withdrawn", "unknown"])
    s_record.add_argument("--actor", required=True)

    niche = sub.add_parser("niche", help="Deterministic niche/market assessment for a topic + product type.")
    niche.add_argument("project_id")

    catalog = sub.add_parser("catalog", help="Catalogue maintenance.")
    catalog_sub = catalog.add_subparsers(dest="catalog_command", required=True)
    catalog_sub.add_parser("rebuild", help="Regenerate both products.json and series.json.")
    catalog_sub.add_parser("verify", help="Read-only: assert product<->series cross-links resolve both ways.")

    marketing = sub.add_parser("marketing", help="Prepare marketing/listing guidance and assets (offline; no external writes).")
    marketing_sub = marketing.add_subparsers(dest="marketing_command", required=True)
    m_guide = marketing_sub.add_parser("guide", help="Per-platform upload and launch step guides.")
    m_guide.add_argument("project_id")
    m_listing = marketing_sub.add_parser("listing", help="Listing copy kit (title, subtitle, description, keywords, categories).")
    m_listing.add_argument("project_id")
    m_kit = marketing_sub.add_parser("kit", help="Prepare the full marketing kit (guide + listing).")
    m_kit.add_argument("project_id")

    return parser


def _dispatch_project(args: argparse.Namespace, root: Path) -> Any:
    if args.project_command == "init":
        return init_project(root, args.topic, args.audience, args.product_type, args.formats, args.project_id, args.language, args.working_title, args.created_by)
    if args.project_command == "list":
        return list_projects(root)
    if args.project_command == "status":
        return project_status(root, args.project_id)
    if args.project_command == "validate":
        return validate_project(root, args.project_id)
    if args.project_command == "next":
        return next_actions(root, args.project_id)
    if args.project_command in ("plan", "recommend"):
        return plan_next(root, args.project_id)
    if args.project_command == "transition":
        return transition(root, args.project_id, args.to, args.actor, args.reason)
    raise RuntimeError("Unhandled project command")


def _dispatch_series(args: argparse.Namespace, root: Path) -> Any:
    if args.series_command == "init":
        books = _load_json_argument(args.books_json, [])
        return init_series(root, args.title, args.premise, books, args.audience, args.language, args.series_id, args.product_type, args.progression, _load_json_argument(args.shared_canon_json, {}) or None, args.created_by, not args.no_first_book)
    if args.series_command == "list":
        return list_series(root)
    if args.series_command == "status":
        return series_status(root, args.series_id)
    if args.series_command == "add-book":
        return add_book(root, args.series_id, args.position, args.project_id, args.formats, args.audience, args.product_type, args.created_by)
    if args.series_command == "link":
        return link_book(root, args.series_id, args.position, args.project_id, args.created_by)
    if args.series_command == "context":
        return sibling_context(root, args.project_id)
    if args.series_command == "milestone":
        return series_milestone(root, args.series_id, args.target_state)
    if args.series_command == "recommend":
        return series_recommend(root, args.series_id, args.target_state)
    if args.series_command == "suggest-from-research":
        return suggest_series_from_research(root, args.category)
    raise RuntimeError("Unhandled series command")


def _dispatch_artifact(args: argparse.Namespace, root: Path) -> Any:
    if args.artifact_command == "list":
        return list_artifacts(root, args.project_id)
    if args.artifact_command == "register":
        return register_artifact(root, args.project_id, args.path, args.artifact_type, args.stage, args.actor, args.rights_status, args.validation_status, args.source_artifact_id, _load_json_argument(args.provenance_json, {}), not args.inactive)
    if args.artifact_command == "freeze":
        from .artifacts import resolve_hash
        hashes = [resolve_hash(root, args.project_id, value) for value in args.artifact]
        return freeze_artifacts(root, args.project_id, hashes, args.actor)
    raise RuntimeError("Unhandled artifact command")


def _dispatch_approval(args: argparse.Namespace, root: Path) -> Any:
    if args.approval_command == "packet":
        return build_gate_packet(root, args.project_id, args.gate)
    if args.approval_command == "list":
        return list_approvals(root, args.project_id)
    if args.approval_command == "grant":
        return grant_approval(root, args.project_id, args.gate, args.approver, args.approver_role, args.artifact, args.scope, args.decision, args.exclusion, args.notes, args.expires_at)
    if args.approval_command == "release-authorize":
        return create_release_authorization(root, args.project_id, args.approver, args.channel, args.product, args.territory, args.artifact, args.operation, args.maximum_external_spend, args.currency, args.expires_at, _load_json_argument(args.pricing_json, {}))
    if args.approval_command == "release-list":
        return release_authorizations(root, args.project_id)
    if args.approval_command == "release-verify":
        return verify_release_authorization(root, args.project_id, args.channel, args.operation, args.hash or None)
    raise RuntimeError("Unhandled approval command")


def _dispatch_build(args: argparse.Namespace, root: Path) -> Any:
    if args.build_command == "interior":
        return build_interior(root, args.project_id, args.binding)
    if args.build_command == "cover":
        return build_cover(root, args.project_id, args.binding)
    if args.build_command == "digital":
        return link_digital_bundle(root, args.project_id)
    if args.build_command == "proof":
        return build_proof(root, args.project_id)
    raise RuntimeError("Unhandled build command")


def _dispatch_fetch(args: argparse.Namespace, root: Path) -> Any:
    # The enable flag is the single gate for network egress in net.fetch. Setting
    # it here (from --allow-net) keeps every network decision at the CLI boundary.
    import os as _os

    if getattr(args, "allow_net", False):
        _os.environ["RESEARCH_FETCH_ENABLED"] = "1"
    from .net import fetch as _fetch  # imported lazily: the ONLY network module

    use_cache = not getattr(args, "no_cache", False)
    if args.fetch_command == "search":
        return _fetch.search(args.query, engine=args.engine, max_results=args.max_results, root=root, use_cache=use_cache)
    if args.fetch_command == "get":
        return _fetch.get_to_cache(args.url, root=root, use_cache=use_cache)
    if args.fetch_command == "probe":
        return _fetch.probe(args.source_id, root=root)
    raise RuntimeError("Unhandled fetch command")


def _dispatch_research(args: argparse.Namespace, root: Path) -> Any:
    from . import research as _research  # offline; no network

    if args.research_command == "init":
        return _research.init_research(root, args.category)
    if args.research_command == "validate":
        return _research.validate_research(root, args.category)
    if args.research_command == "pipeline-add":
        entry = _load_json_argument(_read_stdin_if_dash(args.json), {})
        return _research.pipeline_add(root, args.category, entry)
    if args.research_command == "promote":
        return _research.promote(root, args.category, args.product_id, args.project_id)
    if args.research_command == "show":
        return _research.show_research(root, args.category, args.product_id)
    if args.research_command == "log":
        detail = _load_json_argument(_read_stdin_if_dash(args.detail_json), {}) if args.detail_json else {}
        return _research.log_event(root, args.category, args.event, detail)
    raise RuntimeError("Unhandled research command")


def dispatch(args: argparse.Namespace, root: Path) -> Any:
    if args.command == "doctor":
        if getattr(args, "probe_plan", False):
            from .connectivity import probe_plan
            return probe_plan(root)
        return run_doctor(root)
    if args.command == "connectivity":
        from .connectivity import show_manifest, write_manifest
        if args.connectivity_command == "show":
            return show_manifest(root)
        return write_manifest(root, _load_json_argument(_read_stdin_if_dash(args.json), {}))
    if args.command == "fetch":
        return _dispatch_fetch(args, root)
    if args.command == "research":
        return _dispatch_research(args, root)
    if args.command == "framework":
        return validate_framework(root)
    if args.command == "project":
        return _dispatch_project(args, root)
    if args.command == "series":
        return _dispatch_series(args, root)
    if args.command == "event":
        from .paths import ProjectPaths
        paths = ProjectPaths(root, args.project_id).require()
        return read_events(paths.events, args.limit)
    if args.command == "artifact":
        return _dispatch_artifact(args, root)
    if args.command == "approval":
        return _dispatch_approval(args, root)
    if args.command == "quality":
        return evaluate_quality(root, args.project_id, args.stage)
    if args.command == "rights":
        if args.rights_command == "check":
            return check_rights(root, args.project_id)
        return add_rights_record(root, args.project_id, _load_json_argument(args.record_json, {}))
    if args.command == "generate":
        return generate_content(root, args.project_id, args.content_type, args.count, args.difficulty, args.seed, _load_json_argument(args.params_json, {}), args.actor)
    if args.command == "verify":
        return verify_content(root, args.project_id, args.content_type)
    if args.command == "audit":
        if args.audit_command == "metadata":
            return audit_metadata(root, args.project_id)
        if args.audit_command == "accessibility":
            return audit_accessibility(root, args.project_id)
    if args.command == "build":
        return _dispatch_build(args, root)
    if args.command == "package":
        return package_channel(root, args.project_id, args.channel)
    if args.command == "submission":
        if args.submission_command == "dry-run":
            return create_dry_run(root, args.project_id, args.channel, args.actor)
        return record_submission(root, args.project_id, args.channel, args.evidence, args.external_id, args.status, args.actor)
    if args.command == "niche":
        return assess_niche(root, args.project_id)
    if args.command == "catalog":
        if args.catalog_command == "verify":
            return verify_catalog(root)
        return rebuild_catalog(root)
    if args.command == "marketing":
        if args.marketing_command == "guide":
            return build_launch_guide(root, args.project_id)
        if args.marketing_command == "listing":
            return build_listing_kit(root, args.project_id)
        if args.marketing_command == "kit":
            return build_marketing_kit(root, args.project_id)
    raise RuntimeError("Unhandled command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).expanduser().resolve() if args.root else repo_root()
        result = dispatch(args, root)
        if args.compact:
            print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        else:
            _json(result)
        if isinstance(result, dict):
            if result.get("valid") is False or result.get("status") == "fail":
                return 1
        return 0
    except (PublishingHouseError, FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "error_type": type(exc).__name__}, indent=2), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"status": "error", "error": "Interrupted"}), file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
