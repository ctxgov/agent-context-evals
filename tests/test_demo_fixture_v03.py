from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from build_demo_fixture import build_demo_report


class DemoFixtureV03Tests(unittest.TestCase):
    def test_demo_fixture_contains_reproducible_report_and_60_second_asset(self) -> None:
        report_path = ROOT / "demo" / "reports" / "demo-context-health-report.json"
        markdown_path = ROOT / "demo" / "reports" / "demo-context-health-report.md"
        gif_path = ROOT / "demo" / "60-second-demo.gif"
        script_path = ROOT / "demo" / "60-second-demo-script.md"

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        finding_types = {finding["finding_type"] for finding in payload["findings"]}

        self.assertTrue({"conflicting_policy", "unsupported_release_claim", "hidden_terminal_failure"}.issubset(finding_types))
        self.assertIn("not a security guarantee", markdown_path.read_text(encoding="utf-8"))
        self.assertIn("00:60", script_path.read_text(encoding="utf-8"))
        self.assertTrue(gif_path.exists())
        self.assertEqual(gif_path.read_bytes()[:6], b"GIF89a")

    def test_build_demo_report_can_rebuild_fixture_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "reports"
            payload = build_demo_report(ROOT / "demo" / "fixtures" / "bad_context_repo", output_dir)

            self.assertTrue((output_dir / "demo-context-health-report.json").exists())
            self.assertTrue((output_dir / "demo-context-health-report.md").exists())
            self.assertGreaterEqual(len(payload["findings"]), 3)
            self.assertEqual(payload["fixture"], "bad_context_repo")


if __name__ == "__main__":
    unittest.main()
