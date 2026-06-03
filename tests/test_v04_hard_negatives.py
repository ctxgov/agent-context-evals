from __future__ import annotations

import json
from pathlib import Path
import unittest

from baselines.regex_baseline import predict


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class V04HardNegativeTests(unittest.TestCase):
    def test_hard_negative_split_has_benign_context_hazard_vocabulary(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.4" / "hard_negative_cases.jsonl")
        labels = read_jsonl(ROOT / "data" / "v0.4" / "hard_negative_labels.jsonl")

        self.assertGreaterEqual(len(cases), 20)
        self.assertEqual(len(cases), len(labels))
        self.assertTrue(all(case["case_id"].startswith("hard-negative-") for case in cases))
        self.assertTrue(all(case["split"] == "hard_negative" for case in cases))
        self.assertTrue(all(label["finding_type"] == "none" for label in labels))
        self.assertTrue(all(label["must_flag"] is False for label in labels))

        joined = "\n".join(case["ai_context"].lower() for case in cases)
        for term in ("release", "404", "failed", "rollback", "schema", "memory", "approval"):
            self.assertIn(term, joined)

    def test_regex_baseline_does_not_flag_v04_hard_negatives(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.4" / "hard_negative_cases.jsonl")

        false_positives = [prediction for case in cases if (prediction := predict(case)) is not None]

        self.assertEqual(false_positives, [])


if __name__ == "__main__":
    unittest.main()
