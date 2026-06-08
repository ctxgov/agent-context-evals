# v0.10 Saved-Trace Machine Evidence Design

Status: public machine-evidence design. Author approval was recorded for the
bounded v0.10 publication.

v0.10 adds a public-safe saved-trace cohort on top of v0.9. The goal is to move
from synthetic release-material cases toward redacted dogfood trace shape while
keeping the claim ceiling unchanged.

## What Changed

- Deterministic non-picked saved-trace cohort.
- Redaction receipt for source selection and public-safe transformation.
- Sealed hidden holdout custody.
- Error-analysis report that explains low transparent-baseline scores as
  hard-negative pressure.
- GitHub Actions CI for local evidence gates.
- 5-minute local run page.

## What This Can Support

- Local evidence-shape review.
- Regression checks for scorer, claims, hidden holdout leakage, and no-network
  behavior.
- A clearer public path for maintainers to inspect the artifact.

## What This Still Cannot Support

- No public benchmark claim.
- No human reviewer claim.
- No adoption claim.
- No security claim.
- No provider/model compatibility claim.
- No package release claim.

## Release Gate

```bash
python3 scripts/check_v10_saved_trace_readiness.py
```

Expected status:

```text
pass_saved_trace_machine_evidence_release_ready
```
