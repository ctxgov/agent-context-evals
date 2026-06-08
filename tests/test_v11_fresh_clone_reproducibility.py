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


class V11FreshCloneReproducibilityTests(unittest.TestCase):
    def test_v11_fresh_clone_receipt_gate_passes(self) -> None:
        result = run_local("scripts/check_v11_fresh_clone_receipt.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        readiness = json.loads(result.stdout)
        self.assertEqual(readiness["status"], "pass_fresh_clone_reproducibility_release_ready")
        self.assertTrue(readiness["publication_allowed"])
        self.assertFalse(readiness["public_benchmark_claim_allowed"])
        self.assertFalse(readiness["human_reviewer_claim_allowed"])
        self.assertFalse(readiness["adoption_claim_allowed"])

    def test_v11_receipt_records_public_safe_fresh_clone_run(self) -> None:
        receipt_path = ROOT / "release" / "v0.11-fresh-clone-reproducibility" / "fresh-clone-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["schema_version"], "ach-fresh-clone-reproducibility-v0.11")
        self.assertEqual(receipt["status"], "pass_fresh_clone_reproducibility")
        self.assertEqual(receipt["source_repo"], "https://github.com/ctxgov/agent-context-evals.git")
        self.assertTrue(receipt["fresh_clone"])
        self.assertFalse(receipt["worktree_reused"])
        self.assertFalse(receipt["claim_boundaries"]["public_benchmark_claim_allowed"])
        self.assertFalse(receipt["claim_boundaries"]["human_reviewer_claim_allowed"])
        self.assertFalse(receipt["claim_boundaries"]["adoption_claim_allowed"])

        commands = {entry["command"] for entry in receipt["checks"]}
        self.assertIn("python3 scripts/check_v10_saved_trace_readiness.py", commands)
        self.assertIn("python3 -m unittest discover -s tests -v", commands)
        self.assertTrue(all(entry["returncode"] == 0 for entry in receipt["checks"]))

        text = receipt_path.read_text(encoding="utf-8")
        self.assertNotIn("/Users/", text)
        self.assertNotIn("/private/tmp", text)
        self.assertNotIn("BEGIN PRIVATE KEY", text)

    def test_v11_release_notes_and_ci_are_bounded(self) -> None:
        release_notes = (ROOT / "release" / "v0.11.0.md").read_text(encoding="utf-8")
        self.assertIn("fresh-clone reproducibility", release_notes)
        self.assertIn("5-minute local run feedback request", release_notes)
        self.assertIn("No public benchmark claim", release_notes)
        self.assertIn("No human reviewer claim", release_notes)
        self.assertIn("No adoption claim", release_notes)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("check_v11_fresh_clone_receipt.py", readme)
        self.assertIn("releases/tag/v0.11.0", readme)

        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("check_v11_fresh_clone_receipt.py", ci)


if __name__ == "__main__":
    unittest.main()
