from __future__ import annotations

import argparse
import json
from pathlib import Path

from score_findings import read_jsonl, span_token_f1


def _positive_labels(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("finding_type") != "none" and row.get("must_flag", True)]


def _positive_predictions(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("finding_type") and row.get("finding_type") != "none"]


def _token_count(value: str) -> int:
    return len([part for part in value.split() if part.strip()])


def _bucket(score: float) -> str:
    if score == 1.0:
        return "exact"
    if score >= 0.75:
        return "high"
    if score > 0.0:
        return "partial"
    return "zero"


def build_span_diagnostics(labels_path: Path, predictions_path: Path) -> dict:
    labels = read_jsonl(labels_path)
    predictions = read_jsonl(predictions_path)
    positive_labels = _positive_labels(labels)
    positive_predictions = _positive_predictions(predictions)

    label_by_key = {(row["case_id"], row["finding_type"]): row for row in positive_labels}
    prediction_by_key = {(row["case_id"], row["finding_type"]): row for row in positive_predictions}

    expected = set(label_by_key)
    predicted = set(prediction_by_key)
    tp_keys = sorted(expected & predicted)
    fp_keys = sorted(predicted - expected)
    fn_keys = sorted(expected - predicted)

    span_rows = []
    for case_id, finding_type in tp_keys:
        expected_span = str(label_by_key[(case_id, finding_type)].get("evidence_span", ""))
        predicted_span = str(prediction_by_key[(case_id, finding_type)].get("evidence_span", ""))
        score = span_token_f1(expected_span, predicted_span)
        span_rows.append(
            {
                "case_id": case_id,
                "finding_type": finding_type,
                "expected_span": expected_span,
                "predicted_span": predicted_span,
                "token_f1": score,
                "expected_token_count": _token_count(expected_span),
                "predicted_token_count": _token_count(predicted_span),
            }
        )

    scores = [row["token_f1"] for row in span_rows]
    bucket_counts = {"exact": 0, "high": 0, "partial": 0, "zero": 0}
    for score in scores:
        bucket_counts[_bucket(score)] += 1

    shortest = sorted(span_rows, key=lambda row: (row["predicted_token_count"], row["case_id"], row["finding_type"]))[:10]
    longest = sorted(span_rows, key=lambda row: (-row["predicted_token_count"], row["case_id"], row["finding_type"]))[:10]
    near_misses = sorted(
        [row for row in span_rows if row["token_f1"] < 1.0],
        key=lambda row: (row["token_f1"], row["case_id"], row["finding_type"]),
    )[:20]

    return {
        "schema_id": "agent-context-evals.span-diagnostics/v1",
        "labels": str(labels_path),
        "predictions": str(predictions_path),
        "true_positive_count": len(tp_keys),
        "false_positive_count": len(fp_keys),
        "false_negative_count": len(fn_keys),
        "mean_token_f1": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "min_token_f1": min(scores) if scores else 0.0,
        "max_token_f1": max(scores) if scores else 0.0,
        "bucket_counts": bucket_counts,
        "shortest_predicted_spans": shortest,
        "longest_predicted_spans": longest,
        "near_misses": near_misses,
        "false_positives": [{"case_id": case_id, "finding_type": finding_type} for case_id, finding_type in fp_keys],
        "false_negatives": [{"case_id": case_id, "finding_type": finding_type} for case_id, finding_type in fn_keys],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize evidence-span overlap diagnostics.")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_span_diagnostics(args.labels, args.predictions)
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
