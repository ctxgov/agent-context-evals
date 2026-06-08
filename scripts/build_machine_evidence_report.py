#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path, *, import_path: Path | None = None) -> Any:
    if import_path is not None:
        sys.path.insert(0, str(import_path))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def filter_public_predictions(
    predictions: list[dict[str, Any]],
    public_case_ids: set[str],
) -> tuple[list[dict[str, Any]], int]:
    public_predictions: list[dict[str, Any]] = []
    ignored_hidden_predictions = 0
    for prediction in predictions:
        if prediction["case_id"] not in public_case_ids:
            ignored_hidden_predictions += 1
            continue
        public_predictions.append(dict(prediction))
    return public_predictions, ignored_hidden_predictions


def regex_predictions(module: Any, cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predictions: list[dict[str, Any]] = []
    for case in cases:
        prediction = module.predict(case)
        if prediction:
            predictions.append(prediction)
    return predictions


def summarize_errors(score_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "false_positive_count": score_report["false_positive_count"],
        "false_negative_count": score_report["false_negative_count"],
        "clean_control_false_positive_count": score_report["clean_control_false_positive_count"],
        "false_positives": score_report["false_positives"],
        "false_negatives": score_report["false_negatives"],
        "per_finding_type": score_report["per_finding_type"],
        "per_source_family": score_report.get("per_source_family", {}),
    }


def scrub_local_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: scrub_local_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_local_paths(item) for item in value]
    if isinstance(value, str):
        try:
            path = Path(value)
            if path.is_absolute():
                return str(path.relative_to(ROOT))
        except ValueError:
            return value
    return value


