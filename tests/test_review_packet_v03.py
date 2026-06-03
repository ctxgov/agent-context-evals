from __future__ import annotations

import csv
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class ReviewPacketV03Tests(unittest.TestCase):
    def test_review_packet_is_ready_but_does_not_claim_independent_review_complete(self) -> None:
        required_paths = [
            ROOT / "review" / "independent-review-packet.md",
            ROOT / "review" / "reviewer-rubric.md",
            ROOT / "review" / "label-adjudication-plan.md",
            ROOT / "review" / "blinded-label-sheet.csv",
            ROOT / "review" / "withheld-labels" / "README.md",
            ROOT / "data" / "v0.3" / "review_intake_cases.jsonl",
            ROOT / "data" / "v0.3" / "review_intake_manifest.json",
        ]
        for path in required_paths:
            self.assertTrue(path.exists(), str(path))

        manifest = json.loads((ROOT / "data" / "v0.3" / "review_intake_manifest.json").read_text(encoding="utf-8"))
        cases = read_jsonl(ROOT / "data" / "v0.3" / "review_intake_cases.jsonl")

        self.assertEqual(manifest["independent_review_status"], "pending")
        self.assertFalse(manifest["labels_public"])
        self.assertGreaterEqual(len(cases), 10)
        self.assertTrue(all("source_url" in case for case in cases))
        self.assertTrue(all("expected_finding_type" not in case for case in cases))

    def test_blinded_label_sheet_has_reviewer_fields_and_no_owner_labels(self) -> None:
        sheet_path = ROOT / "review" / "blinded-label-sheet.csv"
        with sheet_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertGreaterEqual(len(rows), 10)
        self.assertIn("reviewer_finding_type", rows[0])
        self.assertIn("reviewer_evidence_span", rows[0])
        self.assertNotIn("expected_finding_type", rows[0])
        self.assertTrue(all(row["case_id"].startswith("review-intake-") for row in rows))


if __name__ == "__main__":
    unittest.main()
