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


class V09MachineEvidenceReleaseTests(unittest.TestCase):
    def test_v09_dataset_allows_sealed_hidden_holdout_without_label_leakage(self) -> None:
        result = run_local(
            "scripts/validate_cases.py",
            "--cases",
            "data/v0.9/machine_evidence_cases.jsonl",
            "--labels",
            "data/v0.9/machine_evidence_labels.jsonl",
            "--allow-unlabeled-split",
            "hidden_holdout",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertGreaterEqual(summary["case_count"], 24)
        self.assertGreaterEqual(summary["positive_label_count"], 12)
        self.assertGreaterEqual(summary["clean_control_count"], 6)
        self.assertGreaterEqual(summary["unlabeled_case_count"], 4)
        self.assertEqual(summary["legacy_label_field_rows"], 0)
        self.assertEqual(summary["unlabeled_splits"], ["hidden_holdout"])

    def test_machine_evidence_report_contains_baselines_errors_and_claim_boundary(self) -> None:
        report_path = ROOT / "reports" / "v0.9-machine-evidence-report.json"
        result = run_local("scripts/build_machine_evidence_report.py", "--output", report_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "pass_machine_evidence_public_label_scoring")
        self.assertFalse(report["public_benchmark_claim_allowed"])
        self.assertFalse(report["human_reviewer_claim_allowed"])
        self.assertIn("noop_baseline", report["baselines"])
        self.assertIn("regex_baseline", report["baselines"])
        self.assertIn("ctxgov_adapter_heuristic", report["baselines"])
        self.assertIn("error_analysis", report)
        self.assertIn("holdout_custody", report)

    def test_reviewer_proxy_adjudication_fixture_is_machine_only(self) -> None:
        path = ROOT / "review" / "reviewer-proxy-adjudication.json"
        report = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(report["schema_version"], "ach-reviewer-proxy-adjudication-v0.9")
        self.assertEqual(report["reviewer_source"], "machine_proxy")
        self.assertFalse(report["human_reviewer_claim_allowed"])
        self.assertFalse(report["adoption_claim_allowed"])
        self.assertGreaterEqual(report["proxy_label_count"], 8)
        self.assertGreaterEqual(len(report["adjudicated_disagreements"]), 3)

    def test_v09_machine_evidence_readiness_gate_passes_after_author_approval(self) -> None:
        result = run_local("scripts/check_v09_machine_evidence_readiness.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass_machine_evidence_release_ready")
        self.assertTrue(report["author_approval_recorded"])
        self.assertTrue(report["publication_allowed"])
        self.assertFalse(report["public_benchmark_claim_allowed"])
        self.assertFalse(report["human_reviewer_claim_allowed"])


if __name__ == "__main__":
    unittest.main()
