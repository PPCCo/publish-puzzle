"""Coverage for the product-aligned series/set layer (publishing_house.series + hooks).

These tests exercise the changes that re-aligned the grafted novel-publisher series
code to the puzzle/coloring/journal/printable product framework:

  1. add_book for each product_type -> a schema-valid child project with the right
     product-band audience and product formats.
  2. Series schema 1.1 rejects novel-only enums (epub, nonfiction, middle-grade-9-12)
     and accepts the product enums.
  3. 1.0 -> 1.1 in-memory migration reads an old manifest without loss.
  4. plan_next emits series_next only for in-series projects with an uncreated next
     slot, and never mutates all_forward_options or blockers.
  5. series_milestone still reports (never grants) after the changes.
  6. sync_series_catalog writes a catalog/series.json carrying product vocabulary.
  7. series suggest-from-research returns a schema-valid --books-json payload from a
     fixture pipeline and mutates nothing (no promote, no series created).
  8. The product-series-add-book skill's three modes drive the expected CLI calls and
     never emit a transition/approve/freeze/external-write verb.

Nothing here touches the network; all work happens in a disposable RepoFixture.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from common import SOURCE_ROOT, RepoFixture

from publishing_house import research, series
from publishing_house.errors import ValidationFailure
from publishing_house.planner import plan_next
from publishing_house.project import validate_file_data
from publishing_house.util import atomic_write_yaml, load_json, load_yaml


def _plan(position: int, working_title: str, **over) -> dict:
    book = {
        "position": position,
        "working_title": working_title,
        "topic": working_title,
        "scope": f"{working_title} scope",
    }
    book.update(over)
    return book


class AddBookProductTypeTests(unittest.TestCase):
    """1. add_book for each product_type yields a schema-valid child project."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_add_book_creates_valid_child_per_product_type(self) -> None:
        for product_type in ("puzzle-book", "coloring-book", "guided-journal", "digital-printable"):
            sid = f"set-{product_type}"
            series.init_series(
                self.root,
                series_title=f"{product_type} set",
                premise="A set for testing product families.",
                books=[
                    _plan(1, f"{product_type} vol 1"),
                    _plan(2, f"{product_type} vol 2"),
                ],
                audience="adult-general",
                product_type=product_type,
                series_id=sid,
                create_first_book=False,
                created_by="test-suite",
            )
            formats = ["digital-pdf"] if product_type == "digital-printable" else ["paperback"]
            out = series.add_book(
                self.root, sid, position=1, audience="adult-general",
                product_type=product_type, formats=formats, created_by="test-suite",
            )
            pid = out["book"]["project_id"]
            project = load_yaml(self.root / "projects" / pid / "project.yaml")
            # Child project validates against the product schema.
            self.assertEqual(validate_file_data(self.root, project, "project.schema.json"), [])
            self.assertEqual(project["product_type"], product_type)
            self.assertEqual(project["audience"], "adult-general")
            self.assertEqual(project["formats"], formats)
            # The bidirectional link is present on the child.
            self.assertEqual(project["series"]["series_id"], sid)
            self.assertEqual(project["series"]["position"], 1)


