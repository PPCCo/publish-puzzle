from __future__ import annotations

import unittest
from pathlib import Path

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

from publishing_house import maintenance
from publishing_house.util import atomic_write_json, atomic_write_text


def _memory_dir(root: Path) -> Path:
    d = root / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_memory(memory_dir: Path, name: str, filename: str) -> None:
    atomic_write_text(
        memory_dir / filename,
        f"---\nname: {name}\ndescription: test\n---\n\nbody\n",
    )


class MaintenancePromotePruneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = common.RepoFixture()
        self.root = self.fixture.root
        self.memory = _memory_dir(self.root)

    def tearDown(self) -> None:
        self.fixture.close()

    def _seed_registry(self, entries: list[dict]) -> None:
        atomic_write_json(
            self.root / ".claude" / "config" / "framework_learnings.json",
            {"schema_version": "1.0", "learnings": entries},
        )

    def _reload(self, learning_id: str) -> dict:
        reg = maintenance.load_registry(self.root)
        return next(e for e in reg["learnings"] if e["id"] == learning_id)

    def test_report_is_idempotent_and_does_not_apply(self) -> None:
        self._seed_registry(
            [
                {
                    "id": "demo", "title": "t", "status": "reported", "auto_apply": True,
                    "matches_memory": ["demo"],
                    "sentinels": [{"file": ".claude/CLAUDE.md", "contains": "Mission"}],
                    "test": None,
                }
            ]
        )
        r1 = maintenance.promote(self.root, "demo", apply=False)
        r2 = maintenance.promote(self.root, "demo", apply=False)
        self.assertEqual(r1["mode"], "report")
        self.assertEqual(self._reload("demo")["status"], "reported")
        self.assertEqual(r2["mode"], "report")

    def test_apply_requires_verification(self) -> None:
        self._seed_registry(
            [
                {
                    "id": "demo", "title": "t", "status": "reported", "auto_apply": True,
                    "matches_memory": ["demo"],
                    "sentinels": [{"file": ".claude/CLAUDE.md", "contains": "THIS STRING IS NOT PRESENT"}],
                    "test": None,
                }
            ]
        )
        with self.assertRaises(ValueError):
            maintenance.promote(self.root, "demo", apply=True)

    def test_apply_marks_applied_when_verified(self) -> None:
        self._seed_registry(
            [
                {
                    "id": "demo", "title": "t", "status": "reported", "auto_apply": True,
                    "matches_memory": ["demo"],
                    "sentinels": [{"file": ".claude/CLAUDE.md", "contains": "Mission"}],
                    "test": None,
                }
            ]
        )
        result = maintenance.promote(self.root, "demo", apply=True)
        self.assertEqual(result["status"], "applied")
        entry = self._reload("demo")
        self.assertEqual(entry["status"], "applied")
        self.assertTrue(entry["changed_files"])

    def test_manual_learning_cannot_auto_apply(self) -> None:
        self._seed_registry(
            [
                {
                    "id": "manual", "title": "t", "status": "reported", "auto_apply": False,
                    "matches_memory": ["manual"],
                    "sentinels": [{"file": ".claude/CLAUDE.md", "contains": "Mission"}],
                    "test": None,
                }
            ]
        )
        with self.assertRaises(ValueError):
            maintenance.promote(self.root, "manual", apply=True)

    def test_prune_refuses_unless_applied_and_verified(self) -> None:
        self._seed_registry(
            [
                {
                    "id": "demo", "title": "t", "status": "reported", "auto_apply": True,
                    "matches_memory": ["demo"],
                    "sentinels": [{"file": ".claude/CLAUDE.md", "contains": "Mission"}],
                    "test": None,
                }
            ]
        )
        _write_memory(self.memory, "demo", "demo.md")
        with self.assertRaises(ValueError):
            maintenance.prune_memory(self.root, "demo", memory_dir=self.memory)
        self.assertTrue((self.memory / "demo.md").is_file())  # not removed

    def test_prune_removes_only_the_one_memory_and_index_line(self) -> None:
        self._seed_registry(
            [
                {
                    "id": "demo", "title": "t", "status": "applied", "auto_apply": True,
                    "matches_memory": ["demo"],
                    "sentinels": [{"file": ".claude/CLAUDE.md", "contains": "Mission"}],
                    "test": None,
                }
            ]
        )
        _write_memory(self.memory, "demo", "demo.md")
        _write_memory(self.memory, "keep", "keep.md")
        atomic_write_text(
            self.memory / "MEMORY.md",
            "# Memory index\n\n- [Demo](demo.md) — hook\n- [Keep](keep.md) — hook\n",
        )
        result = maintenance.prune_memory(self.root, "demo", memory_dir=self.memory)
        self.assertEqual(result["pruned_files"], ["demo.md"])
        self.assertEqual(result["index_lines_removed"], 1)
        self.assertFalse((self.memory / "demo.md").is_file())
        self.assertTrue((self.memory / "keep.md").is_file())  # sibling untouched
        index_text = (self.memory / "MEMORY.md").read_text(encoding="utf-8")
        self.assertNotIn("demo.md", index_text)
        self.assertIn("keep.md", index_text)
        self.assertEqual(self._reload("demo")["status"], "pruned")

    def test_rotate_hooks_refuses_events_ndjson(self) -> None:
        events = self.root / ".claude" / "logs" / "events.ndjson"
        events.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(events, "{}\n")
        with self.assertRaises(ValueError):
            maintenance.rotate_hooks_log(self.root, hooks_log=events)
        # untouched
        self.assertEqual(events.read_text(encoding="utf-8"), "{}\n")

    def test_rotate_hooks_archives_and_truncates(self) -> None:
        hooks = self.root / ".claude" / "logs" / "hooks.ndjson"
        hooks.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(hooks, '{"a":1}\n{"b":2}\n')
        result = maintenance.rotate_hooks_log(self.root, hooks_log=hooks)
        self.assertTrue(result["rotated"])
        self.assertEqual(hooks.read_text(encoding="utf-8"), "")
        backup = self.root / result["backup"]
        self.assertTrue(backup.is_file())
        self.assertIn('"a":1', backup.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
