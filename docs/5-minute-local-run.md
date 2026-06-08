# 5-Minute Local Run

Status: public local machine-evidence path. No public benchmark claim.

Run:

```bash
python3 scripts/check_v10_saved_trace_readiness.py
```

Then inspect:

- `reports/v0.10-machine-evidence-report.md`
- `release/v0.10-machine-evidence/redaction-receipt.json`
- `release/v0.10-machine-evidence/hidden-holdout-custody.json`

Read the result this way:

- `pass_saved_trace_machine_evidence_release_ready` means local files, labels,
  redaction receipt, hidden holdout custody, report generation, claim lint, and
  no-network checks passed.
- Low transparent-baseline scores are hard-negative pressure and
  error-analysis signal, not public benchmark performance.
- Hidden holdout labels are not published and are not used for public scoring.

Boundaries:

- No public benchmark claim.
- No human reviewer claim.
- No adoption claim.
- No security claim.
- No provider/model compatibility claim.
- No package release claim.

The path is meant to let a maintainer or framework author inspect the evidence
shape quickly without needing provider/model calls, package installation, or
external services.
