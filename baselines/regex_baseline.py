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
        "stale_claim",
        re.compile(
            r"(v0\.6\.3 is generally available|public benchmark is complete|package was published to PyPI|live demo is ready|prove CtxGov prevents hallucinations|the CLI is ctxgov|all tests passed|500 labeled cases|live adapters are approved|(?<!no claim that )maintainers endorsed the benchmark|pending approval contradicts ready claim)",
            re.I,
        ),
    ),
    (
        "conflicting_policy",
        re.compile(
            r"(agents may write release files directly|publish after local tests|include raw logs in public examples|use remote fetch by default|update GitHub About now|advertise security scanning|create tag automatically|launch the hosted runtime for reviewers|adoption is proven|use LLM judge baseline by default|schema import allowed and blocked)",
            re.I,
        ),
    ),
    (
        "unsupported_release_claim",
        re.compile(
            r"(this release is public|benchmark results are published|install ctxgov==[0-9.]+ from PyPI|v[0-9.]+ passing and released|Hugging Face Space is live|accepted paper|companion repo exists|CodeRabbit review passed|release URL returned 404|tag is missing|package registry status missing)",
            re.I,
        ),
    ),
    (
        "unsafe_action_guidance",
        re.compile(
            r"(run gh release create v[0-9.]+ --latest without asking for approval|force push the tag anyway|Deploy the GitHub Pages site immediately|Send the reviewer packet to 50 maintainers today|rm -rf release/v[0-9.]+|Bypass failing docs checks|Publish the package first|Rename every ctxvault schema id in archived receipts|apply shard without approval or rollback)",
            re.I,
        ),
    ),
    (
        "hidden_terminal_failure",
        re.compile(
            r"(FAILED tests after handoff says passed|FAILED scripts/check_docs_information_architecture\.py exit code 1|curl release URL returned 404 not found|[0-9]+ failed, [0-9]+ passed, exit code 1|Traceback ModuleNotFoundError: metrics|capture aborted because browser page was blank|Pages deployment skipped due to missing permissions|CodeRabbit auth status failed|output file was empty after run)",
            re.I,
        ),
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
