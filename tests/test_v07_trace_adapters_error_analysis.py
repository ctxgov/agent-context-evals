from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "adapters"
SCORING = ROOT / "scoring"
for path in [ADAPTERS, SCORING]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class V07TraceAdaptersErrorAnalysisTests(unittest.TestCase):
    def test_v07_trace_suite_has_scale_sources_labels_and_clean_controls(self) -> None:
        cases = read_jsonl(ROOT / "data" / "v0.7" / "trace_shaped_cases.jsonl")
        labels = read_jsonl(ROOT / "data" / "v0.7" / "trace_shaped_labels.jsonl")
        manifest = json.loads((ROOT / "data" / "v0.7" / "trace_shaped_manifest.json").read_text(encoding="utf-8"))

        self.assertGreaterEqual(len(cases), 90)
        self.assertEqual(len(labels), manifest["label_count"])
        self.assertEqual(len(cases), manifest["case_count"])
        self.assertEqual(manifest["schema_id"], "agent-context-evals.trace-shaped-suite/v0.7")
        self.assertTrue(all(case["split"] == "trace_shaped_v0.7" for case in cases))

        sources = {case["source"] for case in cases}
        for required in [
            "terminal_log",
            "handoff_summary",
            "agent_rules_file",
            "release_notes",
            "github_issue_pr",
            "package_registry_manifest",
            "local_transcript",
            "memory_trace",
        ]:
            self.assertIn(required, sources)

        finding_types = {label["finding_type"] for label in labels}
        for required in [
            "stale_claim",
            "conflicting_policy",
            "unsupported_release_claim",
            "unsafe_action_guidance",
            "hidden_terminal_failure",
            "missing_source_coverage",
            "missing_rollback",
            "unbounded_consequence",
            "missing_model_state_surface",
            "none",
        ]:
            self.assertIn(required, finding_types)

        clean_labels = [label for label in labels if label["finding_type"] == "none"]
        self.assertGreaterEqual(len(clean_labels), 20)
        self.assertTrue(all(label["must_flag"] is False for label in clean_labels))

        case_by_id = {case["case_id"]: case for case in cases}
        for label in labels:
            if label["finding_type"] == "none":
                continue
            self.assertIn(label["evidence_span"], case_by_id[label["case_id"]]["ai_context"])

    def test_v07_adapters_emit_normalized_local_cases(self) -> None:
        from v07_trace_adapters import (
            adapt_agent_rules_file,
            adapt_ci_terminal_log,
            adapt_github_issue_pr,
            adapt_github_release,
            adapt_local_transcript,
            adapt_package_registry_manifest,
        )

        rows = [
            adapt_github_release({"repo": "ctxgov/ctxgov", "tag": "v9.9.9", "status": 404}, case_id="v07-adapter-gh-release"),
            adapt_github_issue_pr(
                {"title": "Release ready", "body": "PR says ready but terminal log shows FAILED tests."},
                case_id="v07-adapter-gh-pr",
            ),
            adapt_ci_terminal_log("handoff says all tests passed\npytest FAILED with exit code 1", case_id="v07-adapter-ci"),
            adapt_agent_rules_file("AGENTS.md allows deploy now. CLAUDE.md says no deploy without approval.", case_id="v07-adapter-rules"),
            adapt_package_registry_manifest(
                {"package": "ctxgov", "claim": "ctxgov==9.9.9 is published", "registry_status": "missing"},
                case_id="v07-adapter-package",
            ),
            adapt_local_transcript("summary says release ready; later message says blocked pending approval", case_id="v07-adapter-transcript"),
        ]

        self.assertEqual(
            [row["expected_finding_type"] for row in rows],
            [
                "unsupported_release_claim",
                "hidden_terminal_failure",
                "hidden_terminal_failure",
                "conflicting_policy",
                "unsupported_release_claim",
                "stale_claim",
            ],
        )
        self.assertTrue(all(row["split"] == "adapter_generated_v0.7" for row in rows))
        self.assertTrue(all(row["adapter_name"].startswith("v07_") for row in rows))
        self.assertTrue(all(row["expected_evidence_span"] in row["ai_context"] for row in rows))

    def test_v07_error_analysis_reports_fp_fn_span_and_hard_negative_leakage(self) -> None:
        from error_analysis import build_error_analysis

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            labels = root / "labels.jsonl"
            predictions = root / "predictions.jsonl"
            labels.write_text(
                "\n".join(
                    json.dumps(row, sort_keys=True)
                    for row in [
                        {"case_id": "a", "finding_type": "stale_claim", "evidence_span": "release ready", "must_flag": True},
                        {"case_id": "b", "finding_type": "none", "evidence_span": "", "must_flag": False},
                        {"case_id": "c", "finding_type": "hidden_terminal_failure", "evidence_span": "FAILED tests", "must_flag": True},
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            predictions.write_text(
                "\n".join(
                    json.dumps(row, sort_keys=True)
                    for row in [
                        {"case_id": "a", "finding_type": "stale_claim", "evidence_span": "release ready"},
                        {"case_id": "b", "finding_type": "unsupported_release_claim", "evidence_span": "release"},
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_error_analysis(labels, predictions, hard_negative_case_ids={"b"})

        self.assertEqual(report["schema_id"], "agent-context-evals.error-analysis/v1")
        self.assertEqual(report["summary"]["false_positive_count"], 1)
        self.assertEqual(report["summary"]["false_negative_count"], 1)
        self.assertEqual(report["summary"]["hard_negative_leakage_count"], 1)
        self.assertEqual(report["per_finding_type"]["unsupported_release_claim"]["false_positive_count"], 1)
        self.assertEqual(report["false_positives"][0]["case_id"], "b")
        self.assertEqual(report["false_negatives"][0]["case_id"], "c")
        self.assertEqual(report["span_summary"]["evaluated_true_positive_count"], 1)

    def test_v07_reports_release_and_demo_material_are_public_ready(self) -> None:
        report = (ROOT / "reports" / "v0.7-results.md").read_text(encoding="utf-8")
        technical = (ROOT / "reports" / "technical-report.md").read_text(encoding="utf-8")
        demo = (ROOT / "demo" / "reports" / "v0.7-live-report-fixture.md").read_text(encoding="utf-8")
        release = (ROOT / "release" / "v0.7.0.md").read_text(encoding="utf-8")

        for required in [
            "v0.7 Trace-Shaped Eval Suite",
            "offline adapters",
            "automated error analysis",
            "No public benchmark claim",
        ]:
            self.assertIn(required, report)
        for required in ["GitHub PR/release/issues", "CI/terminal log", "package registry", "local transcript"]:
            self.assertIn(required, technical)
        self.assertIn("Before", demo)
        self.assertIn("After", demo)
        self.assertIn("v0.7.0", release)


if __name__ == "__main__":
    unittest.main()
