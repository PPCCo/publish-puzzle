"""Deterministic content generators and independent validators.

Every generator produces content from a seed (so a project + type + index always
yields the identical puzzle) and every generator is paired with an INDEPENDENT
validator that re-derives correctness from the puzzle alone --- it never trusts the
generator's own answer key. This "code generates, code verifies" split is the
core integrity guarantee of the puzzle/activity product family.

The registry maps a content-type key (e.g. ``sudoku``) to a ``ContentType``
bundling its generator and validator. ``generate.py`` and ``verify.py`` are thin
orchestration layers over this registry; the CLI never imports individual
generators directly.
"""
from __future__ import annotations

from .base import ContentType, GeneratedItem, ValidationResult, registry

__all__ = ["ContentType", "GeneratedItem", "ValidationResult", "registry"]
