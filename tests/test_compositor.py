from __future__ import annotations

import glob
import json
import shutil
import unittest

from common import RepoFixture, create_png

from publishing_house import compositor
from publishing_house import dependencies as deps
from publishing_house.artifacts import list_artifacts


def _find_latin_ttf() -> str | None:
    """A resolvable system TTF with real Latin glyphs, for rendering tests only.

    The SHIPPED compositor renders with the cleared repo font; tests just need
    *a* real TTF to prove pixels get drawn. Skip gracefully if none is found.
    """
    from PIL import Image, ImageDraw, ImageFont

    candidates = (
        glob.glob("/System/Library/Fonts/Supplemental/*.ttf")
        + glob.glob("/System/Library/Fonts/*.ttf")
        + glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
        + glob.glob("/Library/Fonts/*.ttf")
    )
    probe = Image.new("RGB", (200, 80), "white")
    draw = ImageDraw.Draw(probe)
    for path in sorted(candidates):
        try:
            font = ImageFont.truetype(path, 40)
            bbox = draw.textbbox((0, 0), "Ab", font=font)
            if (bbox[2] - bbox[0]) > 5:
                return path
        except Exception:  # noqa: BLE001
            continue
    return None


TTF = _find_latin_ttf()


class CompositorFontGateTests(unittest.TestCase):
    """The font gate must be enforced before any caption is drawn."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-composite",
            audience="senior-large-print",
        )
        # A single component to place.
        self.component = self.project_dir / "visuals" / "assets" / "comp-a.png"
        create_png(self.component, width=300, height=300)

    def tearDown(self) -> None:
        self.fixture.close()

    def _spec(self, with_caption: bool) -> dict:
        spec = {
            "schema_version": "1.0",
            "brief_id": "brief-test-panel",
            "canvas": {"width": 400, "height": 400, "background": "#FFFFFF"},
            "components": [
                {
                    "id": "a",
                    "source_brief_id": None,
                    "source_artifact_id": None,
                    "asset_path": "visuals/assets/comp-a.png",
                    "box": [50, 50, 200, 200],
                    "fit": "contain",
                }
            ],
            "captions": [],
        }
        if with_caption:
            spec["captions"] = [
                {
                    "text": "sudoku",
                    "box": [20, 300, 360, 60],
                    "align": "center",
                    "font_role": "label",
                    "max_pt": 40,
                    "min_pt": 10,
                    "colour": "#1A1A1A",
                }
            ]
        return spec

    def test_spec_validates_against_schema(self) -> None:
        from publishing_house.validation import validate_data

        errors = validate_data(self.root, self._spec(True), compositor.SPEC_SCHEMA)
        self.assertEqual([], errors, errors)

    def test_compose_without_captions_needs_no_font(self) -> None:
        # A caption-free composite must succeed even with no cleared font: the
        # gate only fires when real text must be drawn.
        result = compositor.compose(
            self.root, self.project_id, self._spec(False),
            "visuals/assets/brief-test-panel.png",
        )
        self.assertEqual("pass", result["status"])
        self.assertTrue((self.project_dir / result["output_path"]).is_file())

    def test_compose_with_caption_refuses_without_cleared_font(self) -> None:
        # No font selected AND no cleared record -> refuse. This is the font
        # dependency being enforced, not bypassed.
        with self.assertRaises(compositor.FontNotClearedError):
            compositor.compose(
                self.root, self.project_id, self._spec(True),
                "visuals/assets/brief-test-panel.png",
            )

    def test_compose_with_caption_refuses_when_cleared_but_file_missing(self) -> None:
        # A font can be license-cleared by select_font yet have a null
        # font_file_path (license cleared at selection, .ttf not yet bundled) ->
        # the gate still refuses ("license cleared, file not bundled"). The
        # shipped registry now bundles the default families, so we assert this
        # gate against a local-override family whose font_file_path is null.
        local = self.root.joinpath(*deps.LOCAL_RELPATH)
        local.write_text(
            json.dumps(
                {
                    "fonts": [
                        {
                            "family": "Unbundled Test Face",
                            "role_tags": ["label"],
                            "source": "Test — no bundled file",
                            "license_reference": "OFL-1.1",
                            "license_text_path": ".claude/config/licenses/OFL-1.1.md",
                            "embedding_allowed": True,
                            "commercial_use_verified": True,
                            "territories": ["WORLD"],
                            "font_file_path": None,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        deps.select_font(self.root, self.project_id, "Unbundled Test Face", role="label")
        with self.assertRaises(compositor.FontNotClearedError) as ctx:
            compositor.compose(
                self.root, self.project_id,
                self._spec(True) | {"font_family": "Unbundled Test Face"},
                "visuals/assets/brief-test-panel.png",
            )
        self.assertIn("font FILE", str(ctx.exception))


@unittest.skipUnless(TTF, "no resolvable Latin TTF on this machine for render tests")
class CompositorRenderTests(unittest.TestCase):
    """End-to-end render once a cleared font FILE resolves (bundled-font path)."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-composite-render",
            audience="senior-large-print",
        )
        # Vendor a real TTF into the fixture repo and point the registry at it,
        # mirroring the shipped "bundle the cleared .ttf under .claude/config/fonts/"
        # flow. We reuse Andika's registry entry but give it a real file path.
        fonts_dir = self.root / ".claude" / "config" / "fonts"
        fonts_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TTF, fonts_dir / "Andika-Regular.ttf")
        local = self.root.joinpath(*deps.LOCAL_RELPATH)
        local.write_text(
            json.dumps(
                {
                    "fonts": [
                        {
                            "family": "Andika",
                            "role_tags": ["body", "label", "display"],
                            "source": "SIL Global",
                            "license_reference": "OFL-1.1",
                            "license_text_path": ".claude/config/licenses/OFL-1.1.md",
                            "embedding_allowed": True,
                            "commercial_use_verified": True,
                            "territories": ["WORLD"],
                            "font_file_path": ".claude/config/fonts/Andika-Regular.ttf",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        deps.select_font(self.root, self.project_id, "Andika", role="label")

        self.component = self.project_dir / "visuals" / "assets" / "comp-a.png"
        create_png(self.component, width=300, height=300)

    def tearDown(self) -> None:
        self.fixture.close()

    def _spec(self) -> dict:
        return {
            "schema_version": "1.0",
            "brief_id": "brief-test-panel",
            "canvas": {"width": 400, "height": 400, "background": "#FFFFFF"},
            "components": [
                {
                    "id": "a",
                    "source_brief_id": None,
                    "source_artifact_id": None,
                    "asset_path": "visuals/assets/comp-a.png",
                    "box": [50, 50, 200, 200],
                    "fit": "contain",
                }
            ],
            "captions": [
                {
                    "text": "sudoku",
                    "box": [20, 300, 360, 60],
                    "align": "center",
                    "font_role": "label",
                    "max_pt": 40,
                    "min_pt": 10,
                    "colour": "#1A1A1A",
                }
            ],
        }

    def test_resolve_cleared_font_returns_bundled_file(self) -> None:
        family, path = compositor.resolve_cleared_font(self.root, self.project_id)
        self.assertEqual("Andika", family)
        self.assertTrue(path.is_file())

    def test_compose_is_byte_deterministic(self) -> None:
        out1 = "visuals/assets/panel-1.png"
        out2 = "visuals/assets/panel-2.png"
        compositor.compose(self.root, self.project_id, self._spec(), out1)
        compositor.compose(self.root, self.project_id, self._spec(), out2)
        b1 = (self.project_dir / out1).read_bytes()
        b2 = (self.project_dir / out2).read_bytes()
        self.assertEqual(b1, b2, "same spec + inputs must produce byte-identical PNG")

    def test_caption_draws_real_pixels(self) -> None:
        from PIL import Image

        out = "visuals/assets/panel.png"
        compositor.compose(self.root, self.project_id, self._spec(), out)
        image = Image.open(self.project_dir / out).convert("RGB")
        # Inspect the caption box region for non-background (dark) pixels.
        crop = image.crop((20, 300, 380, 360))
        dark = sum(
            1 for px in crop.getdata()
            if px[0] < 120 and px[1] < 120 and px[2] < 120
        )
        self.assertGreater(dark, 0, "caption text drew no visible pixels")

    def test_component_lands_inside_its_box(self) -> None:
        from PIL import Image

        out = "visuals/assets/panel.png"
        compositor.compose(self.root, self.project_id, self._spec(), out)
        image = Image.open(self.project_dir / out).convert("RGB")
        # create_png draws a grey polygon on white; the component box is
        # [50,50,200,200]. There must be non-white pixels inside it and the
        # canvas corners (outside any box) must remain background white.
        inside = image.crop((50, 50, 250, 250))
        non_white_inside = sum(1 for px in inside.getdata() if px != (255, 255, 255))
        self.assertGreater(non_white_inside, 0)
        self.assertEqual((255, 255, 255), image.getpixel((5, 5)))

    def test_composite_ingest_records_component_provenance(self) -> None:
        # Register a component artifact so it has an id to thread through.
        from publishing_house.artifacts import register_artifact

        comp_artifact = register_artifact(
            self.root, self.project_id, "visuals/assets/comp-a.png",
            "illustration", "VISUAL_DEVELOPMENT", "test", rights_status="cleared",
        )
        spec = self._spec()
        spec["components"][0]["source_artifact_id"] = comp_artifact["artifact_id"]
        spec_path = self.project_dir / "visuals" / "composite-specs" / "brief-test-panel.compose.json"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(spec), encoding="utf-8")

        out = "visuals/assets/brief-test-panel.png"
        compositor.compose(self.root, self.project_id, spec, out)
        result = compositor.composite_ingest(
            self.root, self.project_id, "brief-test-panel", out,
            source_artifact_ids=None,  # read from spec
            spec_path="visuals/composite-specs/brief-test-panel.compose.json",
        )
        self.assertEqual("cleared", result["clearance_status"])
        self.assertIn(comp_artifact["artifact_id"], result["source_artifact_ids"])

        # The registered composite carries the component id in source_artifact_ids.
        artifacts = list_artifacts(self.root, self.project_id)
        composite = next(a for a in artifacts if a["artifact_id"] == result["artifact_id"])
        self.assertIn(comp_artifact["artifact_id"], composite["source_artifact_ids"])
        self.assertEqual("deterministic-composite", composite["provenance"]["creation_method"])


class MatteEdgeWhiteTests(unittest.TestCase):
    """The edge-matte helper de-whites a component's ground but keeps interior whites."""

    def _img(self):
        from PIL import Image

        # 20x20 white; a dark 8x8 ring with a WHITE interior hole in the middle,
        # so the interior white is enclosed by dark and unreachable from the edge.
        img = Image.new("RGB", (20, 20), (255, 255, 255))
        px = img.load()
        for x in range(6, 14):
            for y in range(6, 14):
                px[x, y] = (10, 10, 10)  # dark object block
        for x in range(8, 12):
            for y in range(8, 12):
                px[x, y] = (255, 255, 255)  # white hole INSIDE the object
        return img, px

    def test_edge_white_becomes_fill_interior_white_preserved(self) -> None:
        img, _ = self._img()
        fill = (251, 247, 239)  # canvas cream
        out = compositor._matte_edge_white(img, fill, 235)
        opx = out.load()
        # A corner (edge-connected white ground) is repainted to the fill.
        self.assertEqual(fill, opx[0, 0])
        self.assertEqual(fill, opx[19, 19])
        # The dark object is untouched.
        self.assertEqual((10, 10, 10), opx[6, 6])
        # The enclosed interior white hole is PRESERVED (not reachable from edge).
        self.assertEqual((255, 255, 255), opx[9, 9])

    def test_matte_is_deterministic(self) -> None:
        img1, _ = self._img()
        img2, _ = self._img()
        fill = (251, 247, 239)
        a = compositor._matte_edge_white(img1, fill, 235)
        b = compositor._matte_edge_white(img2, fill, 235)
        self.assertEqual(list(a.getdata()), list(b.getdata()))


if __name__ == "__main__":
    unittest.main()
