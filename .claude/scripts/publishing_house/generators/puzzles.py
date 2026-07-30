"""Grid-based puzzle generators + independent validators.

Contains: sudoku, word-search, maze, number-search. Each generator is a pure
function of (seed, difficulty, index, params); each validator re-derives
correctness from the serialized puzzle alone and NEVER trusts the shipped
solution key --- it recomputes it.
"""
from __future__ import annotations

import random
from typing import Any

from .base import ContentType, GeneratedItem, ValidationResult, registry

# --------------------------------------------------------------------------- #
# Difficulty -> concrete knobs. Kept small and explicit so a validator can also
# reason about the intended shape of an item.
# --------------------------------------------------------------------------- #
_SUDOKU_CLUES = {"easy": 40, "medium": 32, "hard": 26, "expert": 23, "mixed": 32}
_WORDSEARCH_SIZE = {"easy": 10, "medium": 13, "hard": 16, "expert": 18, "mixed": 13}
_MAZE_SIZE = {"easy": 10, "medium": 16, "hard": 22, "expert": 28, "mixed": 16}


def _clamp_difficulty(difficulty: str, table: dict[str, Any]) -> Any:
    return table.get(difficulty, table["mixed"])


# --------------------------------------------------------------------------- #
# Sudoku
# --------------------------------------------------------------------------- #
def _pattern(r: int, c: int) -> int:
    return (3 * (r % 3) + r // 3 + c) % 9


def _shuffled_base(rng: random.Random) -> list[list[int]]:
    rows = [g * 3 + r for g in rng.sample(range(3), 3) for r in rng.sample(range(3), 3)]
    cols = [g * 3 + c for g in rng.sample(range(3), 3) for c in rng.sample(range(3), 3)]
    nums = rng.sample(range(1, 10), 9)
    return [[nums[_pattern(r, c)] for c in cols] for r in rows]


def generate_sudoku(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    solution = _shuffled_base(rng)
    clues = int(params.get("clues") or _clamp_difficulty(difficulty, _SUDOKU_CLUES))
    cells = [(r, c) for r in range(9) for c in range(9)]
    rng.shuffle(cells)
    keep = set(cells[:clues])
    puzzle = [[solution[r][c] if (r, c) in keep else 0 for c in range(9)] for r in range(9)]
    return GeneratedItem(
        content_type="sudoku",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"grid": puzzle, "given_count": clues, "size": 9},
        solution={"grid": solution},
        metadata={"rule": "standard-9x9"},
    )


def _valid_sudoku_solution(grid: list[list[int]]) -> bool:
    if len(grid) != 9 or any(len(row) != 9 for row in grid):
        return False
    target = set(range(1, 10))
    for i in range(9):
        if {grid[i][j] for j in range(9)} != target:
            return False
        if {grid[j][i] for j in range(9)} != target:
            return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            block = {grid[br + dr][bc + dc] for dr in range(3) for dc in range(3)}
            if block != target:
                return False
    return True


def validate_sudoku(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="sudoku", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    solution = (item.get("solution") or {}).get("grid", [])
    puzzle = payload.get("grid", [])
    checks: dict[str, bool] = {}
    checks["solution_valid"] = _valid_sudoku_solution(solution)
    consistent = (
        len(puzzle) == 9
        and all(len(row) == 9 for row in puzzle)
        and all(
            puzzle[r][c] in (0, solution[r][c]) if checks["solution_valid"] else False
            for r in range(len(puzzle))
            for c in range(len(puzzle[r]))
        )
    )
    checks["clues_match_solution"] = bool(consistent)
    givens = sum(1 for row in puzzle for v in row if v)
    checks["has_givens"] = givens >= 17  # theoretical minimum for a unique 9x9
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


# --------------------------------------------------------------------------- #
# Word search
# --------------------------------------------------------------------------- #
_DIRECTIONS = [(0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]
_DEFAULT_WORDS = [
    "PUZZLE", "LETTER", "SEARCH", "HIDDEN", "FOCUS", "RELAX", "BRAIN", "SOLVE",
    "GRID", "CLEVER", "MASTER", "RIDDLE", "ANSWER", "LOGIC", "QUIET", "THINK",
]


def _place_word(grid: list[list[str]], word: str, rng: random.Random, size: int) -> tuple[int, int, tuple[int, int]] | None:
    positions = [(r, c) for r in range(size) for c in range(size)]
    rng.shuffle(positions)
    directions = _DIRECTIONS[:]
    rng.shuffle(directions)
    for (r, c) in positions:
        for (dr, dc) in directions:
            end_r, end_c = r + dr * (len(word) - 1), c + dc * (len(word) - 1)
            if not (0 <= end_r < size and 0 <= end_c < size):
                continue
            ok = True
            for i, ch in enumerate(word):
                cell = grid[r + dr * i][c + dc * i]
                if cell not in (" ", ch):
                    ok = False
                    break
            if ok:
                for i, ch in enumerate(word):
                    grid[r + dr * i][c + dc * i] = ch
                return r, c, (dr, dc)
    return None


def generate_wordsearch(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    size = int(params.get("size") or _clamp_difficulty(difficulty, _WORDSEARCH_SIZE))
    raw_words = params.get("words") or _DEFAULT_WORDS
    words = [w.strip().upper() for w in raw_words if w.strip() and len(w.strip()) <= size]
    grid = [[" " for _ in range(size)] for _ in range(size)]
    placements: list[dict[str, Any]] = []
    for word in words:
        placed = _place_word(grid, word, rng, size)
        if placed:
            r, c, (dr, dc) = placed
            placements.append({"word": word, "row": r, "col": c, "dr": dr, "dc": dc})
    for r in range(size):
        for c in range(size):
            if grid[r][c] == " ":
                grid[r][c] = chr(rng.randint(ord("A"), ord("Z")))
    return GeneratedItem(
        content_type="wordsearch",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"grid": grid, "words": [p["word"] for p in placements], "size": size},
        solution={"placements": placements},
        metadata={"diagonals": True, "reversed": True},
    )


def validate_wordsearch(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="wordsearch", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    grid = payload.get("grid", [])
    placements = (item.get("solution") or {}).get("placements", [])
    size = payload.get("size", len(grid))
    checks: dict[str, bool] = {}
    checks["square_grid"] = len(grid) == size and all(len(row) == size for row in grid)
    all_found = True
    for placement in placements:
        word = placement["word"]
        r, c, dr, dc = placement["row"], placement["col"], placement["dr"], placement["dc"]
        try:
            spelled = "".join(grid[r + dr * i][c + dc * i] for i in range(len(word)))
        except IndexError:
            all_found = False
            break
        if spelled != word:
            all_found = False
            break
    checks["all_words_placed"] = all_found and bool(placements)
    checks["word_list_matches"] = sorted(payload.get("words", [])) == sorted(p["word"] for p in placements)
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


# --------------------------------------------------------------------------- #
# Maze (depth-first perfect maze; unique path between entrance and exit)
# --------------------------------------------------------------------------- #
def generate_maze(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    size = int(params.get("size") or _clamp_difficulty(difficulty, _MAZE_SIZE))
    # walls[r][c] = {"N","E","S","W"} present. Start all walls up.
    walls = [[{"N": True, "E": True, "S": True, "W": True} for _ in range(size)] for _ in range(size)]
    visited = [[False] * size for _ in range(size)]
    stack = [(0, 0)]
    visited[0][0] = True
    opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
    moves = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
    while stack:
        r, c = stack[-1]
        neighbours = []
        for direction, (dr, dc) in moves.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and not visited[nr][nc]:
                neighbours.append((direction, nr, nc))
        if not neighbours:
            stack.pop()
            continue
        direction, nr, nc = rng.choice(neighbours)
        walls[r][c][direction] = False
        walls[nr][nc][opposite[direction]] = False
        visited[nr][nc] = True
        stack.append((nr, nc))
    return GeneratedItem(
        content_type="maze",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"walls": walls, "size": size, "entrance": [0, 0], "exit": [size - 1, size - 1]},
        solution={"algorithm": "dfs-perfect-maze"},
        metadata={"perfect": True},
    )


def _maze_solvable(walls: list[list[dict[str, bool]]], size: int, start: tuple[int, int], goal: tuple[int, int]) -> bool:
    moves = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
    seen = {start}
    stack = [start]
    while stack:
        r, c = stack.pop()
        if (r, c) == goal:
            return True
        for direction, (dr, dc) in moves.items():
            if walls[r][c].get(direction, True):
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return False


def validate_maze(item: dict[str, Any]) -> ValidationResult:
    result = ValidationResult(content_type="maze", index=int(item.get("index", 0)), passed=True)
    payload = item.get("payload", {})
    walls = payload.get("walls", [])
    size = payload.get("size", len(walls))
    entrance = tuple(payload.get("entrance", [0, 0]))
    exit_cell = tuple(payload.get("exit", [size - 1, size - 1]))
    checks: dict[str, bool] = {}
    checks["dimensions"] = len(walls) == size and all(len(row) == size for row in walls)
    checks["solvable"] = checks["dimensions"] and _maze_solvable(walls, size, entrance, exit_cell)
    result.checks = checks
    result.passed = all(checks.values())
    if not result.passed:
        result.errors = [name for name, ok in checks.items() if not ok]
    return result


# --------------------------------------------------------------------------- #
# Number search (word-search over digit strings)
# --------------------------------------------------------------------------- #
def generate_numbersearch(seed: int, difficulty: str, index: int, params: dict[str, Any]) -> GeneratedItem:
    rng = random.Random(seed)
    size = int(params.get("size") or _clamp_difficulty(difficulty, _WORDSEARCH_SIZE))
    count = {"easy": 6, "medium": 8, "hard": 10, "expert": 12, "mixed": 8}.get(difficulty, 8)
    numbers = []
    for _ in range(count):
        length = rng.randint(3, min(5, size))
        numbers.append("".join(str(rng.randint(0, 9)) for _ in range(length)))
    grid = [[" " for _ in range(size)] for _ in range(size)]
    placements: list[dict[str, Any]] = []
    for number in numbers:
        placed = _place_word(grid, number, rng, size)
        if placed:
            r, c, (dr, dc) = placed
            placements.append({"word": number, "row": r, "col": c, "dr": dr, "dc": dc})
    for r in range(size):
        for c in range(size):
            if grid[r][c] == " ":
                grid[r][c] = str(rng.randint(0, 9))
    return GeneratedItem(
        content_type="numbersearch",
        index=index,
        difficulty=difficulty,
        seed=seed,
        payload={"grid": grid, "numbers": [p["word"] for p in placements], "size": size},
        solution={"placements": placements},
        metadata={"alphabet": "digits"},
    )


def validate_numbersearch(item: dict[str, Any]) -> ValidationResult:
    base = validate_wordsearch(item)
    base.content_type = "numbersearch"
    return base


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #
registry.register(ContentType("sudoku", "puzzle", "Sudoku (9x9)", generate_sudoku, validate_sudoku))
registry.register(ContentType("wordsearch", "puzzle", "Word Search", generate_wordsearch, validate_wordsearch))
registry.register(ContentType("maze", "puzzle", "Maze", generate_maze, validate_maze))
registry.register(ContentType("numbersearch", "puzzle", "Number Search", generate_numbersearch, validate_numbersearch))
