from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "ctxgov_adapter"
if str(ADAPTER) not in sys.path:
    sys.path.insert(0, str(ADAPTER))

from run_ctxgov import (
    map_ctxgov_finding,
    materialize_case_workspace,
    predict_heuristic,
    prediction_from_ctxgov_finding,
    select_ctxgov_predictions,
)


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
        self.assertEqual(map_ctxgov_finding("release_link_404"), "unsupported_release_claim")
        self.assertEqual(map_ctxgov_finding("package_registry_unverified"), "unsupported_release_claim")
        self.assertEqual(map_ctxgov_finding("release_artifact_missing"), "unsupported_release_claim")
        self.assertEqual(map_ctxgov_finding("memory_missing_source_coverage"), "missing_source_coverage")
        self.assertEqual(map_ctxgov_finding("memory_missing_rollback"), "missing_rollback")
        self.assertEqual(map_ctxgov_finding("memory_unbounded_consequence"), "unbounded_consequence")
        self.assertEqual(map_ctxgov_finding("memory_missing_model_state_surface"), "missing_model_state_surface")
        self.assertEqual(map_ctxgov_finding("task_shard_schema_conflict"), "conflicting_policy")
        self.assertEqual(map_ctxgov_finding("task_shard_unapproved_side_effect"), "unsafe_action_guidance")
        self.assertEqual(map_ctxgov_finding("task_shard_missing_rollback"), "missing_rollback")
        self.assertIsNone(map_ctxgov_finding("duplicated_rule"))

    def test_prediction_from_ctxgov_finding_prefers_exact_evidence_span(self) -> None:
        prediction = prediction_from_ctxgov_finding(
            "case-001",
            {
                "finding_type": "release_link_404",
                "evidence_span": "release URL returned 404",
                "reason": "Release copy points at a release URL that returned 404.",
            },
        )

        self.assertIsNotNone(prediction)
        self.assertEqual(prediction["finding_type"], "unsupported_release_claim")
        self.assertEqual(prediction["evidence_span"], "release URL returned 404")
        self.assertEqual(prediction["ctxgov_finding_type"], "release_link_404")

    def test_selects_single_label_projection_for_trace_pattern_families_without_labels(self) -> None:
        release_case = {"case_id": "release-1", "benchmark_family": "release_integrity_claim_lint_eval"}
        release_predictions = [
            {
                "case_id": "release-1",
                "finding_type": "unsupported_release_claim",
                "ctxgov_finding_type": "release_link_404",
                "evidence_span": "release URL returned 404",
            },
            {
                "case_id": "release-1",
                "finding_type": "unsafe_action_guidance",
                "ctxgov_finding_type": "action_or_publication_without_evidence",
                "evidence_span": "generic publication language",
            },
        ]

        selected_release = select_ctxgov_predictions(release_case, release_predictions)

        self.assertEqual([row["finding_type"] for row in selected_release], ["unsupported_release_claim"])

        task_case = {"case_id": "task-1", "benchmark_family": "task_shard_context_control_eval"}
        task_predictions = [
            {
                "case_id": "task-1",
                "finding_type": "unsafe_action_guidance",
                "ctxgov_finding_type": "task_shard_unapproved_side_effect",
                "evidence_span": "apply shard without approval",
            },
            {
                "case_id": "task-1",
                "finding_type": "missing_rollback",
                "ctxgov_finding_type": "task_shard_missing_rollback",
                "evidence_span": "without approval or rollback",
            },
        ]

        selected_task = select_ctxgov_predictions(task_case, task_predictions)

        self.assertEqual([row["finding_type"] for row in selected_task], ["unsafe_action_guidance"])

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
