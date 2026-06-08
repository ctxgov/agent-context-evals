# v0.10 Saved-Trace Machine Evidence

Status: public bounded machine-evidence release. Author approval was recorded
for this publication.

v0.10 adds redacted dogfood saved-trace fixtures, redaction receipt, hidden
holdout custody, CI gates, and a 5-minute local run path.

Run:

```bash
python3 scripts/check_v10_saved_trace_readiness.py
```

Expected gate status:

```text
pass_saved_trace_machine_evidence_release_ready
```

Claim boundary:

- No public benchmark claim.
- No security claim.
- No provider/model call.
- No adoption claim.
- No human reviewer claim.
- No package publication claim.
- No hosted runtime or live adapter claim.

This release publishes local machine evidence only. It does not execute
provider/model calls, network fetches, package publication, hosted runtime
changes, target writes, reviewer outreach, or adoption measurement.
