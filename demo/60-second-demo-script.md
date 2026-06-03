# 60-Second Demo Script

00:00 - Open the bad context fixture and show the README ready claim.

00:10 - Show `AGENTS.md` with conflicting release policy and unsafe push guidance.

00:20 - Show the release check and terminal log evidence: `404 Not Found` and `FAILED tests after handoff says passed`.

00:35 - Run the demo report builder:

```bash
python3 scripts/build_demo_fixture.py --fixture demo/fixtures/bad_context_repo --output-dir demo/reports
```

00:45 - Open `demo/reports/demo-context-health-report.md` and highlight unsupported release, conflicting policy, hidden terminal failure, unsafe action guidance, and Memory X-Ray L1 gaps.

00:60 - Close on the limitations line: demo fixture only, not a security guarantee or public benchmark claim.