def write_markdown_summary(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# v0.9 Machine Evidence Report",
        "",
        f"Status: `{report['status']}`",
        "",
        "This report is local machine evidence only. It is not human reviewer",
        "evidence, adoption evidence, provider compatibility evidence, or",
        "package release evidence. It is not a public benchmark result.",
        "",
        "## Baselines",
        "",
    ]
    for name, baseline in sorted(report["baselines"].items()):
        score = baseline["score"]
        lines.append(
            f"- `{name}`: precision `{score['precision']}`, recall `{score['recall']}`, "
            f"F1 `{score['f1']}`, FP `{score['false_positive_count']}`, "
            f"FN `{score['false_negative_count']}`"
        )
    lines.extend(
        [
            "",
            "## Holdout",
            "",
            f"- hidden cases: `{report['holdout_custody']['hidden_holdout_case_count']}`",
            "- hidden labels published: `false`",
            "- hidden labels used for scoring: `false`",
            "",
            "## Claim Boundary",
            "",
            "- no human reviewer claim",
            "- no adoption claim",
            "- no public benchmark result claim",
            "- no provider/model compatibility claim",
            "- no package release claim",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    *,
    cases_path: Path,
    labels_path: Path,
    holdout_custody_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    validate_cases = load_module("ach_validate_cases", ROOT / "scripts" / "validate_cases.py")
    score_findings = load_module(
        "ach_score_findings",
        ROOT / "scoring" / "score_findings.py",
        import_path=ROOT / "scoring",
    )
    regex_baseline = load_module("ach_regex_baseline", ROOT / "baselines" / "regex_baseline.py")
    ctxgov_adapter = load_module("ach_ctxgov_adapter", ROOT / "ctxgov_adapter" / "run_ctxgov.py")

    validation = scrub_local_paths(
        validate_cases.validate(
            cases_path,
            labels_path,
            allow_legacy_label_fields=False,
            allow_unlabeled_splits={"hidden_holdout"},
        )
    )
    cases = read_jsonl(cases_path)
    labels = read_jsonl(labels_path)
    public_case_ids = {label["case_id"] for label in labels}
    hidden_case_ids = set(validation["unlabeled_case_ids"])
    hidden_label_leak_ids = sorted(public_case_ids & hidden_case_ids)
    if hidden_label_leak_ids:
        raise RuntimeError(f"hidden holdout labels leaked: {', '.join(hidden_label_leak_ids)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_files = {
        "noop_baseline": output_path.parent / "v0.9-noop-baseline-results.jsonl",
        "regex_baseline": output_path.parent / "v0.9-regex-baseline-results.jsonl",
        "ctxgov_adapter_heuristic": output_path.parent / "v0.9-ctxgov-heuristic-results.jsonl",
    }

    regex_public, regex_hidden = filter_public_predictions(
        regex_predictions(regex_baseline, cases),
        public_case_ids,
    )
    ctxgov_public, ctxgov_hidden = filter_public_predictions(
        ctxgov_adapter.run_cases(cases, mode="heuristic"),
        public_case_ids,
    )
    baseline_predictions: dict[str, tuple[list[dict[str, Any]], int]] = {
        "noop_baseline": ([], 0),
        "regex_baseline": (regex_public, regex_hidden),
        "ctxgov_adapter_heuristic": (ctxgov_public, ctxgov_hidden),
    }

    baselines: dict[str, Any] = {}
    error_analysis: dict[str, Any] = {}
    for name, (predictions, ignored_hidden_predictions) in baseline_predictions.items():
        predictions_path = prediction_files[name]
        write_jsonl(predictions_path, predictions)
        score_report = scrub_local_paths(score_findings.score(labels_path, predictions_path, cases_path))
        baselines[name] = {
            "predictions": str(predictions_path.relative_to(ROOT)),
            "prediction_count": len(predictions),
            "hidden_predictions_ignored_count": ignored_hidden_predictions,
            "score": score_report,
        }
        error_analysis[name] = summarize_errors(score_report)

    holdout_custody = json.loads(holdout_custody_path.read_text(encoding="utf-8"))
    report = {
        "schema_version": "ach-machine-evidence-report-v0.9",
        "status": "pass_machine_evidence_public_label_scoring",
        "dataset": "agent-context-health-v0.9-machine-evidence",
        "cases": str(cases_path.relative_to(ROOT)),
        "cases_sha256": sha256_file(cases_path),
        "public_labels": str(labels_path.relative_to(ROOT)),
        "public_labels_sha256": sha256_file(labels_path),
        "validation": validation,
        "baselines": baselines,
        "error_analysis": error_analysis,
        "holdout_custody": holdout_custody,
        "hidden_labels_used_for_scoring": False,
        "hidden_label_leak_ids": hidden_label_leak_ids,
        "machine_evidence_only": True,
        "author_approval_required": False,
        "publication_allowed": True,
        "public_benchmark_claim_allowed": False,
        "human_reviewer_claim_allowed": False,
        "adoption_claim_allowed": False,
        "provider_model_compatibility_claim_allowed": False,
        "package_release_claim_allowed": False,
    }
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown_summary(output_path.with_suffix(".md"), report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the v0.9 local machine-evidence report.")
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "v0.9" / "machine_evidence_cases.jsonl")
    parser.add_argument("--labels", type=Path, default=ROOT / "data" / "v0.9" / "machine_evidence_labels.jsonl")
    parser.add_argument(
        "--holdout-custody",
        type=Path,
        default=ROOT / "release" / "v0.9-machine-evidence" / "hidden-holdout-custody.json",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "v0.9-machine-evidence-report.json")
    args = parser.parse_args()

    cases_path = args.cases if args.cases.is_absolute() else ROOT / args.cases
    labels_path = args.labels if args.labels.is_absolute() else ROOT / args.labels
    holdout_custody_path = (
        args.holdout_custody
        if args.holdout_custody.is_absolute()
        else ROOT / args.holdout_custody
    )
    output_path = args.output if args.output.is_absolute() else ROOT / args.output

    try:
        report = build_report(
            cases_path=cases_path,
            labels_path=labels_path,
            holdout_custody_path=holdout_custody_path,
            output_path=output_path,
        )
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f"machine evidence report failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": report["status"], "output": str(output_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
