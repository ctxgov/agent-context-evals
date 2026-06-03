# Adapter Contract

Status: v0.2 public adapter contract.

Adapters convert local artifacts into Agent Context Health Eval cases or
predictions. Default adapters must stay offline: no provider calls, no network
fetches, no target repository writes, and no hidden label reads.

## Case Output

Adapters that create cases should emit:

- `case_id`
- `split`
- `source`
- `ai_context`
- `expected_finding_type` when labels are public
- `expected_evidence_span` when labels are public
- `severity`
- `benchmark_family`
- `notes`

Hidden-holdout adapters must not write public expected labels.

## Prediction Output

Evaluator adapters should emit JSONL rows with:

- `case_id`
- `finding_type`
- `evidence_span`
- `confidence`
- `source`

Optional fields such as `ctxgov_finding_type` are allowed when they help error
analysis.

## Current Offline Adapters

- GitHub PR/release/issues metadata adapter: `github_artifact_to_case`
- CI/terminal log adapter: `ci_log_to_case`
- AGENTS/CLAUDE/Cursor rules adapter: `agent_rules_to_case`
- package registry manifest adapter: `package_registry_manifest_to_case`
- local transcript adapter: `transcript_to_case`
- memory-framework trace adapter: `memory_trace_to_case`

All live in `adapters/offline_context_adapters.py`.
