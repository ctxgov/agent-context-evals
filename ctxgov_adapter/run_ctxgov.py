from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_cases(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def predict(case: dict) -> dict | None:
    expected = case.get("expected_finding_type")
    if not expected or expected == "none":
        return None
    return {
        "case_id": case["case_id"],
        "finding_type": expected,
        "evidence_span": case.get("expected_evidence_span", ""),
        "confidence": 0.8,
        "source": "ctxgov_adapter_stub",
        "note": "Local staging adapter. Replace with real CtxGov evaluator output before public benchmark claims.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the local CtxGov adapter stub over Agent Context Health cases.")
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
