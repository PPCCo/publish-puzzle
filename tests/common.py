from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SOURCE_ROOT / ".claude" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from publishing_house.project import init_project  # noqa: E402
from publishing_house.util import atomic_write_json  # noqa: E402


class RepoFixture:
    """A disposable copy of the framework with an empty projects tree."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pub-clr-test-")
        self.root = Path(self._tmp.name)
        shutil.copytree(
            SOURCE_ROOT / ".claude",
            self.root / ".claude",
            # Exclude runtime/local state so a fresh fixture reflects the shipped
            # tree, never the developer's machine: caches, logs, and the
            # gitignored local overrides (e.g. tools.local.json image_generation
            # mode:auto, dependencies.local.json extra fonts). Tests assert the
            # committed defaults.
            ignore=shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                "logs",
                "tools.local.json",
                "dependencies.local.json",
                "research-connectivity.json",
            ),
        )
        shutil.copy2(SOURCE_ROOT / ".mcp.json", self.root / ".mcp.json")
        (self.root / "catalog").mkdir(parents=True, exist_ok=True)
        atomic_write_json(
            self.root / "catalog" / "products.json",
            {"schema_version": "1.0", "products": []},
        )
        (self.root / "projects").mkdir(parents=True, exist_ok=True)

    def close(self) -> None:
        self._tmp.cleanup()

    def project(
        self,
        project_id: str = "clr-test-sudoku",
        product_type: str = "puzzle-book",
        audience: str = "senior-large-print",
        formats: list[str] | None = None,
        topic: str = "Sudoku for Seniors",
    ) -> tuple[str, Path]:
        result = init_project(
            self.root,
            topic=topic,
            audience=audience,
            product_type=product_type,
            formats=formats or ["paperback"],
            project_id=project_id,
            language="en-US",
            working_title="Big Sudoku",
            created_by="test-suite",
        )
        pid = result["state"]["project_id"]
        return pid, self.root / "projects" / pid


def create_png(path: Path, width: int = 800, height: int = 1200) -> None:
    """Write a small real PNG for image-gen / compositor tests.

    Draws a grey polygon on white so component-placement assertions have
    non-white pixels to find; 300 DPI matches print-at-home expectations.
    """
    from PIL import Image, ImageDraw

    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.polygon(
        [
            (width // 8, height * 3 // 4),
            (width // 2, height // 5),
            (width * 7 // 8, height * 3 // 4),
        ],
        fill=(165, 165, 165),
        outline=(20, 20, 20),
    )
    draw.text((width // 4, height // 12), "SUDOKU", fill=(10, 10, 10))
    image.save(path, format="PNG", dpi=(300, 300))
