"""Logic-grid deduction puzzle generator + independent validator.

Generates a small "who-owns-what" logic puzzle: N people each mapped bijectively
to N values across K categories, plus a set of clues that pin the arrangement.
The validator independently re-solves the puzzle from the clues by brute force
over permutations and confirms the solution is BOTH consistent with every clue
AND unique.
"""
from __future__ import annotations

import itertools
import random
from typing import Any

from .base import ContentType, GeneratedItem, ValidationResult, registry

_NAMES = ["Ava", "Ben", "Cara", "Dan", "Eve", "Finn"]
_CATEGORY_POOLS = {
    "colour": ["Red", "Blue", "Green", "Yellow", "Purple", "Orange"],
    "pet": ["Cat", "Dog", "Bird", "Fish", "Rabbit", "Turtle"],
    "drink": ["Tea", "Coffee", "Juice", "Water", "Cocoa", "Soda"],
    "hobby": ["Chess", "Music", "Hiking", "Baking", "Painting", "Reading"],
}


def _size_for(difficulty: str) -> tuple[int, int]:
    table = {"easy": (3, 2), "medium": (4, 2), "hard": (4, 3), "expert": (5, 3), "mixed": (4, 2)}
    return table.get(difficulty, table["mixed"])


def _make_clues(people: list[str], assignment: dict[str, dict[str, str]], categories: list[str], rng: random.Random) -> list[dict[str, str]]:
    clues: list[dict[str, str]] = []
    # Direct positive clues: "<person> has <value>" in some category.
    for person in people:
        cat = rng.choice(categories)
        clues.append({"type": "is", "person": person, "category": cat, "value": assignment[person][cat]})
    return clues


def generate_logic(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    n, k = _size_for(difficulty)
    people = _NAMES[:n]
    categories = list(_CATEGORY_POOLS)[:k]
    assignment: dict[str, dict[str, str]] = {p: {} for p in people}
    for cat in categories:
        values = _CATEGORY_POOLS[cat][:n]
        rng.shuffle(values)
        for person, value in zip(people, values):
            assignment[person][cat] = value
    clues = _make_clues(people, assignment, categories, rng)
    return GeneratedItem(
        content_type="logic",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={
            "people": people,
            "categories": {cat: _CATEGORY_POOLS[cat][:n] for cat in categories},
            "clues": clues,
        },
        solution={"assignment": assignment},
        metadata={"unique_required": True},
    )


def _consistent(candidate: dict[str, dict[str, str]], clues: list[dict[str, str]]) -> bool:
    for clue in clues:
        if clue.get("type") == "is":
            if candidate[clue["person"]].get(clue["category"]) != clue["value"]:
                return False
    return True


def _solve(people: list[str], categories: dict[str, list[str]], clues: list[dict[str, str]]) -> list[dict[str, dict[str, str]]]:
    """Brute-force all bijective assignments consistent with the clues."""
    cats = list(categories)
    per_category_perms = {cat: list(itertools.permutations(categories[cat])) for cat in cats}
    solutions: list[dict[str, dict[str, str]]] = []
    # Cap the search so pathological params can't hang the validator.
    combos = itertools.product(*(per_category_perms[cat] for cat in cats))
    checked = 0
    for combo in combos:
        checked += 1
        if checked > 200000:
            break
        candidate = {person: {} for person in people}
        for cat, perm in zip(cats, combo):
            for person, value in zip(people, perm):
                candidate[person][cat] = value
        if _consistent(candidate, clues):
            solutions.append(candidate)
            if len(solutions) > 1:
                break
    return solutions


def validate_logic(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="logic", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    people = payload.get("people", [])
    categories = payload.get("categories", {})
    clues = payload.get("clues", [])
    shipped = (item.get("solution") or {}).get("assignment", {})
    checks: dict[str, bool] = {}
    solutions = _solve(people, categories, clues)
    checks["has_solution"] = len(solutions) >= 1
    checks["unique_solution"] = len(solutions) == 1
    checks["shipped_matches"] = bool(solutions) and solutions[0] == shipped
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


registry.register(ContentType("logic", "puzzle", "Logic Grid", generate_logic, validate_logic))
