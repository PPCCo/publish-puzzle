#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install MCP support with: python -m pip install -e '.[mcp]'") from exc

from publishing_house.artifacts import list_artifacts
from publishing_house.doctor import run_doctor
from publishing_house.generate import generate_content
from publishing_house.packages import package_channel
from publishing_house.project import list_projects, project_status, validate_project
from publishing_house.quality import evaluate_quality
from publishing_house.rights import check_rights
from publishing_house.state import next_actions
from publishing_house.submission import create_dry_run
from publishing_house.util import repo_root
from publishing_house.validation import validate_framework
from publishing_house.verify import verify_content

mcp = FastMCP("publishing-house")


def root() -> Path:
    return repo_root()


@mcp.tool()
def framework_doctor() -> dict[str, Any]:
    '''Check the local publishing framework and optional production tools without making changes.'''
    return run_doctor(root())


@mcp.tool()
def framework_validate() -> dict[str, Any]:
    '''Validate Claude Code agents, skills, workflows, settings, schemas, and local contracts.'''
    return validate_framework(root())


@mcp.tool()
def projects_list() -> list[dict[str, Any]]:
    '''List product projects (puzzle/coloring/journal/printable) and their current states.'''
    return list_projects(root())


@mcp.tool()
def project_get_status(project_id: str) -> dict[str, Any]:
    '''Return project configuration, state, approvals, artifacts, and latest events.'''
    return project_status(root(), project_id)


@mcp.tool()
def project_validate(project_id: str) -> dict[str, Any]:
    '''Validate a project without changing it.'''
    return validate_project(root(), project_id)


@mcp.tool()
def project_next_actions(project_id: str) -> dict[str, Any]:
    '''Return allowed next states and any approval or report blockers.'''
    return next_actions(root(), project_id)


@mcp.tool()
def project_artifacts(project_id: str) -> list[dict[str, Any]]:
    '''List registered immutable artifacts and current hashes.'''
    return list_artifacts(root(), project_id)


@mcp.tool()
def content_generate(
    project_id: str,
    content_type: str,
    count: int = 1,
    difficulty: str = "mixed",
    seed: int | None = None,
    actor: str = "content-generator",
) -> dict[str, Any]:
    '''Deterministically generate puzzle/journal/printable content and register it as an artifact.'''
    return generate_content(
        root(),
        project_id,
        content_type,
        count=count,
        difficulty=difficulty,
        seed=seed,
        actor=actor,
    )


@mcp.tool()
def content_verify(project_id: str, content_type: str | None = None) -> dict[str, Any]:
    '''Independently verify generated content by code (uniqueness, solvability, answer keys).'''
    return verify_content(root(), project_id, content_type)


@mcp.tool()
def project_quality_gate(project_id: str, stage: str = "current") -> dict[str, Any]:
    '''Evaluate current structured review files against configured quality thresholds.'''
    return evaluate_quality(root(), project_id, stage)


@mcp.tool()
def project_rights_gate(project_id: str) -> dict[str, Any]:
    '''Evaluate the rights ledger; never infer clearance from missing evidence.'''
    return check_rights(root(), project_id)


@mcp.tool()
def prepare_channel_package(project_id: str, channel: str) -> dict[str, Any]:
    '''Prepare a local KDP, Etsy, Gumroad, or generic package. Performs no network write.'''
    return package_channel(root(), project_id, channel)


@mcp.tool()
def create_submission_dry_run(project_id: str, channel: str, actor: str) -> dict[str, Any]:
    '''Create a local dry-run record for a prepared package. Performs no network write.'''
    return create_dry_run(root(), project_id, channel, actor)


if __name__ == "__main__":
    mcp.run(transport="stdio")
