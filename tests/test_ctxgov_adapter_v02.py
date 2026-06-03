from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ctxgov_adapter"
if str(ADAPTER) not in sys.path:
    sys.path.insert(0, str(ADAPTER))

from run_ctxgov import map_ctxgov_finding, materialize_case_workspace, predict_heuristic


class CtxGovAdapterV02Tests(unittest.TestCase):
    def test_heuristic_adapter_does_not_mirror_expected_label(self) -> None:
        case = {
            "case_id": "clean-with-label-trap",
            "ai_context": "This is a clean handoff with no release, policy, action, or terminal failure.",
            "expected_finding_type": "stale_claim",
            "expected_evidence_span": "trap span",
        }

        self.assertIsNone(predict_heuristic(case))

    def test_maps_ctxgov_doctor_finding_types_to_eval_taxonomy(self) -> None:
        self.assertEqual(map_ctxgov_finding("terminal_failure_hidden"), "hidden_terminal_failure")
        self.assertEqual(map_ctxgov_finding("conflicting_instruction"), "conflicting_policy")
        self.assertEqual(map_ctxgov_finding("unsupported_claim"), "unsupported_release_claim")
        self.assertEqual(map_ctxgov_finding("action_or_publication_without_evidence"), "unsafe_action_guidance")
        self.assertIsNone(map_ctxgov_finding("duplicated_rule"))

    def test_materializes_case_as_local_repo_fixture(self) -> None:
        case = {
            "case_id": "repo-case",
            "source": "AGENTS.md + terminal.log",
            "ai_context": "AGENTS.md: deploy now without approval. terminal.log: FAILED tests.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = materialize_case_workspace(case, Path(tmp))

            self.assertTrue((path / "AGENTS.md").exists())
            self.assertTrue((path / "logs" / "terminal.log").exists())
            self.assertIn("deploy now", (path / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
