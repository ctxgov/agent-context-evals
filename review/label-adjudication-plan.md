# Label Adjudication Plan

Status: v0.3 public process note.

## Roles

- Reviewer A labels the blinded sheet without seeing owner labels.
- Reviewer B independently labels the same sheet.
- Adjudicator resolves disagreements after both submissions are frozen.

## Process

1. Copy `review/blinded-label-sheet.csv` for each reviewer.
2. Reviewers fill `reviewer_finding_type`, `reviewer_evidence_span`,
   `reviewer_confidence`, `reviewer_id`, and `reviewer_notes`.
3. Compare reviewer labels by `case_id`.
4. Mark agreement when finding type and evidence span materially match.
5. For disagreement, adjudicator records final finding type, final evidence
   span, and the reason for resolving the case.
6. Only after adjudication, compare final labels against any owner draft labels.
7. Re-run scorer outputs for regex, CtxGov adapter, and offline LLM judge
   decisions.

## Publication Gate

A public benchmark claim remains blocked until the adjudicated label file,
reviewer agreement summary, scorer outputs, false positive analysis, and false
negative analysis are all published.
