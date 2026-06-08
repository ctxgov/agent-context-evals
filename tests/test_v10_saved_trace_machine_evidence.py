from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_local(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *[str(arg) for arg in args]],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class V10SavedTraceMachineEvidenceTests(unittest.TestCase):
    def test_v10_saved_trace_dataset_has_redaction_receipt_and_hidden_holdout(self) -> None:
        result = run_local(
            "scripts/validate_cases.py",
            "--cases",
            "data/v0.10/saved_trace_cases.jsonl",
            "--labels",
            "data/v0.10/saved_trace_labels.jsonl",
            "--allow-unlabeled-split",
            "hidden_holdout",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertGreaterEqual(summary["case_count"], 30)
        self.assertGreaterEqual(summary["positive_label_count"], 16)
        self.assertGreaterEqual(summary["clean_control_count"], 8)
        self.assertGreaterEqual(summary["unlabeled_case_count"], 6)
        self.assertEqual(summary["legacy_label_field_rows"], 0)
        self.assertEqual(summary["unlabeled_splits"], ["hidden_holdout"])

        receipt = json.loads(
            (ROOT / "release" / "v0.10-machine-evidence" / "redaction-receipt.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(receipt["schema_version"], "ach-redaction-receipt-v0.10")
        self.assertEqual(receipt["source_selection"], "non_picked_saved_trace_cohort")
        self.assertGreaterEqual(receipt["public_safe_case_count"], 30)
        self.assertFalse(receipt["raw_private_trace_published"])

    def test_v10_machine_evidence_report_explains_low_baseline_scores_as_pressure(self) -> None:
        report_path = ROOT / "reports" / "v0.10-machine-evidence-report.json"
        result = run_local(
            "scripts/build_machine_evidence_report.py",
            "--cases",
            "data/v0.10/saved_trace_cases.jsonl",
            "--labels",
            "data/v0.10/saved_trace_labels.jsonl",
            "--holdout-custody",
            "release/v0.10-machine-evidence/hidden-holdout-custody.json",
            "--redaction-receipt",
            "release/v0.10-machine-evidence/redaction-receipt.json",
            "--release-version",
            "v0.10",
            "--dataset",
            "agent-context-health-v0.10-saved-trace-machine-evidence",
            "--output",
            report_path,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass_machine_evidence_public_label_scoring")
        self.assertFalse(report["public_benchmark_claim_allowed"])
        self.assertFalse(report["human_reviewer_claim_allowed"])
        self.assertIn("redaction_receipt", report)
        self.assertIn("baseline_interpretation", report)
        self.assertIn("hard-negative pressure", report["baseline_interpretation"]["low_score_interpretation"])

        markdown = (ROOT / "reports" / "v0.10-machine-evidence-report.md").read_text(encoding="utf-8")
        self.assertIn("How To Read Low Baseline Scores", markdown)
        self.assertIn("hard-negative pressure", markdown)

    def test_v10_readiness_and_ci_entrypoints_pass(self) -> None:
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("check_v10_saved_trace_readiness.py", ci)
        self.assertIn("unittest discover", ci)

        result = run_local("scripts/check_v10_saved_trace_readiness.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass_saved_trace_machine_evidence_release_ready")
        self.assertTrue(report["author_approval_recorded"])
        self.assertTrue(report["publication_allowed"])
        self.assertFalse(report["public_benchmark_claim_allowed"])
        self.assertFalse(report["human_reviewer_claim_allowed"])

    def test_five_minute_local_run_page_is_bounded(self) -> None:
        page = (ROOT / "docs" / "5-minute-local-run.md").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/check_v10_saved_trace_readiness.py", page)
        self.assertIn("No public benchmark claim", page)
        self.assertIn("No human reviewer claim", page)
        self.assertIn("No adoption claim", page)


if __name__ == "__main__":
    unittest.main()
