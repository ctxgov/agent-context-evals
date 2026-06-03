from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "adapters"
if str(ADAPTERS) not in sys.path:
    sys.path.insert(0, str(ADAPTERS))

from offline_context_adapters import (
    agent_rules_to_case,
    ci_log_to_case,
    github_artifact_to_case,
    memory_trace_to_case,
    package_registry_manifest_to_case,
    transcript_to_case,
)


class OfflineAdaptersTests(unittest.TestCase):
    def test_github_artifact_adapter_flags_missing_release_url(self) -> None:
        case = github_artifact_to_case(
            {"repo": "ctxgov/ctxgov", "release_claim": "v0.6.3 is live", "release_url_status": 404},
            case_id="gh-1",
        )
        self.assertEqual(case["expected_finding_type"], "unsupported_release_claim")
        self.assertIn("404", case["expected_evidence_span"])

    def test_ci_log_adapter_flags_hidden_failure(self) -> None:
        case = ci_log_to_case("handoff: all checks passed\nterminal: FAILED tests/test_release.py", case_id="ci-1")
        self.assertEqual(case["expected_finding_type"], "hidden_terminal_failure")

    def test_agent_rules_adapter_flags_conflict(self) -> None:
        case = agent_rules_to_case("Network is allowed for this task.\nNo network access is allowed.", case_id="rules-1")
        self.assertEqual(case["expected_finding_type"], "conflicting_policy")

    def test_package_registry_adapter_flags_unsupported_claim(self) -> None:
        case = package_registry_manifest_to_case({"claim": "ctxgov is on PyPI", "pypi_status": "missing"}, case_id="pkg-1")
        self.assertEqual(case["expected_finding_type"], "unsupported_release_claim")

    def test_transcript_adapter_flags_stale_handoff(self) -> None:
        case = transcript_to_case("summary: release ready\nlater: release blocked pending approval", case_id="tr-1")
        self.assertEqual(case["expected_finding_type"], "stale_claim")

    def test_memory_trace_adapter_flags_missing_rollback(self) -> None:
        case = memory_trace_to_case({"memory": "promote this preference", "source_coverage": True, "rollback": None}, case_id="mem-1")
        self.assertEqual(case["expected_finding_type"], "missing_rollback")


if __name__ == "__main__":
    unittest.main()
