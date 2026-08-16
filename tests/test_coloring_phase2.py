from __future__ import annotations

import unittest

from common import RepoFixture, create_png

from publishing_house import coloring_bridge, coloring_review, image_gen, layout
from publishing_house.generate import generate_content
from publishing_house.rights import check_rights
from publishing_house.util import load_json


class ColoringPhase2Tests(unittest.TestCase):
    """Offline acceptance test for Phase 2: coloring line-art briefs → rendered,
    pure-B&W, printable, originality-checked interior pages.

    Never touches live project ledgers — every project lives in a disposable
    RepoFixture temp copy of the framework.
    """

    def setUp(self) -> None:
        self.fx = RepoFixture()
        self.addCleanup(self.fx.close)

    def _coloring_project(self):
        pid, pdir = self.fx.project(
            project_id="clr-phase2-clr",
            product_type="coloring-book",
            audience="kids-4-8",
            topic="Animal Friends Coloring",
        )
        generate_content(self.fx.root, pid, "line-art-brief", count=2, difficulty="easy")
        return pid, pdir

    # --- 2. bridge emits schema-valid B&W briefs + attestation sidecars --------
    def test_bridge_emits_bw_briefs_and_sidecars(self) -> None:
        pid, pdir = self._coloring_project()
        result = coloring_bridge.briefs_from_coloring(self.fx.root, pid)
        self.assertEqual("pass", result["status"], result)
        self.assertEqual(2, result["count"])
        self.assertEqual([], result["errors"])
        for i in range(2):
            brief_path = pdir / f"visuals/briefs/clr-line-art-brief-{i:03d}.json"
            sidecar_path = pdir / f"visuals/briefs/clr-line-art-brief-{i:03d}.attestation.json"
            self.assertTrue(brief_path.exists(), brief_path)
            self.assertTrue(sidecar_path.exists(), sidecar_path)
            brief = load_json(brief_path)
            self.assertIn(
                "black and white line art coloring page",
                brief["generation_prompt"]["positive"],
            )
            self.assertEqual(i + 1, brief["page_number"])
            self.assertEqual("coloring interior page", brief["purpose"])
            sidecar = load_json(sidecar_path)
            self.assertTrue(sidecar["originality_attestation"]["originals_only"])

    # --- 3. enforce_bw hard-thresholds to exactly two luminance values ---------
    def test_enforce_bw_produces_two_luminance_values(self) -> None:
        pid, pdir = self._coloring_project()
        coloring_bridge.briefs_from_coloring(self.fx.root, pid)
        rel = "visuals/assets/clr-line-art-brief-000.png"
        create_png(pdir / rel, width=2550, height=3300)  # has grey polygon
        result = image_gen.enforce_bw(self.fx.root, pid, rel)
        self.assertTrue(result["pure_bw"], result)
        self.assertEqual([0, 255], result["luminance_values"])

    # --- 4. ingest clearance is driven by the named provider -------------------
    def test_ingest_clearance_follows_provider_verification(self) -> None:
        pid, pdir = self._coloring_project()
        coloring_bridge.briefs_from_coloring(self.fx.root, pid)
        rel0 = "visuals/assets/clr-line-art-brief-000.png"
        rel1 = "visuals/assets/clr-line-art-brief-001.png"
        create_png(pdir / rel0, width=2550, height=3300)
        create_png(pdir / rel1, width=2550, height=3300)
        image_gen.enforce_bw(self.fx.root, pid, rel0)
        image_gen.enforce_bw(self.fx.root, pid, rel1)

        verified = image_gen.ingest(
            self.fx.root, pid, "clr-line-art-brief-000", rel0, "local-flux-schnell"
        )
        self.assertEqual("cleared", verified["clearance_status"])
        # An unverified provider yields pending (blocks the rights gate).
        pending = image_gen.ingest(
            self.fx.root, pid, "clr-line-art-brief-001", rel1, "adobe-firefly"
        )
        self.assertEqual("pending", pending["clearance_status"])

        # Provenance carries the originality attestation from the sidecar.
        prov = load_json(pdir / "visuals/assets/clr-line-art-brief-000.provenance.json")
        self.assertIn("originality_attestation", prov)

    # --- 5 & 6. code review pure_bw passes; cleared asset passes rights --------
    def test_review_and_rights_for_cleared_bw_asset(self) -> None:
        pid, pdir = self._coloring_project()
        coloring_bridge.briefs_from_coloring(self.fx.root, pid)
        rel = "visuals/assets/clr-line-art-brief-000.png"
        create_png(pdir / rel, width=2550, height=3300)
        image_gen.enforce_bw(self.fx.root, pid, rel)
        image_gen.ingest(self.fx.root, pid, "clr-line-art-brief-000", rel, "local-flux-schnell")

        review = coloring_review.coloring_review(self.fx.root, pid, brief_id="clr-line-art-brief-000")
        self.assertEqual(1, review["asset_count"])
        self.assertEqual(0, review["open_blockers"])  # pure_bw passes → no blocker
        asset = review["assets"][0]
        self.assertTrue(asset["pure_bw"])

        rights = check_rights(self.fx.root, pid)
        self.assertEqual("PASS", rights["decision"], rights)

    def test_review_flags_non_bw_asset_as_blocker(self) -> None:
        pid, pdir = self._coloring_project()
        coloring_bridge.briefs_from_coloring(self.fx.root, pid)
        rel = "visuals/assets/clr-line-art-brief-000.png"
        # Ingest WITHOUT thresholding → the grey polygon survives → pure_bw blocker.
        create_png(pdir / rel, width=2550, height=3300)
        image_gen.ingest(self.fx.root, pid, "clr-line-art-brief-000", rel, "local-flux-schnell")
        review = coloring_review.coloring_review(self.fx.root, pid)
        self.assertGreaterEqual(review["open_blockers"], 1)
        self.assertTrue(any(f["dimension"] == "pure_bw" for f in review["findings"]))

    # --- 7 & 8. interior places rasters with alt text; proof passes ------------
    def test_interior_places_rasters_and_proof_alt_text(self) -> None:
        pid, pdir = self._coloring_project()
        coloring_bridge.briefs_from_coloring(self.fx.root, pid)
        for i in range(2):
            rel = f"visuals/assets/clr-line-art-brief-{i:03d}.png"
            create_png(pdir / rel, width=2550, height=3300)
            image_gen.enforce_bw(self.fx.root, pid, rel)
            image_gen.ingest(self.fx.root, pid, f"clr-line-art-brief-{i:03d}", rel, "local-flux-schnell")

        layout.build_interior(self.fx.root, pid)
        page_map = load_json(pdir / "outputs/interior/page-map.json")
        self.assertGreater(page_map["raster_image_count"], 0)
        self.assertFalse(page_map["vector_only"])
        raster_pages = [p for p in page_map["pages"] if p.get("raster")]
        self.assertEqual(2, len(raster_pages))
        for p in raster_pages:
            self.assertTrue(bool(p.get("alt_text")) or p.get("decorative") is True, p)

        proof = layout.build_proof(self.fx.root, pid)
        self.assertTrue(proof["interior"]["alt_text_present"])
        self.assertFalse(proof["interior"]["vector_only"])

    # --- min stroke width is orientation-independent and speck-robust ----------
    def test_min_stroke_width_measures_true_thickness(self) -> None:
        """The distance-transform measurement reports true stroke *thickness*,
        not a horizontal run — fixing the old proxy's blind spots."""
        from PIL import Image, ImageDraw

        def measure(draw_fn, w=400, h=400):
            img = Image.new("L", (w, h), 255)
            draw_fn(ImageDraw.Draw(img))
            return coloring_review._min_stroke_width_px(img.tobytes(), w, h)

        # A long, thin HORIZONTAL bar: 6px tall, 300px long. The old horizontal-run
        # proxy read its length (~300); the real measurement reads its thickness.
        h_bar = measure(lambda d: d.rectangle([50, 100, 350, 105], fill=0))
        self.assertLessEqual(h_bar, 8, f"h-bar thickness should be ~6px, got {h_bar}")

        # A vertical bar of the same thickness measures the same (orientation-free).
        v_bar = measure(lambda d: d.rectangle([100, 50, 105, 350], fill=0))
        self.assertLessEqual(v_bar, 8, f"v-bar thickness should be ~6px, got {v_bar}")

        # A large ink blob with a single 1px speck must NOT collapse to 1px: the
        # ridge-run floor rejects the isolated speck.
        def blob_speck(d):
            d.ellipse([100, 100, 300, 300], fill=0)
            d.point((390, 10), fill=0)

        self.assertGreater(measure(blob_speck), 10)

    # --- 9. puzzle-only project stays byte-identical (fallback preserved) ------
    def test_puzzle_only_interior_stays_vector_only(self) -> None:
        pid, pdir = self.fx.project(
            project_id="clr-phase2-sud",
            product_type="puzzle-book",
            audience="senior-large-print",
            topic="Sudoku for Seniors",
        )
        generate_content(self.fx.root, pid, "sudoku", count=2, difficulty="easy")
        layout.build_interior(self.fx.root, pid)
        page_map = load_json(pdir / "outputs/interior/page-map.json")
        self.assertEqual(0, page_map["raster_image_count"])
        self.assertTrue(page_map["vector_only"])


if __name__ == "__main__":
    unittest.main()
