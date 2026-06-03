from __future__ import annotations

import argparse
import json
from pathlib import Path

from metrics import precision_recall_f1
from score_findings import read_jsonl, span_token_f1


def _positive_labels(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("finding_type") != "none" and row.get("must_flag", True)]


def _positive_predictions(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("finding_type") and row.get("finding_type") != "none"]


def _metric_block(tp: int, fp: int, fn: int) -> dict:
    metrics = precision_recall_f1(tp, fp, fn)
    return {
        "true_positive_count": tp,
        "false_positive_count": fp,
        "false_negative_count": fn,
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
    }


def score_multilabel(labels_path: Path, predictions_path: Path) -> dict:
    labels = read_jsonl(labels_path)
    predictions = read_jsonl(predictions_path)
    positive_labels = _positive_labels(labels)
    positive_predictions = _positive_predictions(predictions)

    expected = {(row["case_id"], row["finding_type"]) for row in positive_labels}
    predicted = {(row["case_id"], row["finding_type"]) for row in positive_predictions}

    label_by_key = {(row["case_id"], row["finding_type"]): row for row in positive_labels}
    prediction_by_key = {(row["case_id"], row["finding_type"]): row for row in positive_predictions}

    tp_items = sorted(expected & predicted)
    fp_items = sorted(predicted - expected)
    fn_items = sorted(expected - predicted)

    expected_cases = {case_id for case_id, _ in expected}
    predicted_cases = {case_id for case_id, _ in predicted}
    all_case_ids = {row["case_id"] for row in labels} | {row["case_id"] for row in predictions}
    case_tp = len(expected_cases & predicted_cases)
    case_fp = len(predicted_cases - expected_cases)
    case_fn = len(expected_cases - predicted_cases)
    case_tn = len(all_case_ids - expected_cases - predicted_cases)

    per_finding_type = {}
    for finding_type in sorted({finding_type for _, finding_type in expected | predicted}):
        expected_for_type = {item for item in expected if item[1] == finding_type}
        predicted_for_type = {item for item in predicted if item[1] == finding_type}
        per_finding_type[finding_type] = _metric_block(
            len(expected_for_type & predicted_for_type),
            len(predicted_for_type - expected_for_type),
            len(expected_for_type - predicted_for_type),
        )

    span_scores = []
    for key in tp_items:
        span_scores.append(
            span_token_f1(
                str(label_by_key[key].get("evidence_span", "")),
                str(prediction_by_key[key].get("evidence_span", "")),
            )
        )

    return {
        "schema_id": "agent-context-evals.multilabel-score/v1",
        "labels": str(labels_path),
        "predictions": str(predictions_path),
        "finding_level": _metric_block(len(tp_items), len(fp_items), len(fn_items)),
        "case_level": {
            **_metric_block(case_tp, case_fp, case_fn),
            "true_negative_count": case_tn,
        },
        "expected_positive_finding_count": len(expected),
        "predicted_positive_finding_count": len(predicted),
        "expected_positive_case_count": len(expected_cases),
        "predicted_positive_case_count": len(predicted_cases),
        "per_finding_type": per_finding_type,
        "evidence_span": {
            "evaluated_true_positive_count": len(span_scores),
            "mean_token_f1": round(sum(span_scores) / len(span_scores), 4) if span_scores else 0.0,
        },
        "false_positives": [{"case_id": case_id, "finding_type": finding_type} for case_id, finding_type in fp_items],
        "false_negatives": [{"case_id": case_id, "finding_type": finding_type} for case_id, finding_type in fn_items],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score multi-label Agent Context Health findings.")
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(score_multilabel(args.labels, args.predictions), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
