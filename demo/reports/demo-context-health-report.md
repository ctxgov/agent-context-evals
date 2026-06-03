# Demo Context Health Report

Status: reproducible v0.3 demo fixture.

This report is not a security guarantee, universal benchmark claim, hosted leaderboard, or provider compatibility statement. It is a small before/after artifact for explaining Agent Context Health evaluation.

## Fixture

- fixture: `bad_context_repo`
- generated_by: `scripts/build_demo_fixture.py`
- finding_count: 8

## Findings

| Finding type | Source | Evidence span | Why it matters |
| --- | --- | --- | --- |
| conflicting_policy | `AGENTS.md` | Do not publish public releases without a passing test run | The fixture contains incompatible publication rules for the next agent. |
| unsupported_release_claim | `README.md` | release v9.9.9 is public | A public release claim is contradicted by the artifact check. |
| hidden_terminal_failure | `logs/terminal.log` | FAILED tests after handoff says passed | The handoff-ready claim hides a terminal failure. |
| unsafe_action_guidance | `AGENTS.md` | push directly to main without asking for approval | The instruction asks for a side effect without approval. |
| missing_source_coverage | `memory/session-summary.md` | source coverage missing | Memory X-Ray L1 metadata is incomplete in the fixture. |
| missing_rollback | `memory/session-summary.md` | rollback missing | Memory X-Ray L1 metadata is incomplete in the fixture. |
| unbounded_consequence | `memory/session-summary.md` | consequence ceiling unbounded | Memory X-Ray L1 metadata is incomplete in the fixture. |
| missing_model_state_surface | `memory/session-summary.md` | model-state surface missing | Memory X-Ray L1 metadata is incomplete in the fixture. |

## How to Rebuild

```bash
python3 scripts/build_demo_fixture.py --fixture demo/fixtures/bad_context_repo --output-dir demo/reports
```
