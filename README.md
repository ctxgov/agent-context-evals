# Agent Context Health Eval

Status: public v0.2 evaluation-artifact skeleton for `ctxgov/agent-context-evals`.

This repository is an evaluation artifact for AI-agent context health. It is
not a public benchmark claim, security evaluation, provider compatibility
matrix, hosted demo, or package release.

## Purpose

This skeleton asks whether an evaluator can detect unhealthy AI-facing context
before agent execution, using labeled cases with expected finding types and
evidence spans.

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
  reports/
    v0.1-results.md
    technical-report.md
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

The v0.1 and v0.2 data are synthetic or sanitized trace-pattern data. They are
useful for schema, scorer, adapter, and workflow validation, not for public
benchmark claims. They do not prove security coverage, agent safety, model
reliability, provider compatibility, or real-world prevalence.

Before a public benchmark claim, this needs real trace-derived cases with
reviewer approval, hard negative controls, independent reviewer labels, and a
documented data construction process.

## Related Project

- CtxGov main repo: `https://github.com/ctxgov/ctxgov`
