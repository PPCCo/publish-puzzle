"""Shared contracts and a registry for deterministic content types.

A ``ContentType`` bundles a generator callable and a validator callable under a
key. Generators are pure functions of ``(seed, difficulty, index, params)`` so
the same inputs always produce byte-identical output --- this is what lets the
build and the verifier agree without any shared mutable state. Validators take
ONLY the generated puzzle payload (never the generator's private state) and
re-derive correctness independently.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class GeneratedItem:
    """A single generated content item (one puzzle / page / printable)."""

    content_type: str
    index: int
    difficulty: str
    seed: int
    payload: dict[str, Any]
    solution: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_type": self.content_type,
            "index": self.index,
            "difficulty": self.difficulty,
            "seed": self.seed,
            "payload": self.payload,
            "solution": self.solution,
            "metadata": self.metadata,
        }


@dataclass
class ValidationResult:
    """Outcome of INDEPENDENTLY verifying one generated item."""

    content_type: str
    index: int
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "content_type": self.content_type,
            "index": self.index,
            "passed": self.passed,
            "checks": self.checks,
            "errors": self.errors,
        }


# A generator turns (seed, difficulty, index, params) into one GeneratedItem.
GeneratorFn = Callable[[int, str, int, dict[str, Any]], GeneratedItem]
# A validator re-derives correctness from a serialized item dict alone.
ValidatorFn = Callable[[dict[str, Any]], ValidationResult]


@dataclass(frozen=True)
class ContentType:
    key: str
    family: str  # puzzle | activity | journal | printable | coloring
    label: str
    generate: GeneratorFn
    validate: ValidatorFn
    verifiable: bool = True  # False for open-ended items (journal prompts, art)


class _Registry:
    """Ordered, name-keyed registry of content types."""

    def __init__(self) -> None:
        self._types: dict[str, ContentType] = {}

    def register(self, content_type: ContentType) -> ContentType:
        if content_type.key in self._types:
            raise ValueError(f"Duplicate content type: {content_type.key}")
        self._types[content_type.key] = content_type
        return content_type

    def get(self, key: str) -> ContentType:
        if key not in self._types:
            raise KeyError(
                f"Unknown content type: {key}. Known: {', '.join(sorted(self._types))}"
            )
        return self._types[key]

    def keys(self) -> list[str]:
        return sorted(self._types)

    def all(self) -> list[ContentType]:
        return [self._types[key] for key in sorted(self._types)]


registry = _Registry()


def derive_seed(base_seed: int, content_type: str, index: int) -> int:
    """Deterministically derive a per-item seed from a project-level base seed.

    Uses a stable hash of (base_seed, content_type, index) so two different
    content types drawing from the same project seed never produce correlated
    puzzles, and re-running item N always reproduces the same puzzle.
    """
    material = f"{base_seed}:{content_type}:{index}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big")


# Importing the concrete modules registers their content types as a side effect.
# Kept at the bottom to avoid circular imports (they import from this module).
def _install_builtin_types() -> None:
    from . import (  # noqa: F401
        activity,
        coloring,
        journal,
        logic,
        printable,
        puzzles,
    )


_install_builtin_types()
