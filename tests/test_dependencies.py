from __future__ import annotations

import json
import unittest

from common import RepoFixture

from publishing_house import dependencies as deps
from publishing_house.rights import check_rights
from publishing_house.util import load_json


class DependencyRegistryTests(unittest.TestCase):
    """The offline license-checked dependency (font) registry."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_default_registry_loads_and_validates(self) -> None:
        config = deps.load_dependency_config(self.root)
        self.assertEqual("1.0", config["schema_version"])
        self.assertIsInstance(config.get("fonts"), list)
        self.assertGreaterEqual(len(config["fonts"]), 1)

    def test_font_registry_is_normalized_and_sorted(self) -> None:
        registry = deps.font_registry(self.root)
        families = [font["family"] for font in registry]
        self.assertEqual(families, sorted(families), "registry must be family-sorted")
        for font in registry:
            # Normalization guarantees these keys and types on every entry.
            self.assertIsInstance(font["family"], str)
            self.assertIsInstance(font["role_tags"], list)
            self.assertIsInstance(font["embedding_allowed"], bool)
            self.assertIsInstance(font["commercial_use_verified"], bool)
            self.assertIsInstance(font["territories"], list)

    def test_default_families_are_present(self) -> None:
        families = {font["family"] for font in deps.font_registry(self.root)}
        self.assertIn("Andika", families)
        self.assertIn("Atkinson Hyperlegible Next", families)

    def test_get_font_raises_with_known_families_listed(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            deps.get_font(self.root, "No Such Font")
        message = str(ctx.exception)
        self.assertIn("No Such Font", message)
        # The error must name the registered families so the caller can recover.
        self.assertIn("Andika", message)

    def test_verified_family_is_clearable(self) -> None:
        andika = deps.get_font(self.root, "Andika")
        self.assertTrue(andika["embedding_allowed"])
        self.assertTrue(andika["commercial_use_verified"])
        self.assertTrue(deps.font_is_clearable(andika))

    def test_local_override_can_add_an_unverified_family(self) -> None:
        # A local override JOINS the default registry via deep_merge. Adding an
        # unverified family proves the clearable predicate is data-driven, not
        # hard-coded to the shipped defaults.
        local = self.root.joinpath(*deps.LOCAL_RELPATH)
        local.write_text(
            json.dumps(
                {
                    "fonts": [
                        {
                            "family": "Unverified Display",
                            "role_tags": ["display"],
                            "source": "Test foundry",
                            "license_reference": "proprietary-unknown",
                            "license_text_path": ".claude/config/licenses/OFL-1.1.md",
                            "embedding_allowed": True,
                            "commercial_use_verified": False,
                            "territories": ["WORLD"],
                            "font_file_path": None,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        unverified = deps.get_font(self.root, "Unverified Display")
        self.assertFalse(deps.font_is_clearable(unverified))

    def test_selection_hash_is_deterministic_and_prefixed(self) -> None:
        andika = deps.get_font(self.root, "Andika")
        first = deps._selection_hash(self.root, andika)
        second = deps._selection_hash(self.root, andika)
        self.assertEqual(first, second, "selection hash must be deterministic")
        self.assertTrue(first.startswith("sha256:"))
        self.assertEqual(len(first), len("sha256:") + 64)


class FontSelectionClearanceTests(unittest.TestCase):
    """select_font writes a rights record whose clearance is flag-driven."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-font-select",
            audience="senior-large-print",
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def _ledger_records(self) -> list[dict]:
        ledger = load_json(self.project_dir / "rights" / "ledger.json", {"records": []})
        return ledger.get("records", [])

    def test_verified_family_selects_as_cleared(self) -> None:
        result = deps.select_font(self.root, self.project_id, "Andika", role="body")
        self.assertEqual("cleared", result["clearance_status"])
        self.assertEqual("pass", result["status"])
        self.assertEqual("rgt-font-body-andika", result["rights_id"])
        self.assertTrue(result["asset_hash"].startswith("sha256:"))

        records = self._ledger_records()
        record = next(r for r in records if r["rights_id"] == "rgt-font-body-andika")
        self.assertEqual("font", record["asset_type"])
        self.assertEqual("open-license", record["creation_method"])
        self.assertEqual("cleared", record["clearance_status"])
        self.assertTrue(record["commercial_use"])

        # Selecting a font does not introduce an unlinked/blocked artifact: the
        # rights gate stays PASS because no font-TYPE artifact has been registered
        # yet (the .ttf is registered at build). The shift-left record simply
        # pre-clears the license.
        gate = check_rights(self.root, self.project_id)
        self.assertEqual("PASS", gate["decision"], gate)

    def test_unverified_family_selects_as_pending(self) -> None:
        local = self.root.joinpath(*deps.LOCAL_RELPATH)
        local.write_text(
            json.dumps(
                {
                    "fonts": [
                        {
                            "family": "Unverified Display",
                            "role_tags": ["display"],
                            "source": "Test foundry",
                            "license_reference": "proprietary-unknown",
                            "license_text_path": ".claude/config/licenses/OFL-1.1.md",
                            "embedding_allowed": True,
                            "commercial_use_verified": False,
                            "territories": ["WORLD"],
                            "font_file_path": None,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        result = deps.select_font(
            self.root, self.project_id, "Unverified Display", role="display"
        )
        self.assertEqual("pending", result["clearance_status"])
        self.assertEqual("pending", result["status"])

        record = next(
            r for r in self._ledger_records()
            if r["rights_id"] == "rgt-font-display-unverified-display"
        )
        self.assertEqual("pending", record["clearance_status"])
        self.assertFalse(record["commercial_use"])


if __name__ == "__main__":
    unittest.main()
