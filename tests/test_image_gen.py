from __future__ import annotations

import unittest

from common import RepoFixture, create_png

from publishing_house.image_gen import (
    ai_content_disclosure,
    build_guide,
    image_gen_status,
    image_generation_config,
    ingest,
    provider_registry,
)
from publishing_house.rights import check_rights
from publishing_house.util import atomic_write_json, load_json
from publishing_house.validation import validate_data


def _seed_brief(project_dir, project_id, brief_id="ill-page-001", page_number=1, with_prompt=True):
    brief = {
        "brief_id": brief_id,
        "project_id": project_id,
        "location": f"Page {page_number}",
        "page_number": page_number,
        "purpose": "Decorative sudoku-themed corner motif.",
        "scene_or_subject": "A friendly line-art pencil resting beside a grid.",
        "required_elements": ["pencil", "grid corner"],
        "composition": "Corner motif with clear white space.",
        "dimensions": {"width_px": 1024, "height_px": 1280, "dpi": 300},
        "alt_text_draft": "A line-art pencil resting beside a puzzle grid corner.",
        "rights_constraints": ["Original AI-generated artwork under a commercial license"],
        "status": "approved",
    }
    if with_prompt:
        brief["generation_prompt"] = {
            "positive": "A friendly line-art pencil beside a grid corner, clean black-and-white, coloring-book line-art style",
            "negative": "photorealistic, shading, text",
            "aspect_ratio": "4:5",
            "seed": None,
        }
    atomic_write_json(project_dir / "visuals" / "briefs" / f"{brief_id}.json", brief)
    return brief


class ImageGenConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_provider_registry_verified_flags(self) -> None:
        providers = {p["name"]: p for p in provider_registry(self.fixture.root)}
        # Local open-weight ship verified true; hosted + flux-dev ship false.
        self.assertTrue(providers["local-sdxl"]["commercial_rights_verified"])
        self.assertTrue(providers["local-flux-schnell"]["commercial_rights_verified"])
        self.assertFalse(providers["ideogram"]["commercial_rights_verified"])
        self.assertFalse(providers["adobe-firefly"]["commercial_rights_verified"])
        self.assertFalse(providers["flux-dev-local"]["commercial_rights_verified"])

    def test_status_lists_ready_briefs(self) -> None:
        project_id, project_dir = self.fixture.project()
        _seed_brief(project_dir, project_id, "ill-a", 1, with_prompt=True)
        _seed_brief(project_dir, project_id, "ill-b", 2, with_prompt=False)
        result = image_gen_status(self.fixture.root, project_id)
        self.assertEqual("manual-only", result["mode"])
        self.assertFalse(result["live_enabled"])
        self.assertIn("ill-a", result["briefs_prompt_ready"])
        self.assertIn("ill-b", result["briefs_missing_prompt"])


class ImageGenGuideTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.project_id, self.project_dir = self.fixture.project()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_build_guide_deterministic_and_complete(self) -> None:
        _seed_brief(self.project_dir, self.project_id, "ill-2", 2)
        _seed_brief(self.project_dir, self.project_id, "ill-1", 1)
        result = build_guide(self.fixture.root, self.project_id)
        self.assertEqual(2, result["entry_count"])
        guide_json = load_json(self.project_dir / "visuals" / "manual-generation-guide.json")
        # Sorted by page_number then brief_id.
        self.assertEqual(["ill-1", "ill-2"], [e["brief_id"] for e in guide_json["entries"]])
        entry = guide_json["entries"][0]
        self.assertEqual(1, entry["page_number"])
        self.assertTrue(entry["positive_prompt"])
        self.assertEqual("visuals/assets/ill-1.png", entry["save_to"])
        # The recommended provider tracks the shipped default_provider in tools.default.json
        # (derived here so the test does not go stale when the default changes).
        expected_provider = image_generation_config(self.fixture.root)["default_provider"]
        self.assertEqual(expected_provider, entry["recommended_provider"])
        self.assertIn("image-gen ingest", entry["ingest_command"])
        md = (self.project_dir / "visuals" / "manual-generation-guide.md").read_text(encoding="utf-8")
        self.assertIn("ill-1", md)
        self.assertIn("Save to", md)
        # Determinism: rebuilding yields identical entries (ignoring the stamp).
        build_guide(self.fixture.root, self.project_id)
        rebuilt = load_json(self.project_dir / "visuals" / "manual-generation-guide.json")
        self.assertEqual(guide_json["entries"], rebuilt["entries"])


class ImageGenIngestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.project_id, self.project_dir = self.fixture.project()
        _seed_brief(self.project_dir, self.project_id, "ill-page-001", 1)
        create_png(self.project_dir / "visuals" / "assets" / "ill-page-001.png", 1024, 1280)

    def tearDown(self) -> None:
        self.fixture.close()

    def test_ingest_verified_provider_yields_cleared(self) -> None:
        result = ingest(
            self.fixture.root,
            self.project_id,
            "ill-page-001",
            "visuals/assets/ill-page-001.png",
            "local-sdxl",
        )
        self.assertTrue(result["commercial_rights_verified"])
        self.assertEqual("cleared", result["clearance_status"])
        ledger = load_json(self.project_dir / "rights" / "ledger.json")
        record = ledger["records"][-1]
        self.assertTrue(record["commercial_use"])
        self.assertEqual("ai-generated", record["creation_method"])
        self.assertEqual("CreativeML Open RAIL-M", record["license_or_contract"])
        # Provenance written next to the asset.
        self.assertTrue((self.project_dir / "visuals" / "assets" / "ill-page-001.provenance.json").exists())
        # Rights gate passes for this cleared asset.
        gate = check_rights(self.fixture.root, self.project_id)
        self.assertEqual("PASS", gate["decision"], gate)

    def test_ingest_unverified_provider_yields_pending_and_blocks_gate(self) -> None:
        result = ingest(
            self.fixture.root,
            self.project_id,
            "ill-page-001",
            "visuals/assets/ill-page-001.png",
            "adobe-firefly",
        )
        self.assertFalse(result["commercial_rights_verified"])
        self.assertEqual("pending", result["clearance_status"])
        ledger = load_json(self.project_dir / "rights" / "ledger.json")
        record = ledger["records"][-1]
        self.assertFalse(record["commercial_use"])
        # A pending record blocks the rights gate.
        gate = check_rights(self.fixture.root, self.project_id)
        self.assertEqual("FAIL", gate["decision"], gate)

    def test_ingest_unknown_provider_raises(self) -> None:
        with self.assertRaises(ValueError):
            ingest(
                self.fixture.root,
                self.project_id,
                "ill-page-001",
                "visuals/assets/ill-page-001.png",
                "does-not-exist",
            )

    def test_ai_content_disclosure_reflects_ingested_image(self) -> None:
        self.assertFalse(ai_content_disclosure(self.fixture.root, self.project_id)["images"])
        ingest(
            self.fixture.root,
            self.project_id,
            "ill-page-001",
            "visuals/assets/ill-page-001.png",
            "local-sdxl",
        )
        self.assertTrue(ai_content_disclosure(self.fixture.root, self.project_id)["images"])


class IllustrationBriefBackCompatTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_existing_brief_without_new_fields_still_validates(self) -> None:
        legacy = {
            "brief_id": "ill-legacy",
            "project_id": "clr-x",
            "location": "Page 3",
            "purpose": "Legacy brief.",
            "scene_or_subject": "A scene.",
            "required_elements": ["thing"],
            "composition": "Centered.",
            "dimensions": {"width_px": 800, "height_px": 1200},
            "alt_text_draft": "A scene.",
            "rights_constraints": ["Original artwork"],
        }
        errors = validate_data(self.fixture.root, legacy, "illustration-brief.schema.json")
        self.assertEqual([], errors)

    def test_generation_prompt_requires_positive(self) -> None:
        bad = {
            "brief_id": "ill-bad",
            "project_id": "clr-x",
            "location": "Page 4",
            "purpose": "Brief.",
            "scene_or_subject": "A scene.",
            "required_elements": ["thing"],
            "composition": "Centered.",
            "dimensions": {"width_px": 800, "height_px": 1200},
            "alt_text_draft": "A scene.",
            "rights_constraints": ["Original artwork"],
            "generation_prompt": {"negative": "no text"},
        }
        errors = validate_data(self.fixture.root, bad, "illustration-brief.schema.json")
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
