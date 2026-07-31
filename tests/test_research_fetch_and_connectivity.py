"""Coverage for the quarantined research fetcher and the offline connectivity layer.

These tests never touch the network: they exercise the disabled stub, the host
allowlist, GET-only policy, the on-disk cache (seeded by hand), the connectivity
manifest write/validate/show round-trip, and a static assertion that no core
module imports a network library (the rule-18 network boundary).
"""
from __future__ import annotations

import ast
import os
import time
import unittest
from pathlib import Path

from common import SOURCE_ROOT, RepoFixture

from publishing_house import connectivity
from publishing_house.net import fetch


class _NetDisabled:
    """Context manager forcing RESEARCH_FETCH_ENABLED off (tests never egress)."""

    def __enter__(self) -> None:
        self._prev = os.environ.pop(fetch.ENABLE_FLAG, None)

    def __exit__(self, *exc: object) -> None:
        if self._prev is not None:
            os.environ[fetch.ENABLE_FLAG] = self._prev


class FetchPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_allowed_hosts_come_from_config(self) -> None:
        hosts = fetch.allowed_hosts(self.root)
        self.assertIn("www.kdpeasy.com", hosts)
        self.assertIn("html.duckduckgo.com", hosts)  # search host is allowlisted too
        self.assertNotIn("evil.example.org", hosts)

    def test_non_allowlisted_host_refused(self) -> None:
        with self.assertRaises(fetch.FetchError):
            fetch.get("https://evil.example.org/", root=self.root)

    def test_non_http_scheme_refused(self) -> None:
        with self.assertRaises(fetch.FetchError):
            fetch.get("ftp://www.kdpeasy.com/", root=self.root)

    def test_fetch_error_is_valueerror(self) -> None:
        # So the CLI's existing ValueError handler renders a clean error (exit 2).
        self.assertTrue(issubclass(fetch.FetchError, ValueError))

    def test_disabled_stub_when_network_off(self) -> None:
        with _NetDisabled():
            result = fetch.get("https://www.kdpeasy.com/", root=self.root, use_cache=False)
        self.assertTrue(result["disabled"])
        self.assertEqual(result["status"], 0)
        self.assertEqual(result["body"], "")

    def test_search_disabled_stub(self) -> None:
        with _NetDisabled():
            result = fetch.search("large print sudoku", root=self.root, use_cache=False)
        self.assertTrue(result["disabled"])
        self.assertEqual(result["results"], [])

    def test_search_rejects_unknown_engine(self) -> None:
        with self.assertRaises(fetch.FetchError):
            fetch.search("q", engine="bing", root=self.root)

    def test_probe_unknown_source_refused(self) -> None:
        with self.assertRaises(fetch.FetchError):
            fetch.probe("nosuchsource", root=self.root)

    def test_probe_disabled_reports_manual(self) -> None:
        with _NetDisabled():
            result = fetch.probe("amazon", root=self.root)
        self.assertEqual(result["best_tier"], "manual")
        self.assertEqual(result["status"], "unknown")

    def test_cache_hit_served_without_network(self) -> None:
        # Seed the cache by hand, then confirm a get() served it as tier=cache with
        # the network DISABLED (proves the cache path never needs egress).
        url = "https://www.kdpeasy.com/"
        record = {
            "status": 200, "final_url": url, "body": "<html>cached</html>",
            "truncated": False, "fetched_at": "2026-07-31T00:00:00Z",
            "_fetched_epoch": time.time(),
        }
        fetch._write_cache(self.root, url, record)  # noqa: SLF001 (test seam)
        with _NetDisabled():
            result = fetch.get(url, root=self.root, use_cache=True)
        self.assertTrue(result["from_cache"])
        self.assertEqual(result["tier"], "cache")
        self.assertEqual(result["body"], "<html>cached</html>")

    def test_stale_cache_ignored(self) -> None:
        url = "https://www.kdpeasy.com/"
        record = {
            "status": 200, "final_url": url, "body": "old",
            "_fetched_epoch": time.time() - (fetch.CACHE_TTL_SECONDS + 10),
        }
        fetch._write_cache(self.root, url, record)  # noqa: SLF001
        with _NetDisabled():
            result = fetch.get(url, root=self.root, use_cache=True)
        # Stale cache is skipped -> falls through to the disabled stub, not the body.
        self.assertTrue(result.get("disabled"))

    def test_ddg_href_decoded(self) -> None:
        wrapped = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.kdpeasy.com%2Fsudoku&rut=x"
        self.assertEqual(fetch._decode_ddg_href(wrapped), "https://www.kdpeasy.com/sudoku")  # noqa: SLF001


class ConnectivityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()
        self.root = self.fixture.root

    def tearDown(self) -> None:
        self.fixture.close()

    def test_show_absent_manifest_is_unknown_stub(self) -> None:
        result = connectivity.show_manifest(self.root)
        self.assertEqual(result["web_search_available"], "unknown")
        self.assertEqual(result["sources"], [])

    def test_probe_plan_lists_sources_offline(self) -> None:
        plan = connectivity.probe_plan(self.root)
        ids = [s["id"] for s in plan["sources"]]
        self.assertIn("kdpeasy", ids)
        self.assertIn("amazon", ids)
        # cheapest-first global order
        self.assertEqual(plan["probe_order"][0], "cache")
        self.assertEqual(plan["probe_order"][-1], "manual")

    def test_write_then_show_round_trip(self) -> None:
        payload = {
            "schema_version": "1.0",
            "web_search_available": "false",
            "http_fetch_available": "true",
            "browser_available": "false",
            "checked_at": "2026-07-31T10:00:00Z",
            "sources": [
                {"id": "kdpeasy", "host": "www.kdpeasy.com", "best_tier": "http",
                 "status": "ok", "checked_at": "2026-07-31T10:00:00Z"},
            ],
        }
        written = connectivity.write_manifest(self.root, payload)
        self.assertEqual(written["status"], "written")
        shown = connectivity.show_manifest(self.root)
        self.assertEqual(shown["http_fetch_available"], "true")
        self.assertEqual(shown["sources"][0]["best_tier"], "http")

    def test_write_rejects_invalid_enum(self) -> None:
        bad = {
            "schema_version": "1.0", "web_search_available": "maybe",
            "http_fetch_available": "true", "browser_available": "false",
            "checked_at": "x", "sources": [],
        }
        with self.assertRaises(ValueError):
            connectivity.write_manifest(self.root, bad)
        # Nothing written.
        self.assertFalse((self.root / connectivity._MANIFEST).is_file())  # noqa: SLF001

    def test_write_defaults_fill_missing_fields(self) -> None:
        written = connectivity.write_manifest(self.root, {"web_search_available": "true"})
        self.assertEqual(written["web_search_available"], "true")
        shown = connectivity.show_manifest(self.root)
        self.assertEqual(shown["http_fetch_available"], "unknown")
        self.assertEqual(shown["browser_available"], "unknown")


class NetworkBoundaryTests(unittest.TestCase):
    """Static guard: only publishing_house/net/* may import a network library."""

    _NET_LIBS = {"requests", "httpx", "urllib.request", "urllib.error", "http.client", "socket", "aiohttp"}

    def _imports(self, path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        return names

    def test_no_core_module_imports_network_lib(self) -> None:
        pkg = SOURCE_ROOT / ".claude" / "scripts" / "publishing_house"
        offenders: list[str] = []
        for path in pkg.rglob("*.py"):
            if "net" in path.relative_to(pkg).parts:
                continue  # the quarantined module is allowed
            imported = self._imports(path)
            if imported & self._NET_LIBS:
                offenders.append(f"{path.relative_to(pkg)}: {sorted(imported & self._NET_LIBS)}")
        self.assertEqual(offenders, [], f"network imports outside net/: {offenders}")


if __name__ == "__main__":
    unittest.main()