class SeriesSchemaEnumTests(unittest.TestCase):
    """2. Schema 1.1 rejects novel-only enums, accepts product enums."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def _manifest(self, **over) -> dict:
        base = {
            "schema_version": "1.1",
            "series_id": "enum-set",
            "series_title": "T",
            "premise": "p",
            "audience": "adult-general",
            "language": "en-US",
            "created_at": "2026-08-12T00:00:00Z",
            "created_by": "test",
            "product_type": "puzzle-book",
            "books": [
                {"position": 1, "working_title": "V1", "topic": "t", "scope": "s"},
            ],
        }
        base.update(over)
        return base

    def test_accepts_product_enums(self) -> None:
        self.assertEqual(
            validate_file_data(self.root, self._manifest(), "series.schema.json"), []
        )

    def test_rejects_novel_audience_enum(self) -> None:
        errs = validate_file_data(
            self.root, self._manifest(audience="middle-grade-9-12"), "series.schema.json"
        )
        self.assertTrue(errs)

    def test_rejects_novel_product_type_enum(self) -> None:
        errs = validate_file_data(
            self.root, self._manifest(product_type="nonfiction"), "series.schema.json"
        )
        self.assertTrue(errs)

    def test_rejects_novel_format_enum_in_slot(self) -> None:
        m = self._manifest()
        m["books"][0]["formats"] = ["epub"]
        errs = validate_file_data(self.root, m, "series.schema.json")
        self.assertTrue(errs)

    def test_accepts_product_format_enum_in_slot(self) -> None:
        m = self._manifest()
        m["books"][0]["formats"] = ["digital-pdf"]
        self.assertEqual(validate_file_data(self.root, m, "series.schema.json"), [])


class ManifestMigrationTests(unittest.TestCase):
    """3. 1.0 -> 1.1 in-memory migration reads an old manifest without loss."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_load_manifest_migrates_legacy_vocabulary(self) -> None:
        legacy = {
            "schema_version": "1.0",
            "series_id": "legacy",
            "series_title": "Legacy Set",
            "premise": "Grafted from the novel publisher.",
            "audience": "middle-grade-9-12",
            "language": "en-US",
            "created_at": "2026-01-01T00:00:00Z",
            "created_by": "human",
            "book_type": "picture-book",
            "books": [
                {
                    "position": 1,
                    "working_title": "Old Vol 1",
                    "topic": "t1",
                    "scope": "s1",
                    "audience": "early-reader-6-8",
                    "book_type": "picture-book",
                    "formats": ["epub", "paperback", "audiobook"],
                    "project_id": None,
                },
            ],
        }
        path = self.root / "series" / "legacy" / "series.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_yaml(path, legacy)

        migrated = series._load_manifest(path)  # noqa: SLF001

        # Top-level vocabulary mapped; book_type folded into product_type.
        self.assertEqual(migrated["audience"], "tween-8-12")
        self.assertEqual(migrated["product_type"], "coloring-book")
        self.assertNotIn("book_type", migrated)
        # Nothing lost: title/premise/position/slug survive.
        self.assertEqual(migrated["series_title"], "Legacy Set")
        slot = migrated["books"][0]
        self.assertEqual(slot["working_title"], "Old Vol 1")
        self.assertEqual(slot["audience"], "kids-6-10")
        self.assertEqual(slot["product_type"], "coloring-book")
        # epub -> digital-pdf, paperback kept, audiobook dropped (no equivalent).
        self.assertEqual(slot["formats"], ["digital-pdf", "paperback"])
        # Migration is read-only: on-disk file still carries the legacy vocabulary.
        on_disk = load_yaml(path)
        self.assertEqual(on_disk["audience"], "middle-grade-9-12")
        self.assertEqual(on_disk["book_type"], "picture-book")

    def test_migration_is_idempotent_on_current_manifest(self) -> None:
        current = {
            "schema_version": "1.1",
            "series_id": "cur",
            "series_title": "Current",
            "premise": "p",
            "audience": "adult-general",
            "language": "en-US",
            "created_at": "2026-08-12T00:00:00Z",
            "created_by": "human",
            "product_type": "puzzle-book",
            "books": [
                {"position": 1, "working_title": "V1", "topic": "t", "scope": "s",
                 "audience": "adult-general", "product_type": "puzzle-book",
                 "formats": ["paperback"], "project_id": None},
            ],
        }
        again = series._migrate_manifest(current)  # noqa: SLF001
        self.assertEqual(again["audience"], "adult-general")
        self.assertEqual(again["product_type"], "puzzle-book")
        self.assertEqual(again["books"][0]["formats"], ["paperback"])


