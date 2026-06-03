from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCORING = ROOT / "scoring"
if str(SCORING) not in sys.path:
    sys.path.insert(0, str(SCORING))

from score_findings import score, span_token_f1


class ScoreFindingsV02Tests(unittest.TestCase):
    def write_jsonl(self, path: Path, rows: list[dict]) -> None:
        path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )

    def test_reports_per_finding_type_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            labels = root / "labels.jsonl"
            predictions = root / "predictions.jsonl"
            self.write_jsonl(
                labels,
                [
                    {"case_id": "a", "finding_type": "stale_claim", "evidence_span": "release v0.6.3 missing", "must_flag": True},
                    {"case_id": "b", "finding_type": "conflicting_policy", "evidence_span": "network allowed and blocked", "must_flag": True},
                ],
            )
            self.write_jsonl(
                predictions,
                [
                    {"case_id": "a", "finding_type": "stale_claim", "evidence_span": "v0.6.3 missing"},
                    {"case_id": "c", "finding_type": "unsafe_action_guidance", "evidence_span": "deploy now"},
                ],
            )

            result = score(labels, predictions)

        self.assertEqual(result["per_finding_type"]["stale_claim"]["true_positive_count"], 1)
        self.assertEqual(result["per_finding_type"]["stale_claim"]["precision"], 1.0)
        self.assertEqual(result["per_finding_type"]["conflicting_policy"]["false_negative_count"], 1)
        self.assertEqual(result["per_finding_type"]["unsafe_action_guidance"]["false_positive_count"], 1)

    def test_reports_evidence_span_overlap_for_true_positives(self) -> None:
        self.assertGreater(span_token_f1("release v0.6.3 missing", "v0.6.3 missing"), 0.8)
        self.assertEqual(span_token_f1("release v0.6.3 missing", "unrelated deploy"), 0.0)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            labels = root / "labels.jsonl"
            predictions = root / "predictions.jsonl"
            self.write_jsonl(
                labels,
                [{"case_id": "a", "finding_type": "stale_claim", "evidence_span": "release v0.6.3 missing", "must_flag": True}],
            )
            self.write_jsonl(
                predictions,
                [{"case_id": "a", "finding_type": "stale_claim", "evidence_span": "v0.6.3 missing"}],
            )

            result = score(labels, predictions)

        self.assertGreater(result["evidence_span"]["mean_token_f1"], 0.8)
        self.assertEqual(result["evidence_span"]["evaluated_true_positive_count"], 1)


if __name__ == "__main__":
    unittest.main()
