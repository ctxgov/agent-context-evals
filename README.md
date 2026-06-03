# Agent Context Health Eval

Status: public v0.4 evaluation artifact for `ctxgov/agent-context-evals`.

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
  adapters/
    offline_context_adapters.py
  baselines/
    regex_baseline.py
    llm_judge_baseline.py
  ctxgov_adapter/
    run_ctxgov.py
  scoring/
    score_findings.py
    metrics.py
  review/
    independent-review-packet.md
    blinded-label-sheet.csv
    reviewer-rubric.md
    label-adjudication-plan.md
  demo/
    60-second-demo.gif
    60-second-demo-script.md
    index.html
    fixtures/bad_context_repo/
    reports/demo-context-health-report.md
  reports/
    v0.1-results.md
    technical-report.md
    v0.2-results.md
    v0.3-readiness.md
    v0.4-results.md
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
independent review. These artifacts are useful for schema, scorer, adapter,
workflow, and demo validation, not for public benchmark claims. They do not
prove security coverage, agent safety, model reliability, provider
compatibility, or real-world prevalence.

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

Not ready for benchmark claims:

- independent review of trace-derived cases
- adjudicated reviewer labels
- hidden holdout administration outside this public repo
- public false positive and false negative analysis on reviewed labels
- multi-label scoring for cases where multiple findings are valid

The key v0.4 result is that CtxGov doctor now covers the public trace-pattern
release integrity, Memory X-Ray L1, and Task Shard scaffold. The 1.0000 scores
validate readiness of this artifact and adapter path, not general benchmark
performance.

## Related Project

- CtxGov main repo: `https://github.com/ctxgov/ctxgov`
- CtxGov project page: `https://ctxgov.github.io/ctxgov/`
- Latest companion release: `https://github.com/ctxgov/agent-context-evals/releases/tag/v0.4.0`
