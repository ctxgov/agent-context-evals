# Agent Context Health Eval

Status: public v0.9 machine-evidence artifact for
`ctxgov/agent-context-evals`.

This repository is an evaluation artifact for AI-agent context health. It is
not a public benchmark claim, security evaluation, provider compatibility
matrix, hosted demo, or package release.

## Purpose

This artifact asks whether an evaluator can detect unhealthy AI-facing context
before agent execution, using labeled cases, evidence spans, adapters, and
review workflows.

Finding families:

- `stale_claim`
- `conflicting_policy`
- `unsupported_release_claim`
- `unsafe_action_guidance`
- `hidden_terminal_failure`
- `missing_source_coverage`
- `missing_rollback`
- `unbounded_consequence`
- `missing_model_state_surface`
- `publication_state_drift`
- `repo_map_drift`
- `version_surface_drift`
- `roadmap_pointer_drift`
- clean controls with no expected finding

## Structure

```text
agent-context-evals/
  README.md
  data/
    cases.jsonl
    labels.jsonl
    v0.2/
      trace_pattern_cases.jsonl
      trace_pattern_labels.jsonl
      hidden_holdout_cases.jsonl
      hidden_holdout_manifest.json
      benchmark_families.json
    v0.3/
      review_intake_cases.jsonl
      review_intake_manifest.json
    v0.4/
      hard_negative_cases.jsonl
      hard_negative_labels.jsonl
    v0.5/
      mutation_cases.jsonl
      mutation_labels.jsonl
      mutation_manifest.json
    v0.6/
      adversarial_hard_negative_cases.jsonl
      adversarial_hard_negative_labels.jsonl
      adversarial_hard_negative_manifest.json
    v0.7/
      trace_shaped_cases.jsonl
      trace_shaped_labels.jsonl
      trace_shaped_manifest.json
    v0.8/
      eval_hardening_cases.jsonl
      eval_hardening_labels.jsonl
      eval_hardening_manifest.json
    v0.9/
      machine_evidence_cases.jsonl
      machine_evidence_labels.jsonl
      machine_evidence_manifest.json
      machine_evidence_splits.json
      dataset_card.md
  adapters/
    offline_context_adapters.py
    v07_trace_adapters.py
  baselines/
    regex_baseline.py
    llm_judge_baseline.py
  ctxgov_adapter/
    run_ctxgov.py
  scoring/
    score_findings.py
    metrics.py
    score_multilabel.py
    span_diagnostics.py
    error_analysis.py
  review/
    independent-review-packet.md
    blinded-label-sheet.csv
    reviewer-rubric.md
    label-adjudication-plan.md
    reviewer-proxy-adjudication.json
    reviewer-proxy-labels.jsonl
  demo/
    60-second-demo.gif
    60-second-demo-script.md
    index.html
    fixtures/bad_context_repo/
    reports/demo-context-health-report.md
    reports/v0.7-live-report-fixture.md
  reports/
    v0.1-results.md
    technical-report.md
    v0.2-results.md
    v0.3-readiness.md
    v0.4-results.md
    v0.5-results.md
    v0.6-results.md
    v0.7-results.md
    v0.8-results.md
    v0.9-machine-evidence-report.md
    v0.9-machine-evidence-report.json
  examples/
    clean_repo/
    stale_claim/
    conflicting_policy/
    unsupported_release_claim/
    hidden_terminal_failure/
```

## Quick Run

```bash
python3 baselines/regex_baseline.py --cases data/cases.jsonl --output reports/regex-baseline-results.jsonl
python3 ctxgov_adapter/run_ctxgov.py --cases data/cases.jsonl --output reports/ctxgov-adapter-results.jsonl
python3 scoring/score_findings.py --labels data/labels.jsonl --predictions reports/regex-baseline-results.jsonl
python3 scoring/score_findings.py --labels data/labels.jsonl --predictions reports/ctxgov-adapter-results.jsonl
```

For v0.2 trace-pattern data:

```bash
python3 scripts/generate_v02_data.py
python3 baselines/regex_baseline.py --cases data/v0.2/trace_pattern_cases.jsonl --output reports/v0.2-regex-baseline-results.jsonl
python3 ctxgov_adapter/run_ctxgov.py --cases data/v0.2/trace_pattern_cases.jsonl --output reports/v0.2-ctxgov-heuristic-results.jsonl --mode heuristic
python3 scoring/score_findings.py --labels data/v0.2/trace_pattern_labels.jsonl --predictions reports/v0.2-regex-baseline-results.jsonl
python3 scoring/score_findings.py --labels data/v0.2/trace_pattern_labels.jsonl --predictions reports/v0.2-ctxgov-heuristic-results.jsonl
```

