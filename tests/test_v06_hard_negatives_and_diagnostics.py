from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "baselines"
SCORING = ROOT / "scoring"
for path in [BASELINES, SCORING]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from regex_baseline import predict_all
from span_diagnostics import build_span_diagnostics


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class V06HardNegativesAndDiagnosticsTests(unittest.TestCase):
    def write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

    def test_v06_adversarial_hard_negatives_have_scale_and_no_expected_findings(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.6" / "adversarial_hard_negative_cases.jsonl")
        labels = read_jsonl(ROOT / "data" / "v0.6" / "adversarial_hard_negative_labels.jsonl")

        self.assertGreaterEqual(len(cases), 60)
        self.assertEqual(len(cases), len(labels))
        self.assertTrue(all(case["case_id"].startswith("adv-hard-negative-") for case in cases))
        self.assertTrue(all(case["split"] == "adversarial_hard_negative_v0.6" for case in cases))
        self.assertTrue(all(case["expected_finding_types"] == [] for case in cases))
        self.assertTrue(all(label["finding_type"] == "none" and label["must_flag"] is False for label in labels))

        joined = "\n".join(case["ai_context"].lower() for case in cases)
        for term in ("release", "404", "failed", "rollback", "schema", "memory", "approval"):
            self.assertIn(term, joined)

    def test_regex_baseline_does_not_flag_v06_adversarial_hard_negatives(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.6" / "adversarial_hard_negative_cases.jsonl")

        false_positives = [prediction for case in cases for prediction in predict_all(case)]

        self.assertEqual(false_positives, [])

    def test_v06_hard_negative_result_files_are_empty(self) -> None:
        regex_rows = read_jsonl(ROOT / "reports" / "v0.6-regex-hard-negative-results.jsonl")
        doctor_rows = read_jsonl(ROOT / "reports" / "v0.6-ctxgov-doctor-hard-negative-results.jsonl")

        self.assertEqual(regex_rows, [])
        self.assertEqual(doctor_rows, [])

    def test_span_diagnostics_reports_distribution_and_near_misses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            labels = root / "labels.jsonl"
            predictions = root / "predictions.jsonl"
            self.write_jsonl(
                labels,
                [
                    {"case_id": "a", "finding_type": "stale_claim", "evidence_span": "release is ready", "must_flag": True},
                    {"case_id": "b", "finding_type": "hidden_terminal_failure", "evidence_span": "FAILED tests after handoff says passed", "must_flag": True},
                    {"case_id": "c", "finding_type": "none", "evidence_span": "n/a", "must_flag": False},
                ],
            )
            self.write_jsonl(
                predictions,
                [
                    {"case_id": "a", "finding_type": "stale_claim", "evidence_span": "release is ready"},
                    {"case_id": "b", "finding_type": "hidden_terminal_failure", "evidence_span": "FAILED tests"},
                    {"case_id": "c", "finding_type": "unsupported_release_claim", "evidence_span": "release"},
                ],
            )

            diagnostics = build_span_diagnostics(labels, predictions)

        self.assertEqual(diagnostics["schema_id"], "agent-context-evals.span-diagnostics/v1")
        self.assertEqual(diagnostics["true_positive_count"], 2)
        self.assertEqual(diagnostics["false_positive_count"], 1)
        self.assertEqual(diagnostics["mean_token_f1"], 0.75)
        self.assertEqual(diagnostics["min_token_f1"], 0.5)
        self.assertEqual(diagnostics["max_token_f1"], 1.0)
        self.assertEqual(diagnostics["bucket_counts"]["exact"], 1)
        self.assertEqual(diagnostics["bucket_counts"]["partial"], 1)
        self.assertEqual(diagnostics["near_misses"][0]["case_id"], "b")


if __name__ == "__main__":
    unittest.main()
