# Evaluating AI-Facing Context Health Before Agent Execution

Status: technical report draft for the public v0.1 companion benchmark skeleton.

## Abstract

AI agents consume project context from README files, release notes, rules files,
memory summaries, terminal logs, issue comments, and handoff packets. When those
inputs are stale, conflicting, unsupported, unsafe, or hide prior failures, an
agent can execute against a bad premise. This draft defines a small Agent
Context Health Eval for detecting context hazards before agent execution.

## Problem

Most agent evaluation focuses on model output quality after the model acts.
CtxGov starts earlier: it asks whether the context presented to the agent was
healthy enough to trust.

## Failure Taxonomy

| Finding Type | Definition |
| --- | --- |
| `stale_claim` | A current-facing claim is contradicted by fresher evidence. |
| `conflicting_policy` | Two AI-facing instructions authorize incompatible behavior. |
| `unsupported_release_claim` | Release, package, benchmark, or compatibility copy lacks an artifact. |
| `unsafe_action_guidance` | Context encourages side effects without approval or rollback. |
| `hidden_terminal_failure` | Logs or receipts show failure while handoff copy says pass or ready. |

## Dataset Construction

The v0.1 dataset contains 50 synthetic cases:

- 44 positive cases
- 6 clean controls
- evidence spans for every positive label
- explicit `none` labels for clean controls

The synthetic set is designed to validate schema, scoring, and workflow shape.
It is not intended to estimate real-world prevalence.

## Evaluation Protocol

Each evaluator reads `data/cases.jsonl` and emits predictions with:

- `case_id`
- `finding_type`
- `evidence_span`
- `confidence`
- `source`

The scorer compares `(case_id, finding_type)` pairs and reports precision,
recall, F1, false positives, and false negatives.

## Baselines

Regex baseline:

- deterministic
- no model call
- no network call
- transparent rules
- brittle by design

LLM judge baseline:

- included as an offline no-op baseline
- not run in v0.1 because local staging forbids provider/model calls

CtxGov adapter:

- local output-contract stub in this repository
- must be replaced by real CtxGov evaluator output before public claims

## Results

The local run should report scaffold metrics for:

- regex baseline
- CtxGov adapter stub

Observed local scaffold metrics on 2026-06-03:

| Evaluator | Precision | Recall | F1 | Notes |
| --- | ---: | ---: | ---: | --- |
| regex baseline | 0.9524 | 0.9091 | 0.9302 | Transparent brittle baseline. |
| CtxGov adapter stub | 1.0000 | 1.0000 | 1.0000 | Mirrors labels to verify output contract. |

Do not quote these as public benchmark results. They are reproducibility checks
for the benchmark harness, and the adapter result is not a real evaluator
measurement.

## Error Analysis

Use the scorer output to review:

- false positives on clean controls
- missed failure-family detections
- evidence spans that are too broad
- finding-type confusion between stale and unsupported release claims
- unsafe-action findings that are actually permissioned instructions

## Limitations

This draft does not claim:

- security guarantees
- hallucination prevention
- model reliability improvement
- universal benchmark status
- provider/framework compatibility
- real-world prevalence
- adoption evidence

Before publication, the benchmark needs real trace-derived cases, a hidden
holdout, independent reviewer labels, and a reproducible data-construction
section.

## Future Work

- add a real CtxGov evaluator adapter
- add real saved workflow traces
- add hard negative controls
- replace adapter stub with actual CtxGov evaluator output
- add report rendering and demo GIF
- collect independent FP/FN reviewer notes
