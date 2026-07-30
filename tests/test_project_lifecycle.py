from __future__ import annotations

import unittest

from common import RepoFixture

from publishing_house.state import (
    StateTransitionError,
    allowed_transitions,
    required_gate,
    transition,
)
from publishing_house.planner import plan_next


class ProjectLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RepoFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_init_starts_in_discovery(self) -> None:
        pid, project_dir = self.fixture.project()
        self.assertTrue((project_dir / "project.yaml").is_file())
        self.assertTrue((project_dir / "state.json").is_file())
        self.assertTrue((project_dir / "events.ndjson").is_file())

    def test_allowed_transition_advances_state(self) -> None:
        pid, _ = self.fixture.project()
        result = transition(self.fixture.root, pid, "NICHE_ASSESSMENT", "test", "begin assessment")
        self.assertEqual("DISCOVERY", result["before"]["current_state"])
        self.assertEqual("NICHE_ASSESSMENT", result["after"]["current_state"])

    def test_illegal_transition_is_rejected(self) -> None:
        pid, _ = self.fixture.project()
        transition(self.fixture.root, pid, "NICHE_ASSESSMENT", "test", "begin")
        with self.assertRaises(StateTransitionError):
            transition(self.fixture.root, pid, "PUBLISHED", "test", "illegal jump")

    def test_gate_edges_are_configured(self) -> None:
        root = self.fixture.root
        self.assertEqual("niche", required_gate(root, "NICHE_APPROVAL", "PLANNING"))
        self.assertEqual("interior", required_gate(root, "INTERIOR_APPROVAL", "VISUAL_DEVELOPMENT"))
        self.assertEqual("cover", required_gate(root, "COVER_APPROVAL", "LAYOUT_AND_FORMAT_BUILD"))
        self.assertEqual("listing", required_gate(root, "LISTING_APPROVAL", "FINAL_PROOF"))
        self.assertEqual("release", required_gate(root, "RELEASE_AUTHORIZATION", "READY_FOR_SUBMISSION"))

    def test_plan_next_returns_deterministic_action(self) -> None:
        pid, _ = self.fixture.project()
        plan = plan_next(self.fixture.root, pid)
        self.assertEqual("DISCOVERY", plan["current_state"])
        self.assertIn("autonomy_action", plan)
        self.assertIn(plan["autonomy_action"], {"PROCEED", "STOP_AT_GATE", "BLOCKED", "TERMINAL"})


if __name__ == "__main__":
    unittest.main()
