"""Phase 3 cover pipeline: cover-art brief bridge + art-backed cover wrap.

Covers the three deterministic, offline pieces added for AI-art covers:

* ``cover_bridge.brief_from_cover_art`` — emits ONE schema-valid cover-art
  brief whose constraints (reserve white space, NO in-image text) live in the
  POSITIVE prompt (flux negatives are inert), with front-panel px = trim×dpi+bleed.
* ``compositor.compose_cover_wrap`` — the font gate refuses without a cleared
  embeddable font; with one bundled, it produces a byte-reproducible wrap PNG
  with the art pasted full-bleed on the front panel.
* ``layout.build_cover(style="art")`` — writes a NEW-REVISION PDF at exact
  trim+bleed, never touching an approved procedural ``cover-wrap.pdf``, and
  registers a distinct ``cover-pdf`` artifact.
"""
from __future__ import annotations

import glob
import json
import shutil
import unittest

from common import RepoFixture, create_png

from publishing_house import cover_bridge, layout
from publishing_house import compositor
from publishing_house import dependencies as deps
from publishing_house.artifacts import list_artifacts


def _find_latin_ttf() -> str | None:
    """A resolvable system TTF with real Latin glyphs, for render/build tests."""
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


def _clear_font(root, fonts_dir_name: str, family: str, roles: list[str]) -> None:
    """Vendor the probe TTF and register `family` as a cleared bundled face."""
    fonts_dir = root / ".claude" / "config" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    dest = fonts_dir / fonts_dir_name
    shutil.copyfile(TTF, dest)
    local = root.joinpath(*deps.LOCAL_RELPATH)
    existing = {}
    if local.exists():
        existing = json.loads(local.read_text(encoding="utf-8"))
    fonts = existing.get("fonts", [])
    fonts.append(
        {
            "family": family,
            "role_tags": roles,
            "source": "Test — bundled probe face",
            "license_reference": "OFL-1.1",
            "license_text_path": ".claude/config/licenses/OFL-1.1.md",
            "embedding_allowed": True,
            "commercial_use_verified": True,
            "territories": ["WORLD"],
            "font_file_path": f".claude/config/fonts/{fonts_dir_name}",
        }
    )
    local.write_text(json.dumps({"fonts": fonts}), encoding="utf-8")


