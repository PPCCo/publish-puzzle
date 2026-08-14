from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import common  # noqa: F401  -- sets up sys.path for the publishing_house package

# pre_tool_policy.py lives in .claude/hooks/, which common.py does NOT add to
# sys.path. Load it directly from the repo checkout (the hook imports hooklib +
# publishing_house.util at module load; both resolve via the paths the hook sets
# up itself relative to its own location).
_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_PATH = _REPO_ROOT / ".claude" / "hooks" / "pre_tool_policy.py"


def _load_hook():
    hooks_dir = str(_HOOK_PATH.parent)
    scripts_dir = str(_REPO_ROOT / ".claude" / "scripts")
    for value in (hooks_dir, scripts_dir):
        if value not in sys.path:
            sys.path.insert(0, value)
    spec = importlib.util.spec_from_file_location("pre_tool_policy_under_test", _HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExternalVerbNetTests(unittest.TestCase):
    """The external-writes soft net (rule 11) must DENY genuine external-publish
    verbs while NOT false-positiving on the sanctioned local ph_cli.py, on flag
    NAMES that merely contain a verb (`--maximum-external-spend`), or on
    `--operation`/`--op` flag VALUES (`--operation submit`)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.hook = _load_hook()

    def _soft_net_denies(self, command: str) -> bool:
        """Reproduce exactly the soft-net decision in main() (lines ~197-200)
        using the module's own compiled regexes, without invoking stdin/main."""
        hook = self.hook
        if hook._PH_CLI_RE.search(command):
            return False
        scrubbed = hook._OPERATION_VALUE_RE.sub(" ", command)
        return bool(hook._EXTERNAL_VERB_RE.search(scrubbed))

    def _hard_denies(self, command: str) -> bool:
        import re

        return any(
            re.search(pattern, command, flags=re.IGNORECASE)
            for pattern, _ in self.hook.HARD_DENY_PATTERNS
        )

    # --- must DENY -------------------------------------------------------

    def test_marketplace_curl_post_publish_is_hard_denied(self) -> None:
        cmd = "curl -X POST https://kdp.amazon.com/api/publish -d @book.json"
        self.assertTrue(self._hard_denies(cmd))

    def test_bare_external_verb_is_soft_denied(self) -> None:
        # A genuine external verb as its own token, no sanctioned CLI present.
        self.assertTrue(self._soft_net_denies("publish ./book to gumroad"))
        self.assertTrue(self._soft_net_denies("upload cover.pdf to the store"))

    # --- must ALLOW (false positives the shift-left fix removes) ---------

    def test_ph_cli_release_authorize_is_allowed(self) -> None:
        cmd = (
            ".venv/bin/python3 .claude/scripts/ph_cli.py approval release-authorize "
            "clr-2026-x --operation submit --maximum-external-spend 0.0"
        )
        # Whitelisted local CLI -> soft net skipped entirely.
        self.assertFalse(self._soft_net_denies(cmd))
        # And it is not a marketplace hard-deny either.
        self.assertFalse(self._hard_denies(cmd))

    def test_flag_name_containing_spend_is_not_a_verb(self) -> None:
        # Non-CLI command carrying only the flag NAME must not trip the net.
        cmd = "./some-tool --maximum-external-spend 0.0 --dry-run"
        self.assertFalse(self._soft_net_denies(cmd))

    def test_operation_value_submit_is_scrubbed(self) -> None:
        cmd = "./some-tool --operation submit --report-only"
        self.assertFalse(self._soft_net_denies(cmd))

    def test_op_shortflag_value_is_scrubbed(self) -> None:
        cmd = "./some-tool --op=publish --report-only"
        self.assertFalse(self._soft_net_denies(cmd))


if __name__ == "__main__":
    unittest.main()
