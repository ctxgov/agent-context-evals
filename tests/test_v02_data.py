from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class V02DataTests(unittest.TestCase):
    def test_trace_pattern_cases_have_50_labeled_rows_and_required_families(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.2" / "trace_pattern_cases.jsonl")
        labels = read_jsonl(ROOT / "data" / "v0.2" / "trace_pattern_labels.jsonl")
        families = json.loads((ROOT / "data" / "v0.2" / "benchmark_families.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(cases), 50)
        self.assertEqual(len(cases), len(labels))
        self.assertTrue(all(case["case_id"].startswith("trace-") for case in cases))
        self.assertTrue(all("benchmark_family" in case for case in cases))
        self.assertTrue(all(label["evidence_span"] for label in labels if label["finding_type"] != "none"))

        required = {
            "memory_xray_l1_eval",
            "release_integrity_claim_lint_eval",
            "session_continuity_hidden_holdout_eval",
            "task_shard_context_control_eval",
        }
        self.assertTrue(required.issubset(set(families["families"])))
        finding_types = {label["finding_type"] for label in labels}
        self.assertTrue(
            {
                "missing_source_coverage",
                "missing_rollback",
                "unbounded_consequence",
                "missing_model_state_surface",
            }.issubset(finding_types)
        )

    def test_hidden_holdout_cases_withhold_labels(self) -> None:
        holdout = read_jsonl(ROOT / "data" / "v0.2" / "hidden_holdout_cases.jsonl")
        manifest = json.loads((ROOT / "data" / "v0.2" / "hidden_holdout_manifest.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(holdout), 12)
        self.assertTrue(all(case["split"] == "hidden_holdout" for case in holdout))
        self.assertTrue(all("expected_finding_type" not in case for case in holdout))
        self.assertEqual(manifest["labels_public"], False)


if __name__ == "__main__":
    unittest.main()
