from pathlib import Path
from typing import Any

from .project import sync_catalog


def rebuild_catalog(root: Path) -> dict[str, Any]:
    return sync_catalog(root)
