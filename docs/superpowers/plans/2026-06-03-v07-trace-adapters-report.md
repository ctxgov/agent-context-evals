# v0.7 Trace Adapters Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish `agent-context-evals` v0.7.0 as a trace-shaped local evaluation artifact with offline adapters, error analysis, refreshed report, and demo material.

**Architecture:** Keep the repo local-first and JSONL-based. Add v0.7 trace-shaped cases/labels under `data/v0.7`, extend offline adapters without network calls, add reusable error-analysis reporting, then update reports/demo/release copy and validate through unittest plus scoring commands.

**Tech Stack:** Python standard library, JSONL fixtures, `unittest`, GitHub source releases.

---

### Task 1: v0.7 Trace-Shaped Suite

**Files:**
- Create: `scripts/generate_v07_trace_suite.py`
- Create: `data/v0.7/trace_shaped_cases.jsonl`
- Create: `data/v0.7/trace_shaped_labels.jsonl`
- Create: `data/v0.7/trace_shaped_manifest.json`
- Test: `tests/test_v07_trace_adapters_error_analysis.py`

- [ ] Write tests requiring at least 90 v0.7 cases across terminal logs, handoff summaries, AGENTS/Cursor/CLAUDE rules, release notes, GitHub issue/PR snippets, package registry manifests, local transcripts, and memory traces.
- [ ] Verify the test fails before the generator and data exist.
- [ ] Implement the generator with deterministic rows, evidence spans, finding types, families, and clean controls.
- [ ] Generate data and verify tests pass.

### Task 2: Offline Adapter Expansion

**Files:**
- Modify: `adapters/offline_context_adapters.py`
- Create: `adapters/v07_trace_adapters.py`
- Test: `tests/test_v07_trace_adapters_error_analysis.py`

- [ ] Write tests for GitHub PR/release/issues, CI/terminal log, rules-file, package registry, local transcript, and memory trace adapters.
- [ ] Verify the tests fail because the v0.7 adapter module is missing.
- [ ] Implement adapter functions that accept local payloads/text and return normalized eval cases without network or provider calls.
- [ ] Verify the tests pass and adapter outputs include `adapter_name`, `source`, `benchmark_family`, and evidence spans.

### Task 3: Automated Error Analysis

**Files:**
- Create: `scoring/error_analysis.py`
- Create: `reports/v0.7-regex-error-analysis.json`
- Create: `reports/v0.7-ctxgov-heuristic-error-analysis.json`
- Test: `tests/test_v07_trace_adapters_error_analysis.py`

- [ ] Write tests requiring FP/FN tables, per-finding counts, hard-negative leakage counts, and evidence-span diagnostics summary.
- [ ] Verify the tests fail before `scoring/error_analysis.py` exists.
- [ ] Implement `build_error_analysis(labels, predictions, span_diagnostics=None)`.
- [ ] Generate v0.7 regex and CtxGov heuristic predictions plus error-analysis reports.

### Task 4: Report And Demo Refresh

**Files:**
- Modify: `reports/technical-report.md`
- Create: `reports/v0.7-results.md`
- Modify: `demo/index.html`
- Create: `demo/reports/v0.7-live-report-fixture.md`
- Create: `release/v0.7.0.md`
- Test: `tests/test_v07_trace_adapters_error_analysis.py`

- [ ] Write tests requiring v0.7 report links, adapter descriptions, limitations, and demo fixture references.
- [ ] Update technical report with v0.7 suite, adapter contracts, local-only limitations, and reproducibility commands.
- [ ] Add demo fixture copy that shows before/after context-health findings.
- [ ] Add release draft for `v0.7.0`.

### Task 5: Release And Main Repo Alignment

**Files:**
- Companion: `README.md`, `release/v0.7.0.md`
- Main repo later: `README.md`, `docs/index.html`, `docs/*positioning*`, `release/v0.6.8/*`, release-integrity checker.

- [ ] Run companion full tests and scoring commands.
- [ ] Merge companion PR and publish `agent-context-evals` v0.7.0.
- [ ] Update CtxGov main repo public surface to point to companion v0.7.0 and publish a main alignment release.
- [ ] Prepare LinkedIn/outreach materials with v0.7 links.