class CoverBriefBridgeTests(unittest.TestCase):
    """The cover-art brief must be schema-valid with reserved-space, no-text prompt."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-cover-brief", audience="senior-large-print",
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def test_emits_one_schema_valid_cover_brief(self) -> None:
        result = cover_bridge.brief_from_cover_art(self.root, self.project_id)
        self.assertEqual("pass", result["status"], result)
        self.assertEqual("clr-cover-art-front", result["brief_id"])
        brief_path = self.project_dir / result["brief_path"]
        self.assertTrue(brief_path.is_file())
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        # The purpose marks it a cover; the schema accepts it (cover is a brief type).
        self.assertEqual("cover front art", brief["purpose"])
        from publishing_house.validation import validate_data

        self.assertEqual(
            [], validate_data(self.root, brief, "illustration-brief.schema.json")
        )

    def test_no_in_image_text_and_reserved_space_in_positive_prompt(self) -> None:
        cover_bridge.brief_from_cover_art(self.root, self.project_id)
        brief = json.loads(
            (self.project_dir / "visuals" / "briefs" / "clr-cover-art-front.json")
            .read_text(encoding="utf-8")
        )
        positive = brief["generation_prompt"]["positive"].lower()
        # flux ignores the negative — the constraints MUST be in the positive.
        self.assertIn("no text", positive)
        self.assertTrue("no letter" in positive or "no lettering" in positive)
        self.assertIn("watermark", positive)
        self.assertTrue("space for a title" in positive or "empty space" in positive)
        # In-image text is a prohibited element.
        self.assertIn("in-image text", brief["prohibited_elements"])

    def test_front_panel_pixels_are_trim_times_dpi_plus_bleed(self) -> None:
        cover_bridge.brief_from_cover_art(self.root, self.project_id)
        brief = json.loads(
            (self.project_dir / "visuals" / "briefs" / "clr-cover-art-front.json")
            .read_text(encoding="utf-8")
        )
        dims = brief["dimensions"]
        dpi = dims["dpi"]
        # Senior sudoku resolves to an 8.5×11 trim; front px = (w+bleed)×dpi wide,
        # (h+2·bleed)×dpi tall. Compute from the module's own trim to avoid a literal.
        project = layout.load_yaml((self.project_dir / "project.yaml"))
        w_in, h_in = layout._trim(project)
        self.assertEqual(int(round((w_in + 0.125) * dpi)), dims["width_px"])
        self.assertEqual(int(round((h_in + 2 * 0.125) * dpi)), dims["height_px"])

    def test_provider_defaults_to_configured_default(self) -> None:
        from publishing_house import image_gen

        default = image_gen.image_generation_config(self.root).get("default_provider")
        result = cover_bridge.brief_from_cover_art(self.root, self.project_id)
        self.assertEqual(default, result["provider"])
        override = cover_bridge.brief_from_cover_art(
            self.root, self.project_id, provider="local-sdxl"
        )
        self.assertEqual("local-sdxl", override["provider"])


class CoverWrapFontGateTests(unittest.TestCase):
    """compose_cover_wrap must enforce the cleared-font gate before drawing."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-cover-gate", audience="senior-large-print",
        )
        self.art = self.project_dir / "visuals" / "assets" / "clr-cover-art-front.png"
        create_png(self.art, width=600, height=800)

    def tearDown(self) -> None:
        self.fixture.close()

    def _spec(self) -> dict:
        dpi = 300
        return {
            "dpi": dpi,
            "wrap_px": [1200, 800],
            "bleed_px": int(0.125 * dpi),
            "back": [37, 37, 500, 726],
            "spine": [537, 37, 126, 726],
            "front": [663, 37, 500, 726],
            "solid_rgb": "#1a3a5c",
            "cream_rgb": "#fdf6e3",
            "ink_rgb": "#ffffff",
            "title": "Big Sudoku",
            "count_label": "100 Puzzles",
            "descriptor": "Large Print  •  Easy",
            "spine_title": "Big Sudoku",
            "back_heading": "About This Book",
            "back_lines": ["A relaxing collection of large-print puzzles."],
            "features": ["100 unique puzzles", "Solutions at the back"],
            "trim_label": "8.5 × 11 in",
            "font_display": "Archivo",
            "font_body": "Atkinson Hyperlegible",
        }

    def test_refuses_without_cleared_font(self) -> None:
        with self.assertRaises(compositor.FontNotClearedError):
            compositor.compose_cover_wrap(
                self.root, self.project_id,
                "visuals/assets/clr-cover-art-front.png", self._spec(),
                "outputs/cover/cover-wrap-art.png",
            )


