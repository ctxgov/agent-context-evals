from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "baselines"
if str(BASELINES) not in sys.path:
    sys.path.insert(0, str(BASELINES))

from llm_judge_baseline import build_prompt, run_offline_judge


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class LlmJudgeBaselineV03Tests(unittest.TestCase):
    def write_cases(self, path: Path) -> None:
        rows = [
            {
                "case_id": "judge-case-001",
                "split": "review_intake",
                "source": "public_release_note",
                "ai_context": "README says release v0.8.0 is public, but the release URL returned 404.",
                "expected_finding_type": "unsupported_release_claim",
                "expected_evidence_span": "release URL returned 404",
            },
            {
                "case_id": "judge-case-002",
                "split": "review_intake",
                "source": "handoff_log",
                "ai_context": "Terminal: FAILED tests after handoff says passed.",
                "expected_finding_type": "hidden_terminal_failure",
                "expected_evidence_span": "FAILED tests after handoff says passed",
            },
        ]
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")

    def test_default_run_writes_prompts_manifest_and_no_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = root / "cases.jsonl"
            output = root / "predictions.jsonl"
            manifest = root / "manifest.json"
            prompts = root / "prompts.jsonl"
            self.write_cases(cases)

            result = run_offline_judge(cases, output, manifest, prompts)

            predictions = read_jsonl(output)
            prompt_rows = read_jsonl(prompts)
            manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))

        self.assertEqual(predictions, [])
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(manifest_payload["case_count"], 2)
        self.assertEqual(manifest_payload["provider"], "disabled")
        self.assertFalse(manifest_payload["side_effects"]["provider_or_model_call_performed"])
        self.assertEqual(len(prompt_rows), 2)
        self.assertIn("Return one JSON object", prompt_rows[0]["prompt"])
        self.assertNotIn("expected_finding_type", prompt_rows[0]["prompt"])
        self.assertNotIn("expected_evidence_span", prompt_rows[0]["prompt"])

    def test_build_prompt_uses_taxonomy_without_exposing_labels(self) -> None:
        prompt = build_prompt(
            {
                "case_id": "label-case",
                "source": "fixture",
                "ai_context": "This case is clean.",
                "expected_finding_type": "stale_claim",
                "expected_evidence_span": "trap",
            }
        )

        self.assertIn("stale_claim", prompt)
        self.assertIn("This case is clean.", prompt)
        self.assertNotIn("expected_finding_type", prompt)
        self.assertNotIn("trap", prompt)

    def test_review_decisions_are_validated_and_written_as_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = root / "cases.jsonl"
            output = root / "predictions.jsonl"
            manifest = root / "manifest.json"
            prompts = root / "prompts.jsonl"
            decisions = root / "decisions.jsonl"
            self.write_cases(cases)
            decisions.write_text(
                json.dumps(
                    {
                        "case_id": "judge-case-001",
                        "finding_type": "unsupported_release_claim",
                        "evidence_span": "release URL returned 404",
                        "confidence": 0.72,
                        "rationale": "The public release claim is contradicted by a 404 artifact check.",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            result = run_offline_judge(cases, output, manifest, prompts, review_decisions=decisions)
            predictions = read_jsonl(output)

        self.assertEqual(result["offline_decision_count"], 1)
        self.assertEqual(predictions[0]["case_id"], "judge-case-001")
        self.assertEqual(predictions[0]["finding_type"], "unsupported_release_claim")
        self.assertEqual(predictions[0]["source"], "llm_judge_baseline_offline_decisions")

    def test_rejects_review_decision_for_unknown_case(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = root / "cases.jsonl"
            output = root / "predictions.jsonl"
            manifest = root / "manifest.json"
            prompts = root / "prompts.jsonl"
            decisions = root / "decisions.jsonl"
            self.write_cases(cases)
            decisions.write_text(
                json.dumps({"case_id": "missing", "finding_type": "stale_claim", "evidence_span": "anything"}) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                run_offline_judge(cases, output, manifest, prompts, review_decisions=decisions)


if __name__ == "__main__":
    unittest.main()
