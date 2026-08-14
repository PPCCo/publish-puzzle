"""Deterministic human-approval-gate packet assembler.

``build_gate_packet`` gathers everything a human needs to decide a gate --- exact
artifact hashes, scope, risks, open findings, deterministic gate evidence, and the
available decision options --- and writes it to
``approvals/packets/gate-packet-<gate>-latest.json`` (a subdirectory that
``approvals.list_approvals`` does NOT glob, so a packet can never be mistaken for
an approval record).

It PREPARES a packet only. It NEVER grants, freezes, authorizes, or transitions.
Recording approval remains the exclusive job of the human-only ``/book-approve-*``,
``/book-freeze``, and ``/book-release-authorize`` skills.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .approvals import approval_is_current, list_approvals
from .artifacts import list_artifacts
from .errors import PublishingHouseError
from .events import read_events
from .paths import ProjectPaths
from .state import required_gate, workflow_config
from .util import atomic_write_json, load_company_config, load_json, load_yaml, utc_now

GATES = ("niche", "interior", "cover", "compliance", "listing", "release")

# Which deterministic gate reports are material evidence for each human gate.
_GATE_EVIDENCE: dict[str, list[str]] = {
    "niche": ["niche/assessment-latest.json"],
    # Interior gate binds the FROZEN SOURCE only. The interior PDF + proof are
    # built after this gate freezes the source (LAYOUT_AND_FORMAT_BUILD), so the
    # proof report is intentionally NOT material evidence here — it does not exist yet.
    "interior": [
        "verification/content-verification-latest.json",
        "reviews/quality-gate-latest.json",
    ],
    "cover": ["outputs/proof/cover-proof-report.json"],
    "compliance": [
        "rights/gate-latest.json",
        "accessibility/gate-latest.json",
    ],
    "listing": ["metadata/validation-report.json"],
    "release": [],
}

# Which active-artifact TYPES each human gate binds its approval to. A type NOT
# listed here is intentionally excluded so re-registering a DIFFERENT artifact type
# later (e.g. rebuilding the interior/cover PDF or a channel package) cannot
# invalidate this gate's approval. Interior/cover bind to the SOURCE content/design
# artifacts, explicitly NOT to the *-pdf downstream build outputs.
# ``None`` means "bind every active artifact" (release binds channel-package hashes
# through its own logic, so its scoping is unchanged).
_GATE_ARTIFACT_TYPES: dict[str, list[str] | None] = {
    "niche": ["niche-assessment", "product-brief"],
    "interior": ["content-sudoku", "content-verification", "content-plan"],
    "cover": ["cover-art-direction"],
    "compliance": ["rights-ledger", "rights-gate", "accessibility-gate"],
    "listing": ["metadata", "metadata-validation", "listing-kit"],
    "release": None,
}

# The state a project must be sitting in for each human gate.
_GATE_STATE = {
    "niche": "NICHE_APPROVAL",
    "interior": "INTERIOR_APPROVAL",
    "cover": "COVER_APPROVAL",
    "compliance": "COMPLIANCE_APPROVAL",
    "listing": "LISTING_APPROVAL",
    "release": "RELEASE_AUTHORIZATION",
}

_GATE_SKILL = {
    "niche": "/product-approve-niche",
    "interior": "/product-approve-interior",
    "cover": "/product-approve-cover",
    "compliance": "/product-approve-compliance",
    "listing": "/product-approve-listing",
    "release": "/product-release-authorize",
}


def _report_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"present": False, "decision": None}
    try:
        data = load_json(path)
    except Exception:  # noqa: BLE001
        return {"present": True, "decision": "INVALID"}
    decision = str(data.get("decision") or data.get("status") or "").upper() or None
    return {"present": True, "decision": decision}


def _open_findings(paths: ProjectPaths) -> dict[str, Any]:
    counts = {"blocker": 0, "major": 0, "minor": 0, "note": 0}
    items: list[dict[str, Any]] = []
    for path in sorted(paths.directory.glob("reviews/**/*.json")):
        if path.name in {"index.json", "quality-gate-latest.json"}:
            continue
        try:
            data = load_json(path)
        except Exception:  # noqa: BLE001
            continue
        for finding in data.get("findings", []):
            if finding.get("status") in {"closed", "rejected-with-rationale"}:
                continue
            severity = finding.get("severity", "note")
            if severity in counts:
                counts[severity] += 1
            if severity in {"blocker", "major"}:
                items.append(
                    {
                        "severity": severity,
                        "location": finding.get("location", ""),
                        "summary": finding.get("summary") or finding.get("recommendation", ""),
                        "source": path.relative_to(paths.directory).as_posix(),
                    }
                )
    return {"counts": counts, "open_blocker_or_major": sorted(items, key=lambda i: (i["severity"], i["source"]))}


def _series_context(root: Path, project_id: str, project: dict[str, Any]) -> dict[str, Any] | None:
    """Read-only series/sibling summary for the packet, or None for standalone books.

    Enriches each prior sibling with its current workflow state so a human can see
    whether the books this one builds on are themselves settled. Failures degrade
    gracefully to a partial record rather than blocking packet assembly.
    """
    if not project.get("series"):
        return None
    try:
        from .series import sibling_context

        context = sibling_context(root, project_id)
    except Exception as exc:  # noqa: BLE001
        link = project.get("series", {})
        return {"in_series": True, "series_id": link.get("series_id"), "error": str(exc)}
    if not context.get("in_series"):
        return None
    for prior in context.get("covers_earlier", []):
        prior_id = prior.get("project_id")
        prior["state"] = None
        prior["content_frozen"] = None
        if not prior_id:
            continue
        try:
            sibling_paths = ProjectPaths(root, prior_id)
            if sibling_paths.state.is_file():
                sibling_state = load_json(sibling_paths.state)
                current = str(sibling_state.get("current_state"))
                prior["state"] = current
                # A sibling is "settled enough" to build on once its interior
                # content has passed the interior approval gate (content locked).
                settled = {
                    "INTERIOR_APPROVAL", "VISUAL_DEVELOPMENT", "COVER_APPROVAL",
                    "LAYOUT_AND_FORMAT_BUILD", "ACCESSIBILITY_VALIDATION",
                    "RIGHTS_CLEARANCE", "COMPLIANCE_APPROVAL",
                    "METADATA_AND_COMMERCIAL_PACKAGE", "LISTING_APPROVAL",
                    "FINAL_PROOF", "PLATFORM_PACKAGING", "RELEASE_AUTHORIZATION",
                    "READY_FOR_SUBMISSION", "SUBMISSION", "PUBLISHED",
                    "MONITORING", "EDITION_MAINTENANCE",
                }
                prior["content_frozen"] = current in settled
        except Exception:  # noqa: BLE001
            continue
    return context


def build_gate_packet(root: Path, project_id: str, gate: str) -> dict[str, Any]:
    """Assemble and persist an approval packet for ``gate``. Does NOT grant."""
    if gate not in GATES:
        raise PublishingHouseError(f"Unknown gate: {gate}. Expected one of {', '.join(GATES)}.")

    paths = ProjectPaths(root, project_id).require()
    state = load_json(paths.state)
    project = load_yaml(paths.config, default={}) or {}
    company = load_company_config(root)
    current_state = str(state.get("current_state"))
    expected_state = _GATE_STATE[gate]

    # Exact active-artifact hashes under review.
    active = dict(state.get("active_artifacts", {}))
    manifest = {item.get("sha256"): item for item in list_artifacts(root, project_id)}
    # ``artifacts_under_review`` is scoped to this gate's binding TYPES (see
    # _GATE_ARTIFACT_TYPES) so the approval it produces is NOT bound to unrelated
    # downstream build outputs. ``all_artifact_paths`` keeps EVERY active artifact's
    # path for human visibility (review_files) even when it is not bound.
    allowed_types = _GATE_ARTIFACT_TYPES.get(gate)
    artifacts_under_review = []
    all_artifact_paths: list[str] = []
    for kind, digest in sorted(active.items()):
        entry = manifest.get(digest, {})
        if entry.get("path"):
            all_artifact_paths.append(entry["path"])
        if allowed_types is not None and entry.get("type") not in allowed_types:
            # Not material to THIS gate's approval; visible above but not bound.
            continue
        artifacts_under_review.append(
            {
                "kind": kind,
                "sha256": digest,
                "type": entry.get("type"),
                "path": entry.get("path"),
                "frozen": entry.get("frozen", False),
                "rights_status": entry.get("rights_status"),
                "validation_status": entry.get("validation_status"),
                "registered": bool(entry),
            }
        )

    # Deterministic gate evidence relevant to this gate.
    evidence = []
    for rel in _GATE_EVIDENCE.get(gate, []):
        summary = _report_summary(paths.directory / rel)
        summary["report"] = rel
        summary["is_pass"] = summary.get("decision") == "PASS"
        evidence.append(summary)

    # For the release gate: per-channel package manifest hashes.
    channel_packages = []
    if gate == "release":
        for channel in sorted(project.get("sales_channels", [])):
            mpath = paths.directory / "outputs" / "packages" / channel / "package-manifest.json"
            summary = _report_summary(mpath)
            summary["channel"] = channel
            summary["report"] = mpath.relative_to(paths.directory).as_posix()
            channel_packages.append(summary)

    findings = _open_findings(paths)

    # Series context: if this book belongs to a set, surface (read-only) where it
    # sits, what earlier books cover, and the shared canon, so a human is not
    # approving a set member blind to its siblings. Never fetched from or written
    # to a sibling project beyond its manifest slot; grants nothing.
    series_context = _series_context(root, project_id, project)

    # Existing approvals: current vs invalidated for this gate.
    all_approvals = list_approvals(root, project_id)
    gate_approvals = [a for a in all_approvals if a.get("gate") == gate]
    current_approvers = sorted(
        {a.get("approver") for a in gate_approvals if approval_is_current(a) and a.get("approver")}
    )
    invalidated = [
        {"approval_id": a.get("approval_id"), "approver": a.get("approver"), "reason": a.get("invalidation_reason")}
        for a in gate_approvals
        if a.get("invalidated_at")
    ]
    required_approvers = int(company.get("human_gates", {}).get(gate, 1))

    # Risks: assemble from state divergence, missing evidence, and open findings.
    risks: list[str] = []
    if current_state != expected_state:
        risks.append(
            f"Project state is {current_state}, not {expected_state}; this gate is not the current forward step."
        )
    for ev in evidence:
        if not ev.get("is_pass"):
            risks.append(f"Deterministic evidence not PASS: {ev['report']} = {ev.get('decision')}")
    for pkg in channel_packages:
        if pkg.get("decision") not in {"PASS", "WARNING"}:
            risks.append(f"Channel package missing/failed: {pkg.get('channel')} = {pkg.get('decision')}")
    if findings["counts"]["blocker"]:
        risks.append(f"{findings['counts']['blocker']} open blocker finding(s)")
    if findings["counts"]["major"]:
        risks.append(f"{findings['counts']['major']} open major finding(s)")
    if not artifacts_under_review:
        risks.append("No active artifacts recorded to bind the approval to.")
    unregistered = [a["kind"] for a in artifacts_under_review if not a["registered"]]
    if unregistered:
        risks.append(f"Active artifacts not in the registry: {', '.join(unregistered)}")
    for a in artifacts_under_review:
        if a["sha256"] is None:
            risks.append(f"Active artifact '{a['kind']}' has no hash.")
    # Series continuity: at gates where this book's content depends on earlier
    # books being settled, warn (do NOT block) if a prior sibling is not yet
    # content-frozen — the material this book assumes could still shift.
    continuity_gates = {"interior", "compliance", "listing", "release"}
    if series_context and series_context.get("in_series") and gate in continuity_gates:
        unsettled = [
            f"{p.get('working_title') or p.get('project_id')} ({p.get('state') or 'unknown'})"
            for p in series_context.get("covers_earlier", [])
            if p.get("content_frozen") is False
        ]
        if unsettled:
            risks.append(
                "Series continuity: earlier book(s) this one builds on are not yet "
                f"content-frozen: {', '.join(unsettled)}. Assumed material may still change."
            )

    ready_for_human = not risks

    # review_files: the concrete, project-root-relative files a human should open to
    # decide this gate. Assembled only from data already computed above; deduped in
    # first-seen order; restricted to paths that actually exist on disk. Set to None
    # (JSON null) when nothing applies, so consumers can branch cleanly.
    packet_rel = (paths.directory / "approvals" / "packets" / f"gate-packet-{gate}-latest.json").relative_to(
        paths.directory
    ).as_posix()
    # review_files lists ALL built outputs (all_artifact_paths) for human visibility;
    # the approval BINDING is scoped to the gate's source types via _GATE_ARTIFACT_TYPES,
    # so a human still sees the built interior/cover PDF even though the approval is not
    # bound to its hash.
    candidate_review_files: list[str] = []
    candidate_review_files.extend(all_artifact_paths)
    candidate_review_files.extend(ev["report"] for ev in evidence if ev.get("report"))
    candidate_review_files.extend(pkg["report"] for pkg in channel_packages if pkg.get("report"))
    candidate_review_files.append(packet_rel)
    review_files: list[str] = []
    for rel in candidate_review_files:
        if rel in review_files:
            continue
        if (paths.directory / rel).exists():
            review_files.append(rel)

    # next_command: the single next step for the human, copy-paste runnable. Approvals
    # are recorded through Claude skills (a slash command), not a shell call, so the
    # form is "slash" for all six gates; the "shell" form (a `!`-prefixed command) is
    # reserved for future non-approval steps. When the gate is not yet ready, the
    # command still points at the recording skill but the description names the top
    # blocker(s) so the packet always states the real next action.
    recording_skill = _GATE_SKILL[gate]
    if ready_for_human:
        if gate == "release":
            next_description = "Authorize release (submission preparation only), or reject."
        else:
            next_description = f"Approve the {gate} gate, or reject."
    else:
        top = "; ".join(risks[:3])
        next_description = f"Resolve blockers before deciding the {gate} gate: {top}"
    next_command = {
        "form": "slash",
        "command": f"{recording_skill} {project_id}",
        "description": next_description,
        "ready": ready_for_human,
    }

    packet = {
        "schema_version": "1.0",
        "kind": "approval-gate-packet",
        "project_id": project_id,
        "gate": gate,
        "generated_at": utc_now(),
        "prepared_by": "publishing_house.gate_packet (deterministic; grants nothing)",
        "current_state": current_state,
        "expected_state": expected_state,
        "state_matches_gate": current_state == expected_state,
        "scope": {
            "working_title": project.get("working_title") or project.get("title"),
            "audience": project.get("audience"),
            "book_type": project.get("book_type"),
            "formats": project.get("formats", []),
            "sales_channels": project.get("sales_channels", []),
            "territory": project.get("territory"),
        },
        "artifacts_under_review": artifacts_under_review,
        "deterministic_evidence": evidence,
        "channel_packages": channel_packages,
        "series_context": series_context,
        "open_findings": findings,
        "existing_approvals": {
            "required_distinct_approvers": required_approvers,
            "current_distinct_approvers": current_approvers,
            "current_count": len(current_approvers),
            "approvers_still_needed": max(0, required_approvers - len(current_approvers)),
            "invalidated": invalidated,
        },
        "risks": risks,
        "ready_for_human_review": ready_for_human,
        "decision_options": ["APPROVE", "REJECT", "REQUEST_CHANGES"],
        "human_action": {
            "recording_skill": _GATE_SKILL[gate],
            "note": (
                "This packet grants nothing. A human must DECIDE this gate — either "
                "interactively in-session (the assistant presents the options and records the "
                f"choice) or by invoking {_GATE_SKILL[gate]} — bound to the exact artifact hashes "
                "listed above. Autonomy must STOP here until the human decides."
            ),
            "artifact_hashes_to_bind": [a["sha256"] for a in artifacts_under_review if a["sha256"]],
            "next_command": next_command,
            "review_files": review_files or None,
        },
        "audit": {
            "recent_events": read_events(paths.events, limit=5),
        },
    }

    # Guard: this state must actually gate here (defensive, informational only).
    packet["gate_is_required_transition"] = any(
        required_gate(root, current_state, t) == gate
        for t in workflow_config(root).get("transitions", {}).get(current_state, [])
    )

    out = paths.directory / "approvals" / "packets" / f"gate-packet-{gate}-latest.json"
    atomic_write_json(out, packet)
    packet["packet_path"] = out.relative_to(paths.directory).as_posix()
    return packet
