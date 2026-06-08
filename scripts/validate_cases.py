#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ALLOWED_FINDING_TYPES = {
    "none",
    "stale_claim",
    "conflicting_policy",
    "unsupported_release_claim",
    "unsafe_action_guidance",
    "hidden_terminal_failure",
    "missing_source_coverage",
    "missing_rollback",
    "unbounded_consequence",
    "missing_model_state_surface",
}
CASE_REQUIRED_FIELDS = {"case_id", "split", "source", "ai_context"}
LABEL_REQUIRED_FIELDS = {"case_id", "finding_type", "must_flag"}
LABEL_LEAK_FIELDS = {"expected_finding_type", "expected_evidence_span", "expected_severity"}


class ValidationError(Exception):
    pass


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValidationError(f"{path}:{line_number}: row must be an object")
            rows.append(row)
    return rows


def require_string(row: dict[str, Any], field: str, source: str) -> None:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{source}: field {field!r} must be a non-empty string")


def validate(
    cases_path: Path,
    labels_path: Path,
    *,
    allow_legacy_label_fields: bool = False,
    allow_unlabeled_splits: set[str] | None = None,
) -> dict[str, Any]:
    allow_unlabeled_splits = allow_unlabeled_splits or set()
    cases = read_jsonl(cases_path)
    labels = read_jsonl(labels_path)
    if not cases:
        raise ValidationError("case file is empty")
    if not labels:
        raise ValidationError("label file is empty")

    seen_cases: set[str] = set()
    case_splits: dict[str, str] = {}
    label_leaks: list[str] = []
    for index, case in enumerate(cases, start=1):
        source = f"{cases_path}:{index}"
        missing = sorted(CASE_REQUIRED_FIELDS - case.keys())
        if missing:
            raise ValidationError(f"{source}: missing case fields: {', '.join(missing)}")
        for field in CASE_REQUIRED_FIELDS:
            require_string(case, field, source)
        case_id = case["case_id"]
        if case_id in seen_cases:
            raise ValidationError(f"{source}: duplicate case_id {case_id!r}")
        seen_cases.add(case_id)
        case_splits[case_id] = case["split"]
        leaked = sorted(LABEL_LEAK_FIELDS & case.keys())
        if leaked:
            label_leaks.append(f"{case_id}: {', '.join(leaked)}")

    if label_leaks and not allow_legacy_label_fields:
        raise ValidationError("label leakage in case rows: " + "; ".join(label_leaks[:5]))

    labels_by_case: dict[str, list[dict[str, Any]]] = {}
    label_pairs: set[tuple[str, str]] = set()
    for index, label in enumerate(labels, start=1):
        source = f"{labels_path}:{index}"
        missing = sorted(LABEL_REQUIRED_FIELDS - label.keys())
        if missing:
            raise ValidationError(f"{source}: missing label fields: {', '.join(missing)}")
        require_string(label, "case_id", source)
        require_string(label, "finding_type", source)
        if not isinstance(label.get("must_flag"), bool):
            raise ValidationError(f"{source}: field 'must_flag' must be boolean")
        case_id = label["case_id"]
        finding_type = label["finding_type"]
        if finding_type not in ALLOWED_FINDING_TYPES:
            raise ValidationError(f"{source}: unknown finding_type {finding_type!r}")
        if case_id not in seen_cases:
            raise ValidationError(f"{source}: label references unknown case_id {case_id!r}")
        pair = (case_id, finding_type)
        if pair in label_pairs:
            raise ValidationError(f"{source}: duplicate label pair {case_id!r}/{finding_type!r}")
        label_pairs.add(pair)
        labels_by_case.setdefault(case_id, []).append(label)

    missing_labels = sorted(seen_cases - labels_by_case.keys())
    disallowed_missing_labels = [
        case_id
        for case_id in missing_labels
        if case_splits.get(case_id) not in allow_unlabeled_splits
    ]
    if disallowed_missing_labels:
        raise ValidationError("cases without labels: " + ", ".join(disallowed_missing_labels[:10]))

    positive_labels = [
        label
        for label in labels
        if label.get("finding_type") != "none" and label.get("must_flag", True)
    ]
    clean_controls = [
        label
        for label in labels
        if label.get("finding_type") == "none" or not label.get("must_flag", True)
    ]
    return {
        "cases": str(cases_path),
        "labels": str(labels_path),
        "case_count": len(cases),
        "label_count": len(labels),
        "positive_label_count": len(positive_labels),
        "clean_control_count": len(clean_controls),
        "legacy_label_fields_allowed": allow_legacy_label_fields,
        "legacy_label_field_rows": len(label_leaks),
        "unlabeled_case_count": len(missing_labels),
        "unlabeled_case_ids": missing_labels,
        "unlabeled_splits": sorted({case_splits[case_id] for case_id in missing_labels}),
        "allowed_unlabeled_splits": sorted(allow_unlabeled_splits),
        "finding_types": sorted({label["finding_type"] for label in labels}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Agent Context Health Eval case and label JSONL files.")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument(
        "--allow-legacy-label-fields",
        action="store_true",
        help="Allow v0.1 seed case rows to contain expected_* helper fields.",
    )
    parser.add_argument(
        "--allow-unlabeled-split",
        action="append",
        default=[],
        help="Allow cases in this split to remain unlabeled, for sealed holdout custody only.",
    )
    args = parser.parse_args()
    try:
        summary = validate(
            args.cases,
            args.labels,
            allow_legacy_label_fields=args.allow_legacy_label_fields,
            allow_unlabeled_splits=set(args.allow_unlabeled_split),
        )
    except ValidationError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
