# Author Approval Packet: v0.9 Machine Evidence

Status: author approval recorded for the bounded v0.9 machine-evidence
publication.

Approved bounded action:

```text
Publish v0.9 machine-evidence release materials that describe local hard
negatives, benign controls, hidden holdout custody, baseline scoring, and error
analysis. Do not add benchmark, security, adoption, provider, package, stable
protocol, or human reviewer claims.
```

Before approval, verify:

- `make v09-ready` passes locally.
- `reports/v0.9-machine-evidence-report.json` has
  `pass_machine_evidence_public_label_scoring`.
- `release/v0.9-machine-evidence/hidden-holdout-custody.json` keeps hidden
  labels sealed.
- `review/reviewer-proxy-adjudication.json` says `machine_proxy` and does not
  claim human review.

Still blocked after this approval:

- public benchmark result claims
- external adoption claims
- independent reviewer claims
- no security guarantee claim
- provider/model compatibility claims
- package or hosted runtime release claims
