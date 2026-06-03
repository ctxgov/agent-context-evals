from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


RULES = [
    (
        "missing_source_coverage",
        re.compile(r"(source coverage missing)", re.I),
    ),
    (
        "missing_rollback",
        re.compile(r"(rollback missing)", re.I),
    ),
    (
        "unbounded_consequence",
        re.compile(r"(consequence ceiling unbounded)", re.I),
    ),
    (
        "missing_model_state_surface",
        re.compile(r"(model-state surface missing)", re.I),
    ),
    (
        "hidden_terminal_failure",
        re.compile(r"(FAILED|failed|exit code 1|404 not found|Traceback|auth status failed|output file was empty|FAILED tests after handoff says passed)", re.I),
    ),
    (
        "unsafe_action_guidance",
        re.compile(r"(without asking for approval|force push|Deploy .* immediately|Send .* maintainers|rm -rf|Bypass failing|Publish the package first|Rename every .* archived receipts|apply shard without approval or rollback)", re.I),
    ),
    (
        "unsupported_release_claim",
        re.compile(r"(release is public|benchmark results are published|from PyPI|passing and released|Space is live|accepted paper|repo exists|review passed|release URL returned 404|tag is missing|package registry status missing)", re.I),
    ),
    (
        "conflicting_policy",
        re.compile(r"(may write|publish after|include raw logs|remote fetch by default|About now|advertise security|tag automatically|hosted runtime|adoption is proven|LLM judge baseline|schema import allowed and blocked)", re.I),
    ),
    (
        "stale_claim",
        re.compile(r"(generally available|benchmark is complete|published to PyPI|demo is ready|prevents hallucinations|CLI is ctxgov|all tests passed|500 labeled cases|adapters are approved|endorsed the benchmark|pending approval contradicts ready claim)", re.I),
    ),
]


def read_cases(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def predict(case: dict) -> dict | None:
    text = case["ai_context"]
    for finding_type, pattern in RULES:
        match = pattern.search(text)
        if match:
            return {
                "case_id": case["case_id"],
                "finding_type": finding_type,
                "evidence_span": match.group(0),
                "confidence": 0.45,
                "source": "regex_baseline",
            }
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a transparent regex baseline over Agent Context Health cases.")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for case in read_cases(args.cases):
            prediction = predict(case)
            if prediction:
                handle.write(json.dumps(prediction, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
