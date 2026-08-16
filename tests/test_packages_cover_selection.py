"""The channel packager must bundle the APPROVED art cover, not the stale one.

Regression: ``packages.py`` hard-coded ``outputs/cover/cover-wrap.pdf`` (the
procedural wrap). After a project adopts an AI-art cover (``cover-wrap-art.pdf``,
a new revision that never overwrites the procedural file), every channel package
kept shipping the old procedural cover. ``_cover_pdf`` now prefers the art wrap by
identity — NOT mtime — so re-rendering the procedural cover can never displace an
approved art cover in a package.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from publishing_house.packages import _cover_pdf


class CoverPdfSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.cover_dir = self.root / "outputs" / "cover"
        self.cover_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write(self, name: str, mtime: float | None = None) -> Path:
        p = self.cover_dir / name
        p.write_bytes(b"%PDF-1.4\n")
        if mtime is not None:
            os.utime(p, (mtime, mtime))
        return p

    def test_none_when_no_cover(self) -> None:
        self.assertIsNone(_cover_pdf(self.root))

    def test_procedural_when_only_procedural(self) -> None:
        self._write("cover-wrap.pdf")
        self.assertEqual(self.cover_dir / "cover-wrap.pdf", _cover_pdf(self.root))

    def test_prefers_art_over_procedural(self) -> None:
        self._write("cover-wrap.pdf")
        self._write("cover-wrap-art.pdf")
        self.assertEqual(self.cover_dir / "cover-wrap-art.pdf", _cover_pdf(self.root))

    def test_prefers_art_even_when_procedural_is_newer(self) -> None:
        # Art cover approved first; procedural re-rendered afterwards (newer mtime).
        self._write("cover-wrap-art.pdf", mtime=1_000)
        self._write("cover-wrap.pdf", mtime=2_000)
        self.assertEqual(
            self.cover_dir / "cover-wrap-art.pdf",
            _cover_pdf(self.root),
            "art cover must win by identity, not lose to a newer procedural mtime",
        )


if __name__ == "__main__":
    unittest.main()