For a real CtxGov doctor invocation, pass a local checkout of
`https://github.com/ctxgov/ctxgov`:

```bash
python3 ctxgov_adapter/run_ctxgov.py \
  --cases data/v0.2/trace_pattern_cases.jsonl \
  --output reports/v0.2-ctxgov-doctor-results.jsonl \
  --mode doctor \
  --ctxgov-root /path/to/ctxgov
```

The v0.2 `heuristic` mode does not read labels, but it is still a transparent
pattern adapter over public trace-pattern data. Treat it as scaffold validation,
not as a research benchmark result. The `doctor` mode shells out to CtxGov's
local `ctxgov.cli doctor` command with no provider/model call.

For v0.3 review and demo materials:

```bash
python3 baselines/llm_judge_baseline.py \
  --cases data/v0.3/review_intake_cases.jsonl \
  --output reports/v0.3-llm-judge-baseline-results.jsonl \
  --manifest reports/v0.3-llm-judge-baseline-manifest.json \
  --prompt-output reports/v0.3-llm-judge-prompts.jsonl

python3 scripts/build_demo_fixture.py \
  --fixture demo/fixtures/bad_context_repo \
  --output-dir demo/reports

bash scripts/render_demo_gif.sh demo/60-second-demo.gif
```

The LLM-judge harness is offline by default. It writes prompts and a manifest,
and can ingest offline reviewer/model decisions with `--review-decisions`, but
it does not call a provider or model.

For v0.4 hard negatives and native CtxGov doctor coverage:

```bash
python3 baselines/regex_baseline.py \
  --cases data/v0.4/hard_negative_cases.jsonl \
  --output reports/v0.4-hard-negative-regex-results.jsonl

python3 ctxgov_adapter/run_ctxgov.py \
  --cases data/v0.2/trace_pattern_cases.jsonl \
  --output reports/v0.4-ctxgov-doctor-results.jsonl \
  --mode doctor \
  --ctxgov-root /path/to/ctxgov

python3 scoring/score_findings.py \
  --labels data/v0.2/trace_pattern_labels.jsonl \
  --predictions reports/v0.4-ctxgov-doctor-results.jsonl
```

For v0.5 deterministic mutation and multi-label scoring:

```bash
python3 scripts/generate_v05_mutation_data.py

python3 baselines/regex_baseline.py \
  --cases data/v0.5/mutation_cases.jsonl \
  --output reports/v0.5-regex-baseline-results.jsonl \
  --multi-label

python3 ctxgov_adapter/run_ctxgov.py \
  --cases data/v0.5/mutation_cases.jsonl \
  --output reports/v0.5-ctxgov-doctor-results.jsonl \
  --mode doctor \
  --projection none \
  --ctxgov-root /path/to/ctxgov

python3 scoring/score_multilabel.py \
  --labels data/v0.5/mutation_labels.jsonl \
  --predictions reports/v0.5-regex-baseline-results.jsonl

python3 scoring/score_multilabel.py \
  --labels data/v0.5/mutation_labels.jsonl \
  --predictions reports/v0.5-ctxgov-doctor-results.jsonl
```

For v0.6 adversarial hard negatives and span diagnostics:

```bash
python3 scripts/generate_v06_adversarial_hard_negatives.py

python3 baselines/regex_baseline.py \
  --cases data/v0.6/adversarial_hard_negative_cases.jsonl \
  --output reports/v0.6-regex-hard-negative-results.jsonl \
  --multi-label

python3 ctxgov_adapter/run_ctxgov.py \
  --cases data/v0.6/adversarial_hard_negative_cases.jsonl \
  --output reports/v0.6-ctxgov-doctor-hard-negative-results.jsonl \
  --mode doctor \
  --projection none \
  --ctxgov-root /path/to/ctxgov

python3 scoring/span_diagnostics.py \
  --labels data/v0.5/mutation_labels.jsonl \
  --predictions reports/v0.5-ctxgov-doctor-results.jsonl \
  --output reports/v0.5-ctxgov-doctor-span-diagnostics.json
```

For v0.7 trace-shaped local evaluation:

```bash
python3 scripts/generate_v07_trace_suite.py

python3 baselines/regex_baseline.py \
  --cases data/v0.7/trace_shaped_cases.jsonl \
  --output reports/v0.7-regex-baseline-results.jsonl \
  --multi-label

python3 ctxgov_adapter/run_ctxgov.py \
  --cases data/v0.7/trace_shaped_cases.jsonl \
  --output reports/v0.7-ctxgov-doctor-results.jsonl \
  --mode doctor \
  --projection none \
  --ctxgov-root /path/to/ctxgov

python3 scoring/error_analysis.py \
  --labels data/v0.7/trace_shaped_labels.jsonl \
  --predictions reports/v0.7-ctxgov-doctor-results.jsonl \
  --hard-negative-labels data/v0.7/trace_shaped_labels.jsonl \
  --output reports/v0.7-ctxgov-doctor-error-analysis.json
```

