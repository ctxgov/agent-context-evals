from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCORING = ROOT / "scoring"
if str(SCORING) not in sys.path:
    sys.path.insert(0, str(SCORING))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class V08EvalHardeningTests(unittest.TestCase):
    def test_v08_suite_has_hard_negatives_and_self_audit_cases(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.8" / "eval_hardening_cases.jsonl")
        labels = read_jsonl(ROOT / "data" / "v0.8" / "eval_hardening_labels.jsonl")
        manifest = json.loads((ROOT / "data" / "v0.8" / "eval_hardening_manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_id"], "agent-context-evals.eval-hardening-suite/v0.8")
        self.assertEqual(len(cases), 54)
        self.assertEqual(len(labels), 54)
        self.assertEqual(manifest["hard_negative_count"], 50)
        self.assertEqual(manifest["self_audit_case_count"], 4)
        self.assertEqual(manifest["independent_review_status"], "pending")
        self.assertFalse(manifest["reviewer_packet_labels_public"])
        self.assertTrue(all(value is False for value in manifest["claim_boundary"].values()))

        labels_by_id = {label["case_id"]: label for label in labels}
        for case in cases:
            label = labels_by_id[case["case_id"]]
            self.assertEqual(case["split"], "eval_hardening_v0.8")
            if case["benchmark_family"] == "eval_hardening_hard_negative":
                self.assertEqual(label["finding_type"], "none")
                self.assertFalse(label["must_flag"])
            if case["benchmark_family"] == "self_audit_public_release":
                self.assertTrue(label["must_flag"])
                self.assertIn(label["evidence_span"], case["ai_context"])

        finding_types = {label["finding_type"] for label in labels}
        for required in [
            "publication_state_drift",
            "repo_map_drift",
            "version_surface_drift",
            "roadmap_pointer_drift",
        ]:
            self.assertIn(required, finding_types)

    def test_v08_reviewer_sheet_is_blind(self) -> None:
        with (ROOT / "review" / "v08-reviewer-sheet-template.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 54)
        forbidden = {
            "expected_finding_type",
            "expected_finding_types",
            "expected_evidence_span",
            "finding_type",
            "must_flag",
            "hard_negative",
        }
        self.assertTrue(rows)
        self.assertFalse(forbidden & set(rows[0].keys()))
        for required in ["case_id", "ai_context", "reviewer_finding_type", "reviewer_evidence_span", "reviewer_notes"]:
            self.assertIn(required, rows[0])

    def test_v08_reviewer_packet_checker_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_v08_reviewer_packet.py"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["issue_count"], 0)

    def test_v08_regex_baseline_leaks_on_hard_negatives(self) -> None:
        from score_multilabel import score_multilabel

        predictions = ROOT / "reports" / "v0.8-regex-hardening-results.jsonl"
        if predictions.exists():
            report = score_multilabel(ROOT / "data" / "v0.8" / "eval_hardening_labels.jsonl", predictions)
            self.assertGreater(report["case_level"]["false_positive_count"], 0)
            self.assertEqual(report["expected_positive_case_count"], 4)
            self.assertGreaterEqual(report["case_level"]["true_negative_count"], 1)

    def test_v08_release_materials_keep_boundary(self) -> None:
        for path in [
            ROOT / "README.md",
            ROOT / "reports" / "v0.8-results.md",
            ROOT / "release" / "v0.8.0.md",
            ROOT / "review" / "v08-reviewer-protocol.md",
            ROOT / "review" / "v08-adjudication-log-template.md",
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("No public benchmark claim", text)
            self.assertIn("No provider/model call", text)
            self.assertIn("No adoption claim", text)


if __name__ == "__main__":
    unittest.main()