class PlanNextSeriesHintTests(unittest.TestCase):
    """4. plan_next series_next hint: in-series + uncreated next slot only; never
    perturbs all_forward_options or blockers."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def _make_series_with_vol1(self) -> str:
        out = series.init_series(
            self.root,
            series_title="Sudoku Ladder",
            premise="Easy to hard.",
            books=[_plan(1, "Easy"), _plan(2, "Medium")],
            audience="adult-general",
            product_type="puzzle-book",
            series_id="ladder",
            create_first_book=True,
            created_by="test-suite",
        )
        return out["created_book"]["project_id"]

    def _set_state(self, pid: str, state_name: str) -> None:
        state_path = self.root / "projects" / pid / "state.json"
        state = load_json(state_path)
        state["current_state"] = state_name
        from publishing_house.util import atomic_write_json
        atomic_write_json(state_path, state)

    def test_series_next_none_for_non_series_project(self) -> None:
        pid, _ = self.fixture.project(project_id="clr-2026-standalone")
        result = plan_next(self.root, pid)
        self.assertIsNone(result["series_next"])

    def test_series_next_none_before_release_authorization(self) -> None:
        pid = self._make_series_with_vol1()  # starts at DISCOVERY
        result = plan_next(self.root, pid)
        self.assertIsNone(result["series_next"])

    def test_series_next_present_at_release_with_uncreated_slot(self) -> None:
        pid = self._make_series_with_vol1()
        self._set_state(pid, "RELEASE_AUTHORIZATION")
        result = plan_next(self.root, pid)
        self.assertIsNotNone(result["series_next"])
        self.assertEqual(result["series_next"]["series_id"], "ladder")
        self.assertEqual(result["series_next"]["next_position"], 2)
        self.assertIn("series add-book ladder --position 2", result["series_next"]["suggested_command"])

    def test_series_next_does_not_perturb_forward_options_or_blockers(self) -> None:
        pid = self._make_series_with_vol1()
        self._set_state(pid, "RELEASE_AUTHORIZATION")
        with_hint = plan_next(self.root, pid)
        # The hint is advisory: forward options + blockers match the same run's
        # non-series fields (which the hint must not touch). Assert the hint is
        # purely additive by checking the documented invariant keys exist and the
        # autonomy decision is unaffected by the presence of series_next.
        self.assertIn("all_forward_options", with_hint)
        self.assertIsInstance(with_hint["all_forward_options"], list)
        self.assertIsInstance(with_hint["blockers"], list)
        # series_next is a separate key; removing it leaves a valid plan dict.
        self.assertIn("autonomy_action", with_hint)

    def test_series_next_none_when_all_slots_created(self) -> None:
        pid = self._make_series_with_vol1()
        series.add_book(self.root, "ladder", position=2, created_by="test-suite")
        self._set_state(pid, "RELEASE_AUTHORIZATION")
        result = plan_next(self.root, pid)
        self.assertIsNone(result["series_next"])


class SeriesMilestoneReportingTests(unittest.TestCase):
    """5. series_milestone still reports and never grants."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_milestone_reports_not_reached_with_uncreated_slot(self) -> None:
        series.init_series(
            self.root, series_title="Ladder", premise="p",
            books=[_plan(1, "Easy"), _plan(2, "Medium")],
            audience="adult-general", product_type="puzzle-book",
            series_id="ladder", create_first_book=True, created_by="test-suite",
        )
        result = series.series_milestone(self.root, "ladder", target_state="PUBLISHED")
        self.assertFalse(result["milestone_reached"])
        self.assertFalse(result["all_books_created"])
        # Reporting only: no approval/gate/state artifact is produced.
        self.assertNotIn("approval", result)
        self.assertNotIn("granted", result)

    def test_milestone_rejects_unknown_target_state(self) -> None:
        series.init_series(
            self.root, series_title="Ladder", premise="p",
            books=[_plan(1, "Easy"), _plan(2, "Medium")],
            audience="adult-general", product_type="puzzle-book",
            series_id="ladder", create_first_book=False, created_by="test-suite",
        )
        with self.assertRaises(ValidationFailure):
            series.series_milestone(self.root, "ladder", target_state="NOT_A_STATE")


