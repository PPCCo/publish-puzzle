from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from common import SOURCE_ROOT

from publishing_house.validation import validate_framework

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

HUMAN_ONLY_SKILLS = {
    "product-approve-niche",
    "product-approve-interior",
    "product-approve-cover",
    "product-approve-compliance",
    "product-approve-listing",
    "product-release-authorize",
    "product-submit",
    "product-incident",
}


class FrameworkStructureTests(unittest.TestCase):
    def test_framework_validator_passes(self) -> None:
        result = validate_framework(SOURCE_ROOT)
        self.assertEqual("pass", result["status"], result)
        self.assertEqual([], result["errors"])

    def test_agent_frontmatter_has_required_fields(self) -> None:
        agents = [
            p
            for p in (SOURCE_ROOT / ".claude" / "agents").rglob("*.md")
            if p.name not in {"README.md", "CATALOG.md"}
        ]
        self.assertGreaterEqual(len(agents), 34)
        for path in agents:
            text = path.read_text(encoding="utf-8")
            self.assertIsNotNone(FRONTMATTER.match(text), path.as_posix())

    def test_human_only_gate_skills_disable_model_invocation(self) -> None:
        for name in HUMAN_ONLY_SKILLS:
            text = (SOURCE_ROOT / ".claude" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("disable-model-invocation: true", text, name)

    def test_external_writes_are_disabled(self) -> None:
        settings = json.loads((SOURCE_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual("disabled", settings["env"]["PUBLISHING_EXTERNAL_WRITES"])
        self.assertEqual("1", settings["env"]["CLAUDE_CODE_MCP_ALLOWLIST_ENV"])
        mcp = json.loads((SOURCE_ROOT / ".mcp.json").read_text(encoding="utf-8"))
        server = mcp["mcpServers"]["publishing-house"]
        self.assertEqual("disabled", server["env"]["PUBLISHING_EXTERNAL_WRITES"])
        self.assertTrue(any("${CLAUDE_PROJECT_DIR:-.}" in value for value in server["args"]))

    def test_bounded_autonomous_run_skill_exists(self) -> None:
        text = (SOURCE_ROOT / ".claude" / "skills" / "product-run" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("--until", text)
        self.assertIn("Never invoke human-only", text)
        self.assertNotIn("disable-model-invocation: true", text)

    def test_dynamic_workflows_have_meta_and_agent_calls(self) -> None:
        workflows = list((SOURCE_ROOT / ".claude" / "workflows").glob("*.js"))
        self.assertGreaterEqual(len(workflows), 12)
        for path in workflows:
            text = path.read_text(encoding="utf-8")
            self.assertIn("export const meta", text, path.as_posix())
            self.assertIn("agent(", text, path.as_posix())

    def test_required_framework_boundaries_exist(self) -> None:
        required = [
            ".claude/CLAUDE.md",
            ".claude/settings.json",
            ".claude/config/workflow_states.json",
            ".claude/config/quality_gates.json",
            ".claude/hooks/pre_tool_policy.py",
            ".claude/scripts/ph_cli.py",
            ".claude/mcp/publishing_house_server.py",
            ".mcp.json",
        ]
        for relative in required:
            self.assertTrue((SOURCE_ROOT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
