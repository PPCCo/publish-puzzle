from __future__ import annotations

import json
import unittest

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

from publishing_house.gate_packet import _report_summary
from publishing_house.util import atomic_write_json


class ReportSummaryDecisionFieldTests(unittest.TestCase):
    """`_report_summary` must recognise every deterministic report's status field.

    Proof/gate reports use ``decision``/``status`` (PASS/FAIL/WARNING); the
    channel-package builder (`packages.py::_common_manifest`) records
    ``preflight_status`` (pass/warning/fail). A correctly-built package with a
    passing preflight must NOT be misread as missing (decision=None) at the
    release gate — that was a real writer/reader field mismatch.
    """

    def setUp(self) -> None:
        self.fixture = common.RepoFixture()
        self.dir = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def _write(self, name: str, data: dict) -> object:
        path = self.dir / name
        atomic_write_json(path, data)
        return path

    def test_missing_report_is_not_pass(self) -> None:
        summary = _report_summary(self.dir / "does-not-exist.json")
        self.assertFalse(summary["present"])
        self.assertIsNone(summary["decision"])

    def test_invalid_json_is_flagged(self) -> None:
        path = self.dir / "broken.json"
        path.write_text("{ not json", encoding="utf-8")
        summary = _report_summary(path)
        self.assertEqual("INVALID", summary["decision"])

    def test_reads_decision_field(self) -> None:
        path = self._write("proof.json", {"decision": "PASS"})
        self.assertEqual("PASS", _report_summary(path)["decision"])

    def test_reads_status_field(self) -> None:
        path = self._write("gate.json", {"status": "pass"})
        self.assertEqual("PASS", _report_summary(path)["decision"])

    def test_reads_preflight_status_field(self) -> None:
        # Regression: the packaging manifest's own status field must be honoured
        # so a warning-clean channel package reads as WARNING (a passing value),
        # not None (which the release packet treats as missing/failed).
        path = self._write(
            "package-manifest.json",
            {"channel": "kdp", "preflight_status": "warning", "external_write_performed": False},
        )
        self.assertEqual("WARNING", _report_summary(path)["decision"])

    def test_preflight_pass_reads_as_pass(self) -> None:
        path = self._write("package-manifest.json", {"preflight_status": "pass"})
        self.assertEqual("PASS", _report_summary(path)["decision"])

    def test_no_status_field_is_none(self) -> None:
        path = self._write("empty.json", {"channel": "kdp"})
        self.assertIsNone(_report_summary(path)["decision"])


if __name__ == "__main__":
    unittest.main()
