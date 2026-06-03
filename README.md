# Agent Context Health Eval

Status: public v0.1 skeleton for `ctxgov/agent-context-evals`.

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
- clean controls with no expected finding

## Structure

```text
agent-context-evals/
  README.md
  data/
    cases.jsonl
    labels.jsonl
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

The checked-in `ctxgov_adapter/run_ctxgov.py` is a local output-contract stub.
Replace it with a real CtxGov invocation before using the adapter output as a
result. The included `reports/ctxgov-adapter-results.jsonl` exists so the
scorer and report shape can be inspected.

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

The v0.1 data is synthetic and small. It is useful for schema, scorer, and
workflow validation, not for public benchmark claims. It does not prove security
coverage, agent safety, model reliability, provider compatibility, or real-world
prevalence.

Before a public benchmark claim, this needs real trace-derived cases, hidden
holdout cases, negative controls, independent reviewer notes, and a documented
data construction process.

## Related Project

- CtxGov main repo: `https://github.com/ctxgov/ctxgov`
