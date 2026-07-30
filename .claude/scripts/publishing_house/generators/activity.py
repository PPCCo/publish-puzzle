"""Word/letter activity generators + independent validators.

Contains: cryptogram, word-jumble, fill-in (criss-cross word placement). Each
validator re-derives correctness from the puzzle payload alone.
"""
from __future__ import annotations

import random
import string
from typing import Any

from .base import ContentType, GeneratedItem, ValidationResult, registry

_QUOTES = [
    "SMALL STEPS EVERY DAY ADD UP TO BIG RESULTS",
    "A CALM MIND SOLVES THE HARDEST PUZZLE",
    "PATIENCE TURNS EFFORT INTO MASTERY",
    "CURIOSITY IS THE ENGINE OF DISCOVERY",
    "EVERY EXPERT WAS ONCE A BEGINNER",
]
_JUMBLE_WORDS = [
    "PUZZLE", "LETTER", "ANSWER", "RIDDLE", "CLEVER", "MASTER",
    "SILENT", "GARDEN", "ORANGE", "PLANET", "BRIDGE", "CANDLE",
]


# --------------------------------------------------------------------------- #
# Cryptogram: substitution cipher over a quote.
# --------------------------------------------------------------------------- #
def _derangement(rng: random.Random) -> dict[str, str]:
    letters = list(string.ascii_uppercase)
    while True:
        shuffled = letters[:]
        rng.shuffle(shuffled)
        if all(a != b for a, b in zip(letters, shuffled)):
            return dict(zip(letters, shuffled))


def generate_cryptogram(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    plain = str(params.get("text") or rng.choice(_QUOTES)).upper()
    cipher = _derangement(rng)
    encoded = "".join(cipher.get(ch, ch) for ch in plain)
    hints = {}
    if difficulty in ("easy", "medium", "mixed"):
        hint_count = {"easy": 3, "medium": 2, "mixed": 2}.get(difficulty, 2)
        used = sorted({ch for ch in plain if ch.isalpha()})
        for letter in rng.sample(used, min(hint_count, len(used))):
            hints[cipher[letter]] = letter
    return GeneratedItem(
        content_type="cryptogram",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"ciphertext": encoded, "hints": hints},
        solution={"plaintext": plain, "key": cipher},
        metadata={"scheme": "monoalphabetic-substitution"},
    )


