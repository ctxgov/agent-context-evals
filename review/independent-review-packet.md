# Independent Review Packet

Status: v0.3 review-ready packet. Independent review is pending.

This packet prepares public trace-derived intake material for third-party
labeling. It does not claim that labels have been independently reviewed.

## Contents

- `data/v0.3/review_intake_cases.jsonl`: blinded intake cases with public source URLs.
- `review/blinded-label-sheet.csv`: reviewer worksheet with blank label fields.
- `review/reviewer-rubric.md`: finding taxonomy and evidence-span rules.
- `review/label-adjudication-plan.md`: merge process for two reviewers and one adjudicator.
- `review/withheld-labels/README.md`: explains why owner labels are not committed.

## Reviewer Task

For each case:

1. Read `ai_context` and, when useful, inspect `source_url`.
2. Choose one `reviewer_finding_type`.
3. Copy a minimal exact `reviewer_evidence_span` from `ai_context`.
4. Use `none` only when no listed hazard is present.
5. Add a short note when the case is ambiguous or multi-label.

## Completion Standard

The review is complete only when:

- at least two independent reviewers label every case
- disagreements are adjudicated and recorded
- owner labels remain hidden until after reviewer submission
- precision, recall, F1, and evidence-span overlap are recomputed on the adjudicated labels

Until then, these cases are review-ready material, not benchmark evidence.
