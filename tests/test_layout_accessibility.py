from __future__ import annotations

import unittest

from common import RepoFixture

from publishing_house import layout
from publishing_house.accessibility import audit_accessibility
from publishing_house.generate import generate_content
from publishing_house.layout import _INTERIOR_BODY_PT
from publishing_house.util import load_json


class InteriorAccessibilityFactsTests(unittest.TestCase):
    """The interior build records the accessibility facts it actually renders,
    and the proof + accessibility audit read those measured facts rather than
    absent design hints. Regression guard for the vector-only / 11pt interior.
    """

    def setUp(self) -> None:
        self.fixture = RepoFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def _adult_digital_project(self):
        # adult-general + digital-pdf => alt_text_required is True in the audit,
        # so the vector-only designation must satisfy it (not a design hint).
        pid, path = self.fixture.project(
            project_id="clr-test-easy-sudoku",
            product_type="puzzle-book",
            audience="adult-general",
            formats=["paperback", "digital-pdf"],
            topic="Easy Sudoku for Adults",
        )
        generate_content(
            self.fixture.root, pid, "sudoku", count=4, difficulty="easy", seed=7, actor="test"
        )
        return pid, path

    def test_interior_records_measured_body_type_and_no_raster_images(self) -> None:
        pid, path = self._adult_digital_project()
        layout.build_interior(self.fixture.root, pid)
        page_map = load_json(path / "outputs" / "interior" / "page-map.json")
        # The build records what it drew, single-sourced from the draw constant.
        self.assertEqual(_INTERIOR_BODY_PT, page_map["min_body_type_pt"])
        self.assertEqual(0, page_map["raster_image_count"])
        self.assertTrue(page_map["vector_only"])

    def test_proof_reflects_measured_facts(self) -> None:
        pid, path = self._adult_digital_project()
        layout.build_interior(self.fixture.root, pid)
        proof = layout.build_proof(self.fixture.root, pid)
        interior = proof["interior"]
        self.assertEqual(_INTERIOR_BODY_PT, interior["min_type_pt"])
        # Vector-only interior with zero raster images satisfies alt-text.
        self.assertTrue(interior["alt_text_present"])
        self.assertTrue(interior["vector_only"])
        self.assertEqual(0, interior["raster_image_count"])

    def test_accessibility_audit_passes_for_vector_only_adult_digital(self) -> None:
        pid, _ = self._adult_digital_project()
        layout.build_interior(self.fixture.root, pid)
        layout.build_proof(self.fixture.root, pid)
        result = audit_accessibility(self.fixture.root, pid)
        self.assertEqual("PASS", result["decision"], result)
        self.assertTrue(result["checks"]["type_size"], result)
        self.assertTrue(result["checks"]["alt_text"], result)
        self.assertEqual([], result["issues"], result)

    def test_audit_fails_closed_without_a_built_proof(self) -> None:
        # No interior build/proof => no measured facts => never a silent pass.
        pid, _ = self._adult_digital_project()
        result = audit_accessibility(self.fixture.root, pid)
        self.assertNotEqual("PASS", result["decision"], result)


if __name__ == "__main__":
    unittest.main()
