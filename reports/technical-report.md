# Evaluating AI-Facing Context Health Before Agent Execution

Status: technical report draft for the public v0.2 companion benchmark skeleton.

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

Do not quote these as public benchmark results. They are reproducibility checks
for the benchmark harness. The v0.2 doctor result is the only real CtxGov
invocation result, and it shows current coverage gaps rather than benchmark
readiness.

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

Before benchmark publication, this needs real trace-derived cases with reviewer
approval, independently administered hidden labels, hard negative controls,
multi-label policy, and a reproducible data-construction section.

## Future Work

- improve the real CtxGov doctor adapter mappings and upstream CtxGov findings
- add real saved workflow traces
- add hard negative controls
- add report rendering and demo GIF
- collect independent FP/FN reviewer notes
