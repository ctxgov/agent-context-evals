from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from metrics import precision_recall_f1


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def span_token_f1(expected_span: str, predicted_span: str) -> float:
    expected_tokens = _tokens(expected_span)
    predicted_tokens = _tokens(predicted_span)
    if not expected_tokens or not predicted_tokens:
        return 0.0
    overlap = expected_tokens & predicted_tokens
    if not overlap:
        return 0.0
    precision = len(overlap) / len(predicted_tokens)
    recall = len(overlap) / len(expected_tokens)
    return round(2 * precision * recall / (precision + recall), 4)


def _metric_block(items: set[tuple[str, str]], expected: set[tuple[str, str]], predicted: set[tuple[str, str]]) -> dict:
    tp = len(items & expected & predicted)
    fp = len((items & predicted) - expected)
    fn = len((items & expected) - predicted)
    metrics = precision_recall_f1(tp, fp, fn)
    return {
        "true_positive_count": tp,
        "false_positive_count": fp,
        "false_negative_count": fn,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
    }


def score(labels_path: Path, predictions_path: Path) -> dict:
    labels = read_jsonl(labels_path)
    predictions = read_jsonl(predictions_path)

    expected = {
        (row["case_id"], row["finding_type"])
        for row in labels
        if row["finding_type"] != "none" and row.get("must_flag", True)
    }
    predicted = {
        (row["case_id"], row["finding_type"])
        for row in predictions
        if row.get("finding_type") and row.get("finding_type") != "none"
    }
    label_by_key = {
        (row["case_id"], row["finding_type"]): row
        for row in labels
        if row["finding_type"] != "none" and row.get("must_flag", True)
    }
    prediction_by_key = {
        (row["case_id"], row["finding_type"]): row
        for row in predictions
        if row.get("finding_type") and row.get("finding_type") != "none"
    }

    tp_items = sorted(expected & predicted)
    fp_items = sorted(predicted - expected)
    fn_items = sorted(expected - predicted)

    metrics = precision_recall_f1(len(tp_items), len(fp_items), len(fn_items))
    finding_types = sorted({finding_type for _, finding_type in expected | predicted})
    per_finding_type = {}
    for finding_type in finding_types:
        items = {(case_id, row_finding_type) for case_id, row_finding_type in expected | predicted if row_finding_type == finding_type}
        per_finding_type[finding_type] = _metric_block(items, expected, predicted)

    span_scores = []
    for key in tp_items:
        label_span = str(label_by_key[key].get("evidence_span", ""))
        prediction_span = str(prediction_by_key[key].get("evidence_span", ""))
        span_scores.append(span_token_f1(label_span, prediction_span))
    mean_span = round(sum(span_scores) / len(span_scores), 4) if span_scores else 0.0

    return {
        "labels": str(labels_path),
        "predictions": str(predictions_path),
        "expected_positive_count": len(expected),
        "predicted_positive_count": len(predicted),
        "true_positive_count": len(tp_items),
        "false_positive_count": len(fp_items),
        "false_negative_count": len(fn_items),
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "per_finding_type": per_finding_type,
        "evidence_span": {
            "evaluated_true_positive_count": len(span_scores),
            "mean_token_f1": mean_span,
        },
        "false_positives": [{"case_id": case_id, "finding_type": finding_type} for case_id, finding_type in fp_items],
        "false_negatives": [{"case_id": case_id, "finding_type": finding_type} for case_id, finding_type in fn_items],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score Agent Context Health findings.")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score(args.labels, args.predictions), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
