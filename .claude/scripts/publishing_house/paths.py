from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import ProjectNotFoundError
from .util import ensure_within


# Directory layout for a puzzle / coloring / journal / printable project.
# Every content family writes generated content + solutions/answer-keys under
# ``content/`` and the paired machine-verification reports under
# ``verification/``. ``line-art/`` holds original coloring assets (originals
# only) with their provenance. ``layout/`` holds page-assembly intermediates;
# ``outputs/`` holds built print-ready PDFs, digital bundles, and channel
# packages. Nothing here is book-manuscript specific.
PROJECT_DIRS = [
    "brief",
    "concepts",
    "niche",
    "content/puzzles",
    "content/solutions",
    "content/coloring",
    "content/journal",
    "content/printable",
    "line-art/originals",
    "line-art/briefs",
    "line-art/provenance",
    "visuals/assets",
    "visuals/briefs",
    "verification",
    "reviews",
    "layout",
    "accessibility",
    "rights/evidence",
    "metadata/channels",
    "marketing",
    "approvals",
    "approvals/packets",
    "artifacts",
    "release",
    "outputs/print",
    "outputs/interior",
    "outputs/cover",
    "outputs/digital",
    "outputs/proof",
    "outputs/packages",
    "tmp",
]


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    project_id: str

    @property
    def directory(self) -> Path:
        return self.root / "projects" / self.project_id

    @property
    def config(self) -> Path:
        return self.directory / "project.yaml"

    @property
    def state(self) -> Path:
        return self.directory / "state.json"

    @property
    def events(self) -> Path:
        return self.directory / "events.ndjson"

    @property
    def lock(self) -> Path:
        return self.directory / ".lock"

    @property
    def artifact_manifest(self) -> Path:
        return self.directory / "artifacts" / "manifest.json"

    @property
    def rights_ledger(self) -> Path:
        return self.directory / "rights" / "ledger.json"

    @property
    def reviews_index(self) -> Path:
        return self.directory / "reviews" / "index.json"

    def require(self) -> "ProjectPaths":
        if not self.config.is_file() or not self.state.is_file():
            raise ProjectNotFoundError(f"Project not found: {self.project_id}")
        return self

    def resolve_inside(self, relative_or_absolute: str | Path) -> Path:
        p = Path(relative_or_absolute)
        if not p.is_absolute():
            p = self.directory / p
        return ensure_within(p, self.directory)


@dataclass(frozen=True)
class SeriesPaths:
    root: Path
    series_id: str

    @property
    def directory(self) -> Path:
        return self.root / "series" / self.series_id

    @property
    def manifest(self) -> Path:
        return self.directory / "series.yaml"

    @property
    def plan(self) -> Path:
        return self.directory / "series-plan.md"

    @property
    def events(self) -> Path:
        return self.directory / "events.ndjson"

    @property
    def lock(self) -> Path:
        return self.directory / ".lock"

    def require(self) -> "SeriesPaths":
        if not self.manifest.is_file():
            raise ProjectNotFoundError(f"Series not found: {self.series_id}")
        return self
