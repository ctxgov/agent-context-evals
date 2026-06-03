from __future__ import annotations

import argparse
import json
from pathlib import Path

from metrics import precision_recall_f1


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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

    tp_items = sorted(expected & predicted)
    fp_items = sorted(predicted - expected)
    fn_items = sorted(expected - predicted)

    metrics = precision_recall_f1(len(tp_items), len(fp_items), len(fn_items))
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
