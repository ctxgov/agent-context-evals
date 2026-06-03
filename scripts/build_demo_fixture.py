from __future__ import annotations

import argparse
import json
from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _finding(case_id: str, finding_type: str, evidence_span: str, source_path: str, reason: str) -> dict:
    return {
        "case_id": case_id,
        "finding_type": finding_type,
        "evidence_span": evidence_span,
        "source_path": source_path,
        "confidence": 0.7,
        "reason": reason,
    }


def detect_demo_findings(fixture_root: Path) -> list[dict]:
    agents = _read(fixture_root / "AGENTS.md")
    readme = _read(fixture_root / "README.md")
    release_check = _read(fixture_root / "docs" / "release-check.md")
    terminal = _read(fixture_root / "logs" / "terminal.log")
    memory = _read(fixture_root / "memory" / "session-summary.md")
    all_text = "\n".join([agents, readme, release_check, terminal, memory])

    findings: list[dict] = []
    if "Do not publish public releases without a passing test run" in agents and "Publish release notes after any local run" in agents:
        findings.append(
            _finding(
                "demo-conflicting-policy",
                "conflicting_policy",
                "Do not publish public releases without a passing test run",
                "AGENTS.md",
                "The fixture contains incompatible publication rules for the next agent.",
            )
        )
    if "release v9.9.9 is public" in readme and "404 Not Found" in release_check:
        findings.append(
            _finding(
                "demo-unsupported-release",
                "unsupported_release_claim",
                "release v9.9.9 is public",
                "README.md",
                "A public release claim is contradicted by the artifact check.",
            )
        )
    if "FAILED tests after handoff says passed" in terminal and "all tests passed" in readme:
        findings.append(
            _finding(
                "demo-hidden-terminal-failure",
                "hidden_terminal_failure",
                "FAILED tests after handoff says passed",
                "logs/terminal.log",
                "The handoff-ready claim hides a terminal failure.",
            )
        )
    if "push directly to main without asking for approval" in agents:
        findings.append(
            _finding(
                "demo-unsafe-action",
                "unsafe_action_guidance",
                "push directly to main without asking for approval",
                "AGENTS.md",
                "The instruction asks for a side effect without approval.",
            )
        )
    memory_rules = [
        ("missing_source_coverage", "source coverage missing", "memory/session-summary.md"),
        ("missing_rollback", "rollback missing", "memory/session-summary.md"),
        ("unbounded_consequence", "consequence ceiling unbounded", "memory/session-summary.md"),
        ("missing_model_state_surface", "model-state surface missing", "memory/session-summary.md"),
    ]
    for finding_type, evidence, source_path in memory_rules:
        if evidence in all_text:
            findings.append(
                _finding(
                    f"demo-{finding_type.replace('_', '-')}",
                    finding_type,
                    evidence,
                    source_path,
                    "Memory X-Ray L1 metadata is incomplete in the fixture.",
                )
            )
    return findings


def _markdown_report(payload: dict) -> str:
    rows = "\n".join(
        "| {finding_type} | `{source_path}` | {evidence_span} | {reason} |".format(**finding)
        for finding in payload["findings"]
    )
    return f"""# Demo Context Health Report

Status: reproducible v0.3 demo fixture.

This report is not a security guarantee, universal benchmark claim, hosted leaderboard, or provider compatibility statement. It is a small before/after artifact for explaining Agent Context Health evaluation.

## Fixture

- fixture: `{payload["fixture"]}`
- generated_by: `{payload["generated_by"]}`
- finding_count: {len(payload["findings"])}

## Findings

| Finding type | Source | Evidence span | Why it matters |
| --- | --- | --- | --- |
{rows}

## How to Rebuild

```bash
python3 scripts/build_demo_fixture.py --fixture demo/fixtures/bad_context_repo --output-dir demo/reports
```
"""


def build_demo_report(fixture_root: Path, output_dir: Path) -> dict:
    findings = detect_demo_findings(fixture_root)
    payload = {
        "schema_version": "agent-context-health-demo-v0.3",
        "fixture": fixture_root.name,
        "generated_by": "scripts/build_demo_fixture.py",
        "claim_boundary": "Demo fixture only; not a security guarantee or benchmark claim.",
        "findings": findings,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "demo-context-health-report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "demo-context-health-report.md").write_text(_markdown_report(payload), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the reproducible v0.3 demo context-health report.")
    parser.add_argument("--fixture", type=Path, default=Path("demo/fixtures/bad_context_repo"))
    parser.add_argument("--output-dir", type=Path, default=Path("demo/reports"))
    args = parser.parse_args()
    build_demo_report(args.fixture, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
