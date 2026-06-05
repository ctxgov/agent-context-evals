# v0.8 Blind Reviewer Protocol

Status: public local review protocol. No public benchmark claim.

## Purpose

This protocol lets an independent reviewer inspect v0.8 eval-hardening cases
without seeing owner labels. It is meant to test whether hard negatives and
self-audit cases are understandable to a reviewer before any public benchmark
or adoption claim is considered.

## What Reviewers Receive

- `review/v08-reviewer-sheet-template.csv`
- `data/v0.8/eval_hardening_cases.jsonl`
- this protocol

Reviewers should not receive `data/v0.8/eval_hardening_labels.jsonl` during the
blind pass.

## Review Steps

1. Read each `ai_context` row.
2. Decide whether the row contains an active context-health finding.
3. If yes, enter a finding type and evidence span.
4. If no, leave finding type blank and explain why the risky-looking text is
   quoted, historical, fixed, blocked, provenance-only, or explicitly negated.
5. Record uncertainty in `reviewer_notes`.

## Boundary

- No public benchmark claim.
- No security claim.
- No provider/model call.
- No adoption claim.
- No package publication claim.
- No hosted runtime or live adapter claim.
- No CLI beta claim.

The reviewer pass is review input only. It is not runtime verification,
provider verification, adoption evidence, or a dependency for using this local
artifact.