The v0.7 suite contains 96 trace-shaped local cases across terminal logs,
handoff summaries, AGENTS/Cursor/CLAUDE-style rules, release notes, GitHub
issue/PR snippets, package registry manifests, local transcripts, and memory
traces. It is a local reproducibility artifact, not a public benchmark claim.

For v0.8 eval hardening:

```bash
python3 scripts/generate_v08_eval_hardening.py
python3 scripts/check_v08_reviewer_packet.py
python3 -m unittest tests.test_v08_eval_hardening -v
```

The v0.8 suite adds 50 public-safe hard negatives and 4 CtxGov v0.6.11
self-audit cases. It also adds a blind reviewer protocol and adjudication
template. This is local eval hardening only: No public benchmark claim. No provider/model call. No adoption claim. No package, hosted runtime, live adapter, or CLI beta claim.

For v0.9 machine evidence:

```bash
python3 scripts/check_v09_machine_evidence_readiness.py
python3 -m unittest tests.test_v09_machine_evidence_release -v
```

The v0.9 suite adds public labeled machine-evidence cases, clean controls,
sealed hidden holdout custody, baseline/error-analysis output, and a
reviewer-proxy adjudication fixture. This is local machine evidence only: No
public benchmark claim. No provider/model call. No adoption claim. No human
reviewer claim. No package, hosted runtime, live adapter, or CLI beta claim.

## Case Schema

Each `data/cases.jsonl` row contains:

- `case_id`
- `split`
- `source`
- `ai_context`
- `expected_finding_type`
- `expected_evidence_span`
- `severity`
- `notes`

Each `data/labels.jsonl` row contains:

- `case_id`
- `finding_type`
- `evidence_span`
- `start_char`
- `end_char`
- `must_flag`
- `rationale`

Clean controls use `finding_type: "none"` and `must_flag: false`.

## Limitations

The v0.1 and v0.2 data are synthetic or sanitized trace-pattern data. The v0.3
review intake cases are public trace-derived material prepared for independent
review, but the review is still pending. The v0.4 hard negatives are synthetic
controls that reduce obvious regex false positives but do not replace
independent review. The v0.5 mutation split is deterministic local scaffold
data with multi-label cases and clean controls; it is a strong regression gate,
not a public benchmark claim. The v0.6 adversarial hard negatives add local
false-positive pressure with hazardous vocabulary in repaired, scoped, or
negated context. These artifacts are useful for schema, scorer, adapter,
workflow, and demo validation. They do not prove security coverage, agent
safety, model reliability, provider compatibility, or real-world prevalence.
The v0.9 machine-evidence release adds hidden holdout custody and reproducible
local scoring, but it still does not replace independent human review or
external adoption evidence.

Before a public benchmark claim, this needs real trace-derived cases with
reviewer approval, hard negative controls, independent reviewer labels, and a
documented data construction process.

## Readiness

Ready for public project surface:

- v0.2 scorer, regex baseline, CtxGov heuristic adapter, and real CtxGov doctor adapter results
- v0.3 offline LLM-judge interface with no provider/model call by default
- v0.3 independent review packet with labels withheld
- v0.3 reproducible demo fixture and 60-second GIF
- v0.4 hard-negative controls and tightened regex baseline
- v0.4 native CtxGov doctor adapter run for release integrity, Memory X-Ray L1,
  and Task Shard coverage
- v0.5 deterministic mutation data with 160 cases, 206 labels, 40 clean
  controls, multi-label scoring, and native CtxGov doctor adapter run
- v0.6 adversarial hard negatives with 60 clean controls and span diagnostics
- v0.9 machine-evidence release with sealed hidden holdout custody, baseline
  scoring, and reviewer-proxy adjudication fixture

Not ready for benchmark claims:

- independent review of trace-derived cases
- adjudicated reviewer labels
- hidden holdout label unsealing outside author-controlled custody
- public false positive and false negative analysis on independently reviewed labels

The key v0.6 result is that the artifact now has both positive deterministic
mutation coverage and adversarial clean controls. The 1.0000 v0.5 doctor score
and 0-FP v0.6 hard-negative result validate readiness of this artifact and
adapter path, not general benchmark performance.

## Related Project

- CtxGov main repo: `https://github.com/ctxgov/ctxgov`
- CtxGov project page: `https://ctxgov.github.io/ctxgov/`
- Latest companion release: `https://github.com/ctxgov/agent-context-evals/releases/tag/v0.9.0`