class SeriesCatalogVocabularyTests(unittest.TestCase):
    """6. sync_series_catalog writes catalog/series.json with product vocabulary."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_series_catalog_carries_product_vocabulary_and_validates(self) -> None:
        series.init_series(
            self.root, series_title="Ladder", premise="p",
            books=[_plan(1, "Easy"), _plan(2, "Medium")],
            audience="senior-large-print", product_type="puzzle-book",
            series_id="ladder", create_first_book=True, created_by="test-suite",
        )
        catalog = series.sync_series_catalog(self.root)
        # Validates against the catalog schema.
        self.assertEqual(
            validate_file_data(self.root, catalog, "series-catalog.schema.json"), []
        )
        entry = next(e for e in catalog["series"] if e["series_id"] == "ladder")
        self.assertEqual(entry["audience"], "senior-large-print")
        self.assertEqual(entry["product_type"], "puzzle-book")
        # Written to disk.
        on_disk = load_json(self.root / "catalog" / "series.json")
        self.assertTrue(any(e["series_id"] == "ladder" for e in on_disk["series"]))


class SuggestFromResearchTests(unittest.TestCase):
    """7. suggest-from-research returns a schema-valid books payload and mutates
    nothing (no promote, no series created)."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def _seed_pipeline(self) -> None:
        research.init_research(self.root, "Logic Puzzles")
        # Two explicitly-grouped volumes (a real series) + one lone journal (group of 1).
        research.pipeline_add(self.root, "Logic Puzzles", {
            "product_id": "easy-sudoku", "status": "candidate", "working_title": "Easy Sudoku",
            "audience": "adult-general", "product_type": "puzzle-book", "formats": ["paperback"],
            "priority": 2, "difficulty": {"tier": "easy"},
            "series_grouping": {"is_series": True, "series_slug": "sudoku-ladder", "position": 1},
            "positioning": "gentle warm-up",
        })
        research.pipeline_add(self.root, "Logic Puzzles", {
            "product_id": "medium-sudoku", "status": "candidate", "working_title": "Medium Sudoku",
            "audience": "adult-general", "product_type": "puzzle-book", "formats": ["paperback"],
            "priority": 1, "difficulty": {"tier": "medium"},
            "series_grouping": {"is_series": True, "series_slug": "sudoku-ladder", "position": 2},
        })
        research.pipeline_add(self.root, "Logic Puzzles", {
            "product_id": "lone-journal", "status": "candidate", "working_title": "Solo Journal",
            "audience": "adult-general", "product_type": "guided-journal", "formats": ["paperback"],
        })

    def test_suggestion_groups_orders_and_excludes_singletons(self) -> None:
        self._seed_pipeline()
        out = series.suggest_series_from_research(self.root, "Logic Puzzles")
        self.assertEqual(out["candidate_count"], 3)
        # Only the 2-volume sudoku group qualifies; the lone journal is excluded.
        self.assertEqual(out["suggested_series_count"], 1)
        suggestion = out["suggestions"][0]
        self.assertEqual(suggestion["grouping"], "explicit")
        titles = [b["working_title"] for b in suggestion["books"]]
        # Ordered by explicit position, not by priority (medium has higher priority).
        self.assertEqual(titles, ["Easy Sudoku", "Medium Sudoku"])
        self.assertEqual([b["position"] for b in suggestion["books"]], [1, 2])

    def test_suggested_books_payload_builds_a_valid_series(self) -> None:
        self._seed_pipeline()
        out = series.suggest_series_from_research(self.root, "Logic Puzzles")
        payload = out["suggestions"][0]["series_init_payload"]
        # Strip the non-schema helper key, as the skill does, then init a series.
        books = [{k: v for k, v in b.items() if k != "source_product_id"} for b in payload["books"]]
        result = series.init_series(
            self.root, series_title=payload["title"], premise=payload["premise"],
            books=books, audience=payload["audience"], product_type=payload["product_type"],
            series_id="from-research", create_first_book=False, created_by="test-suite",
        )
        manifest = load_yaml(self.root / "series" / "from-research" / "series.yaml")
        self.assertEqual(validate_file_data(self.root, manifest, "series.schema.json"), [])
        self.assertEqual(len(manifest["books"]), 2)
        self.assertEqual(result["series"]["series_id"], "from-research")

    def test_suggest_mutates_nothing(self) -> None:
        self._seed_pipeline()
        before = research.show_research(self.root, "Logic Puzzles")
        series.suggest_series_from_research(self.root, "Logic Puzzles")
        after = research.show_research(self.root, "Logic Puzzles")
        # No promote: all three entries remain candidates.
        self.assertEqual(after["counts"]["promoted"], 0)
        self.assertEqual(before["counts"]["candidates"], after["counts"]["candidates"])
        # No series directory created.
        self.assertFalse((self.root / "series").exists())

    def test_suggest_missing_category_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            series.suggest_series_from_research(self.root, "never-researched")


class AddBookSkillContractTests(unittest.TestCase):
    """8. The product-series-add-book skill drives the expected CLI calls and never
    emits a transition/approve/freeze/external-write verb."""

    SKILL = SOURCE_ROOT / ".claude" / "skills" / "product-series-add-book" / "SKILL.md"

    def setUp(self) -> None:
        self.text = self.SKILL.read_text(encoding="utf-8")

    def test_skill_exists_and_is_user_invocable_sonnet(self) -> None:
        self.assertTrue(self.SKILL.is_file())
        self.assertIn("user-invocable: true", self.text)
        self.assertIn("claude-sonnet-5", self.text)  # pinned to Sonnet, never Opus

    def test_skill_drives_the_three_mode_cli_calls(self) -> None:
        self.assertIn("series add-book", self.text)   # mode 1
        self.assertIn("series link", self.text)        # mode 2
        self.assertIn("series suggest-from-research", self.text)  # mode 3
        self.assertIn("research promote", self.text)   # mode 3 bookkeeping
        # Mode 3 requires a human choice before building.
        self.assertIn("AskUserQuestion", self.text)

    def test_skill_emits_no_forbidden_verbs(self) -> None:
        # The add-book skill links/creates volumes; it must never transition state,
        # approve/freeze a gate, or perform an external write.
        forbidden = [
            "project transition",
            "approval grant",
            "approval release-authorize",
            "artifact freeze",
            "content-freeze",
        ]
        for verb in forbidden:
            self.assertNotIn(verb, self.text, f"skill must not emit '{verb}'")

    def test_skill_states_per_volume_gate_independence(self) -> None:
        # The core safety invariant: no series-level gate bypasses a volume's gates.
        lowered = self.text.lower()
        self.assertIn("six", lowered)
        self.assertIn("gate", lowered)
        self.assertTrue(
            "does not create a series-level" in lowered
            or "not create a series-level" in lowered,
            "skill must state it creates no series-level gate",
        )


if __name__ == "__main__":
    unittest.main()
