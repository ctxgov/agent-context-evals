from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from score_findings import read_jsonl, span_token_f1


def _positive_labels(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("finding_type") != "none" and row.get("must_flag", True)]


def _positive_predictions(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("finding_type") and row.get("finding_type") != "none"]


def _count_block() -> dict:
    return {"true_positive_count": 0, "false_positive_count": 0, "false_negative_count": 0}


def build_error_analysis(labels_path: Path, predictions_path: Path, *, hard_negative_case_ids: Iterable[str] = ()) -> dict:
    labels = read_jsonl(labels_path)
    predictions = read_jsonl(predictions_path)
    positive_labels = _positive_labels(labels)
    positive_predictions = _positive_predictions(predictions)
    hard_negatives = set(hard_negative_case_ids)

    label_by_key = {(row["case_id"], row["finding_type"]): row for row in positive_labels}
    prediction_by_key = {(row["case_id"], row["finding_type"]): row for row in positive_predictions}
    expected = set(label_by_key)
    predicted = set(prediction_by_key)
    tp_keys = sorted(expected & predicted)
    fp_keys = sorted(predicted - expected)
    fn_keys = sorted(expected - predicted)

    per_finding_type: dict[str, dict] = {}
    for _, finding_type in sorted(expected | predicted):
        per_finding_type.setdefault(finding_type, _count_block())
    for _, finding_type in tp_keys:
        per_finding_type[finding_type]["true_positive_count"] += 1
    for _, finding_type in fp_keys:
        per_finding_type[finding_type]["false_positive_count"] += 1
    for _, finding_type in fn_keys:
        per_finding_type[finding_type]["false_negative_count"] += 1

    span_scores = []
    for key in tp_keys:
        span_scores.append(
            span_token_f1(
                str(label_by_key[key].get("evidence_span", "")),
                str(prediction_by_key[key].get("evidence_span", "")),
            )
        )

    false_positives = [
        {
            "case_id": case_id,
            "finding_type": finding_type,
            "predicted_span": str(prediction_by_key[(case_id, finding_type)].get("evidence_span", "")),
            "hard_negative_leakage": case_id in hard_negatives,
        }
        for case_id, finding_type in fp_keys
    ]
    false_negatives = [
        {
            "case_id": case_id,
            "finding_type": finding_type,
            "expected_span": str(label_by_key[(case_id, finding_type)].get("evidence_span", "")),
        }
        for case_id, finding_type in fn_keys
    ]

    return {
        "schema_id": "agent-context-evals.error-analysis/v1",
        "labels": str(labels_path),
        "predictions": str(predictions_path),
        "summary": {
            "true_positive_count": len(tp_keys),
            "false_positive_count": len(fp_keys),
            "false_negative_count": len(fn_keys),
            "hard_negative_leakage_count": sum(1 for row in false_positives if row["hard_negative_leakage"]),
        },
        "per_finding_type": per_finding_type,
        "span_summary": {
            "evaluated_true_positive_count": len(span_scores),
            "mean_token_f1": round(sum(span_scores) / len(span_scores), 4) if span_scores else 0.0,
            "min_token_f1": min(span_scores) if span_scores else 0.0,
            "max_token_f1": max(span_scores) if span_scores else 0.0,
        },
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def _read_case_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    rows = read_jsonl(path)
    return {row["case_id"] for row in rows if row.get("finding_type") == "none" or row.get("expected_finding_types") == []}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FP/FN and hard-negative leakage analysis for eval predictions.")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--hard-negative-labels", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_error_analysis(args.labels, args.predictions, hard_negative_case_ids=_read_case_ids(args.hard_negative_labels))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
