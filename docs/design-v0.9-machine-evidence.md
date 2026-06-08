# v0.9 Machine Evidence Design

Status: public release design. Author approval was recorded for the bounded
v0.9 machine-evidence publication.

v0.9 is designed for the current constraint: no independent human reviewer is
available. Local benchmark-style checks can replace some engineering readiness
judgment, but they cannot replace external adoption or independent review
evidence.

## What Machine Evidence Can Decide

- Case and label files are structurally valid.
- Public cases do not contain label-helper fields.
- Hidden holdout cases can exist without public labels.
- Default scoring does not use hidden labels.
- Baseline and scaffold evaluator outputs are reproducible offline.
- Error analysis is generated from the same scorer for every baseline.
- Release copy keeps the bounded claim shape.

## What Machine Evidence Cannot Decide

- Whether external OSS maintainers find the tool useful.
- Whether downstream users adopt it.
- Whether a provider/model integration is compatible.
- Whether the package or hosted runtime is released.
- Whether security properties hold in real deployments.
- Whether the benchmark is representative of broad real-world usage.

## Release Shape

The bounded public shape after author approval is:

```text
v0.9 is a machine-evidence release candidate for Agent Context Health:
expanded fixture cases, sealed hidden holdout custody, local scoring, and
error-analysis artifacts. It is not a human-reviewed benchmark or adoption
claim.
```

The readiness gate must return:

```text
pass_machine_evidence_release_ready
```

That status means the public materials pass the bounded machine-evidence gate.
It does not permit broader benchmark, adoption, provider, package, security, or
human-reviewer claims.

## Human Work Still Required

Author approval was required for this bounded v0.9 machine-evidence release.
Independent reviewer notes remain optional future evidence and must not be
claimed until they exist.