def validate_cryptogram(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="cryptogram", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    solution = item.get("solution") or {}
    key = solution.get("key", {})
    plain = solution.get("plaintext", "")
    cipher_text = payload.get("ciphertext", "")
    checks: dict[str, bool] = {}
    # Re-encode the plaintext with the shipped key and confirm it matches.
    reencoded = "".join(key.get(ch, ch) for ch in plain)
    checks["key_round_trips"] = reencoded == cipher_text
    # A valid substitution key must be a bijection over letters actually used.
    values = [v for k, v in key.items() if k.isalpha()]
    checks["key_is_bijection"] = len(values) == len(set(values))
    checks["no_fixed_points"] = all(k != v for k, v in key.items() if k.isalpha())
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


# --------------------------------------------------------------------------- #
# Word jumble: scramble words; solver unscrambles.
# --------------------------------------------------------------------------- #
def _scramble(word: str, rng: random.Random) -> str:
    if len(word) < 2:
        return word
    letters = list(word)
    for _ in range(20):
        rng.shuffle(letters)
        if "".join(letters) != word:
            break
    return "".join(letters)


def generate_jumble(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    count = {"easy": 5, "medium": 7, "hard": 9, "expert": 10, "mixed": 7}.get(difficulty, 7)
    pool = [w.strip().upper() for w in (params.get("words") or _JUMBLE_WORDS) if w.strip()]
    rng.shuffle(pool)
    chosen = pool[:count]
    jumbles = [{"scrambled": _scramble(word, rng), "length": len(word)} for word in chosen]
    return GeneratedItem(
        content_type="jumble",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"items": jumbles},
        solution={"words": chosen},
        metadata={},
    )


def validate_jumble(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="jumble", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    words = (item.get("solution") or {}).get("words", [])
    items = payload.get("items", [])
    checks: dict[str, bool] = {"counts_match": len(items) == len(words)}
    anagram_ok = True
    for entry, word in zip(items, words):
        if sorted(entry.get("scrambled", "")) != sorted(word):
            anagram_ok = False
            break
    checks["each_is_anagram"] = anagram_ok and bool(words)
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


# --------------------------------------------------------------------------- #
# Fill-in (criss-cross): place words into a grid; solver fills from a bank.
# --------------------------------------------------------------------------- #
def generate_fillin(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    size = {"easy": 9, "medium": 11, "hard": 13, "expert": 15, "mixed": 11}.get(difficulty, 11)
    pool = [w.strip().upper() for w in (params.get("words") or _JUMBLE_WORDS) if w.strip() and len(w.strip()) <= size]
    rng.shuffle(pool)
    grid = [[None for _ in range(size)] for _ in range(size)]
    placements: list[dict[str, Any]] = []

    def _fits(word: str, r: int, c: int, dr: int, dc: int) -> bool:
        for i, ch in enumerate(word):
            rr, cc = r + dr * i, c + dc * i
            if not (0 <= rr < size and 0 <= cc < size):
                return False
            cell = grid[rr][cc]
            if cell not in (None, ch):
                return False
        return True

    def _write(word: str, r: int, c: int, dr: int, dc: int) -> None:
        for i, ch in enumerate(word):
            grid[r + dr * i][c + dc * i] = ch
        placements.append({"word": word, "row": r, "col": c, "dr": dr, "dc": dc})

    # First word centred horizontally; the rest try to cross existing letters.
    if pool:
        first = pool[0]
        _write(first, size // 2, max(0, (size - len(first)) // 2), 0, 1)
    for word in pool[1:]:
        placed = False
        for r in range(size):
            for c in range(size):
                for dr, dc in ((0, 1), (1, 0)):
                    if _fits(word, r, c, dr, dc):
                        crosses = any(grid[r + dr * i][c + dc * i] is not None for i in range(len(word)))
                        if crosses and _fits(word, r, c, dr, dc):
                            _write(word, r, c, dr, dc)
                            placed = True
                            break
                if placed:
                    break
            if placed:
                break
    return GeneratedItem(
        content_type="fillin",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={
            "size": size,
            "blocked": [[grid[r][c] is None for c in range(size)] for r in range(size)],
            "bank": sorted({p["word"] for p in placements}),
        },
        solution={"placements": placements, "grid": grid},
        metadata={},
    )


def validate_fillin(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="fillin", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    solution = item.get("solution") or {}
    size = payload.get("size", 0)
    placements = solution.get("placements", [])
    grid = solution.get("grid", [])
    checks: dict[str, bool] = {}
    within = True
    spelled_ok = True
    for placement in placements:
        word, r, c = placement["word"], placement["row"], placement["col"]
        dr, dc = placement["dr"], placement["dc"]
        for i, ch in enumerate(word):
            rr, cc = r + dr * i, c + dc * i
            if not (0 <= rr < size and 0 <= cc < size):
                within = False
                break
            if grid[rr][cc] != ch:
                spelled_ok = False
    checks["placements_in_bounds"] = within and bool(placements)
    checks["grid_matches_placements"] = spelled_ok
    checks["bank_matches"] = sorted(payload.get("bank", [])) == sorted({p["word"] for p in placements})
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


registry.register(ContentType("cryptogram", "activity", "Cryptogram", generate_cryptogram, validate_cryptogram))
registry.register(ContentType("jumble", "activity", "Word Jumble", generate_jumble, validate_jumble))
registry.register(ContentType("fillin", "activity", "Fill-In (Criss-Cross)", generate_fillin, validate_fillin))
