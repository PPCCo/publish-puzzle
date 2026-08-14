from __future__ import annotations

import unittest

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

from publishing_house.generators.puzzles import (
    _count_sudoku_solutions,
    generate_sudoku,
    validate_sudoku,
)


class SudokuUniquenessTests(unittest.TestCase):
    def test_counter_solved_grid_is_one(self) -> None:
        item = generate_sudoku(seed=7, difficulty="easy", index=0, params={"clues": 81})
        self.assertEqual(_count_sudoku_solutions(item.payload["grid"], limit=2), 1)

    def test_counter_empty_grid_is_ambiguous(self) -> None:
        empty = [[0] * 9 for _ in range(9)]
        self.assertEqual(_count_sudoku_solutions(empty, limit=2), 2)  # early-exit at 2

    def test_validate_records_unique_solution_flag(self) -> None:
        item = generate_sudoku(seed=11, difficulty="easy", index=0, params={"clues": 81})
        result = validate_sudoku(_serialize(item))
        self.assertIn("unique_solution", result.checks)
        self.assertTrue(result.checks["unique_solution"])
        self.assertTrue(result.passed)

    def test_unique_solution_is_non_fatal(self) -> None:
        # A grid with too few clues is ambiguous, but the fatal checks
        # (solution_valid, clues_match_solution, has_givens) still pass, so the
        # item verifies while unique_solution is recorded False.
        item = generate_sudoku(seed=3, difficulty="easy", index=0, params={"clues": 81})
        serial = _serialize(item)
        # Strip most givens to force ambiguity while keeping >=17 and consistency.
        grid = serial["payload"]["grid"]
        kept = 0
        for r in range(9):
            for c in range(9):
                if grid[r][c] != 0:
                    kept += 1
                    if kept > 20:
                        grid[r][c] = 0
        result = validate_sudoku(serial)
        self.assertFalse(result.checks["unique_solution"])
        self.assertTrue(result.checks["clues_match_solution"])
        self.assertTrue(result.passed)  # non-fatal: item still verifies
        self.assertNotIn("unique_solution", result.errors)


def _serialize(item) -> dict:
    return {
        "index": item.index,
        "payload": {"grid": [row[:] for row in item.payload["grid"]], "given_count": item.payload.get("given_count"), "size": 9},
        "solution": {"grid": [row[:] for row in item.solution["grid"]]},
    }


if __name__ == "__main__":
    unittest.main()
