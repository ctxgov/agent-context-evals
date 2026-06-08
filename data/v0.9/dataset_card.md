# Agent Context Health v0.9 Machine Evidence

Status: public machine-evidence release with author approval recorded. This is
not external reviewer evidence, adoption evidence, package release evidence,
provider compatibility evidence, or a live benchmark result.

The v0.9 data expands v0.8 with more hard negatives, more benign controls, and
a sealed hidden holdout split. Public cases are author-labeled fixture cases.
Hidden holdout cases are included only as unlabeled cases with a custody
receipt; their labels are not published here.

Local use:

```bash
python3 scripts/validate_cases.py --cases data/v0.9/machine_evidence_cases.jsonl --labels data/v0.9/machine_evidence_labels.jsonl --allow-unlabeled-split hidden_holdout
python3 scripts/build_machine_evidence_report.py --output reports/v0.9-machine-evidence-report.json
python3 scripts/check_v09_machine_evidence_readiness.py
```

Claim boundary:

- no human reviewer claim
- no adoption claim
- no security guarantee
- no provider/model compatibility claim
- no package release claim
- no public benchmark result claim

The intended release shape is a machine-evidence release that says what local
gates pass while keeping external review and adoption claims blocked until
those forms of evidence exist.