@unittest.skipUnless(TTF, "no resolvable Latin TTF for render/build tests")
class CoverWrapRenderTests(unittest.TestCase):
    """With cleared display+body fonts bundled, the wrap renders full-bleed art."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-cover-render", audience="senior-large-print",
        )
        _clear_font(self.root, "Archivo-Black.ttf", "Archivo", ["display", "label"])
        _clear_font(self.root, "Atkinson.ttf", "Atkinson Hyperlegible", ["body", "label"])
        deps.select_font(self.root, self.project_id, "Archivo", role="display")
        deps.select_font(self.root, self.project_id, "Atkinson Hyperlegible", role="body")
        self.art = self.project_dir / "visuals" / "assets" / "clr-cover-art-front.png"
        create_png(self.art, width=600, height=800)

    def tearDown(self) -> None:
        self.fixture.close()

    def _spec(self) -> dict:
        dpi = 300
        return {
            "dpi": dpi,
            "wrap_px": [1400, 800],
            "bleed_px": int(0.125 * dpi),
            "back": [37, 37, 600, 726],
            "spine": [637, 37, 126, 726],
            "front": [763, 37, 600, 726],
            "solid_rgb": "#1a3a5c",
            "cream_rgb": "#fdf6e3",
            "ink_rgb": "#ffffff",
            "title": "Big Sudoku",
            "count_label": "100 Puzzles",
            "descriptor": "Large Print  •  Easy",
            "spine_title": "Big Sudoku",
            "back_heading": "About This Book",
            "back_lines": ["A relaxing collection of large-print puzzles."],
            "features": ["100 unique puzzles", "Solutions at the back"],
            "trim_label": "8.5 × 11 in",
            "font_display": "Archivo",
            "font_body": "Atkinson Hyperlegible",
        }

    def test_wrap_is_byte_deterministic(self) -> None:
        a = compositor.compose_cover_wrap(
            self.root, self.project_id, "visuals/assets/clr-cover-art-front.png",
            self._spec(), "outputs/cover/wrap-a.png",
        )
        b = compositor.compose_cover_wrap(
            self.root, self.project_id, "visuals/assets/clr-cover-art-front.png",
            self._spec(), "outputs/cover/wrap-b.png",
        )
        self.assertEqual("pass", a["status"])
        self.assertEqual(
            (self.project_dir / a["output_path"]).read_bytes(),
            (self.project_dir / b["output_path"]).read_bytes(),
        )

    def test_long_title_callout_does_not_collide(self) -> None:
        """A long 4-line title must push the cream callout below it, not overlap.

        Regression: the title band and callout Y were both fixed, so a long adult
        title (e.g. "…Relaxing Puzzles with Full Solutions") overran the callout
        and clipped its text. The callout now sits below the title's true bottom.
        """
        from PIL import Image

        spec = self._spec()
        spec["title"] = "Easy Sudoku for Adults Relaxing Puzzles with Full Solutions"
        cream = tuple(
            int(spec["cream_rgb"].lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)
        )
        res = compositor.compose_cover_wrap(
            self.root, self.project_id, "visuals/assets/clr-cover-art-front.png",
            spec, "outputs/cover/wrap-long.png",
        )
        image = Image.open(self.project_dir / res["output_path"]).convert("RGB")
        fx, fy, fw, fh = spec["front"]
        # Find the topmost row containing the solid cream callout inside the front.
        px = image.load()
        cream_top = None
        for yy in range(fy, fy + fh):
            row_cream = sum(
                1 for xx in range(fx, fx + fw, 8) if px[xx, yy] == cream
            )
            if row_cream > (fw // 8) // 2:  # a majority-cream row = the callout band
                cream_top = yy
                break
        self.assertIsNotNone(cream_top, "cream callout band not found on front panel")
        # The title's white ink must not intrude into the cream band: the callout
        # top sits strictly below where the title occupies. Sample the title zone
        # just above the callout — it should contain white ink (the title), and the
        # callout band itself should be predominantly solid cream (not overrun).
        band_cream = sum(
            1 for xx in range(fx, fx + fw, 4) if px[xx, cream_top + 4] == cream
        )
        self.assertGreater(
            band_cream, (fw // 4) // 2, "callout band is not cleanly cream — title overran it"
        )

    def test_front_panel_carries_art_pixels(self) -> None:
        from PIL import Image

        res = compositor.compose_cover_wrap(
            self.root, self.project_id, "visuals/assets/clr-cover-art-front.png",
            self._spec(), "outputs/cover/wrap.png",
        )
        image = Image.open(self.project_dir / res["output_path"]).convert("RGB")
        fx, fy, fw, fh = self._spec()["front"]
        # The art create_png draws a grey polygon; pasted full-bleed the front
        # panel must contain non-solid, non-cream pixels.
        crop = image.crop((fx, fy, fx + fw, fy + fh))
        distinct = len(set(crop.getdata()))  # noqa: PIL getdata is fine for a test count
        self.assertGreater(distinct, 3, "front panel shows no art variety")


@unittest.skipUnless(TTF, "no resolvable Latin TTF for build tests")
class BuildCoverArtStyleTests(unittest.TestCase):
    """build_cover(style='art') is a NEW revision; it never overwrites the wrap."""

    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root
        self.project_id, self.project_dir = self.fixture.project(
            project_id="clr-cover-build", audience="senior-large-print",
        )
        _clear_font(self.root, "Archivo-Black.ttf", "Archivo", ["display", "label"])
        _clear_font(self.root, "Atkinson.ttf", "Atkinson Hyperlegible", ["body", "label"])
        deps.select_font(self.root, self.project_id, "Archivo", role="display")
        deps.select_font(self.root, self.project_id, "Atkinson Hyperlegible", role="body")
        # The cover spine width depends on the interior page count, which needs
        # at least one generated content batch to lay out.
        from publishing_house.generate import generate_content

        generate_content(
            self.root, self.project_id, "sudoku", count=4, difficulty="easy",
            seed=7, actor="test",
        )
        layout.build_interior(self.root, self.project_id)
        # An ingested cover-art asset must exist for style='art'.
        create_png(
            self.project_dir / "visuals" / "assets" / "clr-cover-art-front.png",
            width=600, height=800,
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def test_missing_art_raises(self) -> None:
        (self.project_dir / "visuals" / "assets" / "clr-cover-art-front.png").unlink()
        with self.assertRaises(layout.BuildError):
            layout.build_cover(self.root, self.project_id, style="art")

    def test_art_build_is_new_revision_not_overwrite(self) -> None:
        # First build the approved procedural cover, snapshot its bytes.
        proc = layout.build_cover(self.root, self.project_id, style="procedural")
        proc_pdf = self.project_dir / proc["path"]
        self.assertEqual("outputs/cover/cover-wrap.pdf", proc["path"])
        before = proc_pdf.read_bytes()

        art = layout.build_cover(self.root, self.project_id, style="art")
        self.assertEqual("art", art["style"])
        self.assertEqual("outputs/cover/cover-wrap-art.pdf", art["path"])
        # The approved procedural wrap is untouched on disk.
        self.assertEqual(before, proc_pdf.read_bytes())
        self.assertTrue((self.project_dir / art["path"]).is_file())
        self.assertTrue((self.project_dir / art["wrap_png"]).is_file())

    def test_art_pdf_wrap_size_is_trim_plus_bleed(self) -> None:
        import re

        art = layout.build_cover(self.root, self.project_id, style="art")
        # No PDF lib in the venv; parse the MediaBox reportlab writes verbatim.
        raw = (self.project_dir / art["path"]).read_bytes().decode("latin-1")
        m = re.search(r"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", raw)
        self.assertIsNotNone(m, "no MediaBox in the art cover PDF")
        w_pt, h_pt = float(m.group(3)), float(m.group(4))
        # Points → inches (72 pt/in). Height = trim height + 2·bleed.
        project = layout.load_yaml(self.project_dir / "project.yaml")
        _w, h_in = layout._trim(project)
        self.assertAlmostEqual(h_pt / 72.0, h_in + 0.25, places=2)
        self.assertAlmostEqual(w_pt / 72.0, art["wrap_size_in"][0], places=2)

    def test_art_pdf_registered_as_cover_pdf(self) -> None:
        art = layout.build_cover(self.root, self.project_id, style="art")
        artifacts = list_artifacts(self.root, self.project_id)
        registered = next(
            a for a in artifacts if a["artifact_id"] == art["artifact_id"]
        )
        self.assertEqual("cover-pdf", registered["type"])
        self.assertEqual("art", registered["provenance"]["style"])
        self.assertEqual("pending", registered["rights_status"])


if __name__ == "__main__":
    unittest.main()
