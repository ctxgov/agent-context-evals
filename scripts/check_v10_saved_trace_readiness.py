#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_script(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": " ".join([sys.executable, *args]),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def require_files(paths: list[Path]) -> list[str]:
    return [str(path.relative_to(ROOT)) for path in paths if not path.exists()]


def private_text_issues(paths: list[Path]) -> list[dict[str, Any]]:
    forbidden = ["/Users/", "/private/tmp", "BEGIN PRIVATE KEY", "sk-", "ghp_", "gho_"]
    issues: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            if marker in text:
                issues.append({"path": str(path.relative_to(ROOT)), "marker": marker})
    return issues


def main() -> int:
    cases_path = ROOT / "data" / "v0.10" / "saved_trace_cases.jsonl"
    labels_path = ROOT / "data" / "v0.10" / "saved_trace_labels.jsonl"
    custody_path = ROOT / "release" / "v0.10-machine-evidence" / "hidden-holdout-custody.json"
    redaction_path = ROOT / "release" / "v0.10-machine-evidence" / "redaction-receipt.json"
    report_path = ROOT / "reports" / "v0.10-machine-evidence-report.json"

    generate = run_script("scripts/generate_v10_saved_trace_machine_evidence.py")
    validate_cases = load_module("ach_validate_cases_v10", ROOT / "scripts" / "validate_cases.py")
    validation = validate_cases.validate(
        cases_path,
        labels_path,
        allow_legacy_label_fields=False,
        allow_unlabeled_splits={"hidden_holdout"},
    )

    required_files = [
        ROOT / ".github" / "workflows" / "ci.yml",
        cases_path,
        labels_path,
        ROOT / "data" / "v0.10" / "dataset_card.md",
        ROOT / "data" / "v0.10" / "saved_trace_manifest.json",
        ROOT / "data" / "v0.10" / "saved_trace_splits.json",
        custody_path,
        redaction_path,
        ROOT / "docs" / "5-minute-local-run.md",
        ROOT / "docs" / "design-v0.10-saved-trace-machine-evidence.md",
        ROOT / "release" / "v0.10-machine-evidence" / "README.md",
        ROOT / "release" / "v0.10.0.md",
    ]
    missing = require_files(required_files)
    labels = read_jsonl(labels_path)
    hidden_label_case_ids = sorted({row["case_id"] for row in labels} & set(validation["unlabeled_case_ids"]))

    build_report = run_script(
        "scripts/build_machine_evidence_report.py",
        "--cases",
        "data/v0.10/saved_trace_cases.jsonl",
        "--labels",
        "data/v0.10/saved_trace_labels.jsonl",
        "--holdout-custody",
        "release/v0.10-machine-evidence/hidden-holdout-custody.json",
        "--redaction-receipt",
        "release/v0.10-machine-evidence/redaction-receipt.json",
        "--release-version",
        "v0.10",
        "--dataset",
        "agent-context-health-v0.10-saved-trace-machine-evidence",
        "--output",
        "reports/v0.10-machine-evidence-report.json",
    )
    report: dict[str, Any] = {}
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))

    claim_check = run_script(
        "scripts/check_no_benchmark_claim.py",
        "README.md",
        "docs/5-minute-local-run.md",
        "docs/design-v0.10-saved-trace-machine-evidence.md",
        "data/v0.10/dataset_card.md",
        "release/v0.10.0.md",
        "release/v0.10-machine-evidence/README.md",
        "reports/v0.10-machine-evidence-report.md",
    )
    network_check = run_script(
        "scripts/check_no_network_calls.py",
        "baselines",
        "ctxgov_adapter",
        "scoring",
        "scripts",
        "tests",
        "review",
        "adapters",
    )
    redaction = json.loads(redaction_path.read_text(encoding="utf-8"))
    custody = json.loads(custody_path.read_text(encoding="utf-8"))

    failures: list[dict[str, Any]] = []
    if generate["returncode"] != 0:
        failures.append({"generate": generate})
    if missing:
        failures.append({"missing_files": missing})
    if validation.get("legacy_label_field_rows") != 0:
        failures.append({"legacy_label_field_rows": validation.get("legacy_label_field_rows")})
    if validation.get("unlabeled_splits") != ["hidden_holdout"]:
        failures.append({"unlabeled_splits": validation.get("unlabeled_splits")})
    if hidden_label_case_ids:
        failures.append({"hidden_label_case_ids": hidden_label_case_ids})
    if redaction.get("source_selection") != "non_picked_saved_trace_cohort":
        failures.append({"source_selection": redaction.get("source_selection")})
    if redaction.get("raw_private_trace_published") is not False:
        failures.append({"raw_private_trace_published": redaction.get("raw_private_trace_published")})
    if custody.get("custody_status") != "sealed_not_scored_publicly":
        failures.append({"custody_status": custody.get("custody_status")})
    if build_report["returncode"] != 0:
        failures.append({"build_report": build_report})
    if report.get("status") != "pass_machine_evidence_public_label_scoring":
        failures.append({"machine_evidence_report_status": report.get("status")})
    if "redaction_receipt" not in report:
        failures.append({"redaction_receipt": "missing"})
    if report.get("hidden_labels_used_for_scoring") is not False:
        failures.append({"hidden_labels_used_for_scoring": report.get("hidden_labels_used_for_scoring")})
    for field in [
        "public_benchmark_claim_allowed",
        "human_reviewer_claim_allowed",
        "adoption_claim_allowed",
        "provider_model_compatibility_claim_allowed",
        "package_release_claim_allowed",
    ]:
        if report.get(field) is not False:
            failures.append({field: report.get(field)})
    private_issues = private_text_issues(
        [
            ROOT / "README.md",
            ROOT / "docs" / "5-minute-local-run.md",
            ROOT / "docs" / "design-v0.10-saved-trace-machine-evidence.md",
            ROOT / "data" / "v0.10" / "dataset_card.md",
            ROOT / "release" / "v0.10.0.md",
            ROOT / "release" / "v0.10-machine-evidence" / "README.md",
            ROOT / "reports" / "v0.10-machine-evidence-report.json",
            ROOT / "reports" / "v0.10-machine-evidence-report.md",
        ]
    )
    if private_issues:
        failures.append({"private_text_issues": private_issues})
    if claim_check["returncode"] != 0:
        failures.append({"claim_check": claim_check})
    if network_check["returncode"] != 0:
        failures.append({"network_check": network_check})

    status = "pass_saved_trace_machine_evidence_release_ready" if not failures else "fail_saved_trace_machine_evidence_release_ready"
    readiness = {
        "schema_version": "ach-v10-saved-trace-readiness/v0",
        "status": status,
        "case_count": validation["case_count"],
        "positive_label_count": validation["positive_label_count"],
        "clean_control_count": validation["clean_control_count"],
        "unlabeled_case_count": validation["unlabeled_case_count"],
        "hidden_holdout_case_count": custody.get("hidden_holdout_case_count"),
        "redaction_receipt": "release/v0.10-machine-evidence/redaction-receipt.json",
        "machine_evidence_report": "reports/v0.10-machine-evidence-report.json",
        "author_approval_recorded": True,
        "publication_allowed": True,
        "public_benchmark_claim_allowed": False,
        "human_reviewer_claim_allowed": False,
        "adoption_claim_allowed": False,
        "provider_model_calls_allowed": False,
        "package_release_claim_allowed": False,
        "claim_check": claim_check,
        "network_check": network_check,
        "failures": failures,
    }
    print(json.dumps(readiness, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
