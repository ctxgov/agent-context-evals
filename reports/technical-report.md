# Evaluating AI-Facing Context Health Before Agent Execution

Status: technical report draft for the public v0.6 companion evaluation artifact.

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
| `missing_source_coverage` | Memory candidate lacks source coverage evidence. |
| `missing_rollback` | Memory candidate lacks deletion or rollback path. |
| `unbounded_consequence` | Memory candidate lacks a consequence ceiling. |
| `missing_model_state_surface` | Memory candidate omits affected model-state surfaces. |

## Dataset Construction

The v0.1 dataset contains 50 synthetic cases:

- 44 positive cases
- 6 clean controls
- evidence spans for every positive label
- explicit `none` labels for clean controls

The v0.2 dataset adds 50 sanitized trace-pattern cases and 12 public
hidden-holdout case texts with labels withheld. The v0.2 families are:

- Memory X-Ray L1 Eval
- Release Integrity / Claim-Lint Eval
- Session Continuity Hidden-Holdout Eval
- Task Shard Context Control Eval

These sets are designed to validate schema, scoring, adapters, and workflow
shape. They are not intended to estimate real-world prevalence.

The v0.4 dataset adds 20 synthetic hard negatives. The v0.5 dataset adds 160
deterministic mutation cases and 206 labels:

- 120 positive cases
- 40 clean controls
- 40 multi-label cases
- paraphrase, order-shuffle, cross-file, repaired-clean, and negated-clean
  mutations

The v0.5 split is a regression and artifact-readiness scaffold. It is not
independently adjudicated trace data.

The v0.6 dataset adds 60 adversarial hard negatives. Each case contains hazard
vocabulary such as releases, 404s, failed commands, rollback, memory, schema,
and approval, but the context is repaired, scoped, or negated and should not be
flagged.

## Evaluation Protocol

Each evaluator reads `data/cases.jsonl` and emits predictions with:

- `case_id`
- `finding_type`
- `evidence_span`
- `confidence`
- `source`

The scorer compares `(case_id, finding_type)` pairs and reports aggregate and
per-finding precision, recall, F1, false positives, false negatives, and
token-F1 evidence-span overlap for true positives.

For multi-label splits, `scoring/score_multilabel.py` treats each
`(case_id, finding_type)` pair as one expected finding and separately reports
case-level precision, recall, F1, and true negatives.

## Baselines

Regex baseline:

- deterministic
- no model call
- no network call
- transparent rules
- brittle by design

LLM judge baseline:

- included as an offline no-op baseline
- not run by default because this repo forbids provider/model calls without
  explicit configuration

CtxGov adapter:

- `heuristic` mode: transparent pattern adapter that does not read labels
- `doctor` mode: invokes local `ctxgov.cli doctor` over materialized case
  workspaces
- neither mode makes a public benchmark claim

## Results

The local run should report scaffold metrics for:

- regex baseline
- CtxGov heuristic adapter
- CtxGov doctor adapter when a local CtxGov checkout is provided

Observed v0.1 local scaffold metrics on 2026-06-03:

| Evaluator | Precision | Recall | F1 | Notes |
| --- | ---: | ---: | ---: | --- |
| regex baseline | 0.9524 | 0.9091 | 0.9302 | Transparent brittle baseline. |
| CtxGov heuristic adapter | 0.5000 | 0.0455 | 0.0833 | Does not read labels; narrow pattern adapter. |

Observed v0.2 local scaffold metrics on 2026-06-03:

| Evaluator | Precision | Recall | F1 | Mean Evidence Token-F1 | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| regex baseline | 1.0000 | 1.0000 | 1.0000 | 0.9143 | Transparent rules over public trace-pattern data; overfits scaffold patterns. |
| CtxGov heuristic adapter | 1.0000 | 1.0000 | 1.0000 | 0.5803 | Does not read labels, but remains a pattern adapter over public data. |
| CtxGov doctor adapter | 0.3158 | 0.1200 | 0.1739 | 0.2000 | Real local CtxGov doctor invocation; exposes taxonomy and adapter gaps. |

Observed v0.5 local mutation multi-label metrics on 2026-06-03:

| Evaluator | Cases | Labels | Precision | Recall | F1 | Mean Evidence Token-F1 | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| regex baseline | 160 | 206 | 1.0000 | 0.6205 | 0.7658 | 1.0000 | High precision, limited paraphrase and multi-label recall. |
| CtxGov doctor adapter | 160 | 206 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | Local CtxGov doctor invocation over deterministic mutation scaffold. |

Observed v0.6 local adversarial hard-negative metrics on 2026-06-03:

| Evaluator | Cases | Expected positives | Predicted positives | False positives | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| regex baseline | 60 | 0 | 0 | 0 | No FP on local adversarial clean controls. |
| CtxGov doctor adapter | 60 | 0 | 0 | 0 | No FP on local adversarial clean controls. |

Do not quote these as public benchmark results. They are reproducibility checks
for the harness, adapter, and local doctor coverage. The v0.5 doctor result and
v0.6 hard-negative result are deterministic scaffold readiness signals, not
real-world performance estimates.

## Error Analysis

Use the scorer output to review:

- false positives on clean controls
- missed failure-family detections
- evidence spans that are too broad
- finding-type confusion between stale and unsupported release claims
- unsafe-action findings that are actually permissioned instructions
- under-labeled multi-label cases where one evidence span implies both unsafe
  action and missing rollback
- false positives on repaired, scoped, or negated hard negatives

## Limitations

This draft does not claim:

- security guarantees
- hallucination prevention
- model reliability improvement
- universal benchmark status
- provider/framework compatibility
- real-world prevalence
- adoption evidence

Before benchmark publication, this needs real trace-derived cases with reviewer
approval, independently administered hidden labels, larger hard negative
controls, adjudication notes, and a reproducible data-construction section.

## Future Work

- add real saved workflow traces
- expand hard negative controls beyond deterministic clean cases
- collect independent FP/FN reviewer notes
