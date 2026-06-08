# v0.9 Machine Evidence Release Candidate

Status: public bounded machine-evidence release. Author approval was recorded
for this publication.

This release candidate replaces the blocked human-review lane with machine
evidence where that is valid: larger hard-negative coverage, benign controls,
sealed hidden holdout custody, local baseline scoring, and error analysis. It
does not replace human evidence for external adoption, independent review, or
field validation.

Run:

```bash
make v09-ready
```

Expected gate status:

```text
pass_machine_evidence_release_ready
```

Claim boundary:

- no human reviewer claim
- no adoption claim
- no security guarantee
- no provider/model compatibility claim
- no package release claim
- no public benchmark result claim
- no publication without author approval

Allowed public positioning:

```text
CtxGov Agent Context Health v0.9 is a machine-evidence release candidate:
local fixture data, sealed hidden holdout custody, local scoring, and bounded
release-material checks. It is not external reviewer or adoption evidence.
```
