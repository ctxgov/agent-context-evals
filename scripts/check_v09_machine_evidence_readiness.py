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


def require_files(paths: list[Path]) -> list[str]:
    return [str(path.relative_to(ROOT)) for path in paths if not path.exists()]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


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
    cases_path = ROOT / "data" / "v0.9" / "machine_evidence_cases.jsonl"
    labels_path = ROOT / "data" / "v0.9" / "machine_evidence_labels.jsonl"
    report_path = ROOT / "reports" / "v0.9-machine-evidence-report.json"
    custody_path = ROOT / "release" / "v0.9-machine-evidence" / "hidden-holdout-custody.json"
    validate_cases = load_module("ach_validate_cases", ROOT / "scripts" / "validate_cases.py")
    validation = validate_cases.validate(
        cases_path,
        labels_path,
        allow_legacy_label_fields=False,
        allow_unlabeled_splits={"hidden_holdout"},
    )

    required_files = [
        cases_path,
        labels_path,
        ROOT / "data" / "v0.9" / "dataset_card.md",
        ROOT / "data" / "v0.9" / "machine_evidence_manifest.json",
        ROOT / "data" / "v0.9" / "machine_evidence_splits.json",
        custody_path,
        ROOT / "review" / "reviewer-proxy-labels.jsonl",
        ROOT / "review" / "reviewer-proxy-adjudication.json",
        ROOT / "release" / "v0.9-machine-evidence" / "README.md",
        ROOT / "release" / "v0.9-machine-evidence" / "author-approval-packet.md",
        ROOT / "release" / "v0.9.0.md",
        ROOT / "docs" / "design-v0.9-machine-evidence.md",
        ROOT / "scripts" / "build_machine_evidence_report.py",
    ]
    missing = require_files(required_files)

    build_report = run_script(
        "scripts/build_machine_evidence_report.py",
        "--cases",
        "data/v0.9/machine_evidence_cases.jsonl",
        "--labels",
        "data/v0.9/machine_evidence_labels.jsonl",
        "--holdout-custody",
        "release/v0.9-machine-evidence/hidden-holdout-custody.json",
        "--output",
        "reports/v0.9-machine-evidence-report.json",
    )
    report: dict[str, Any] = {}
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))

    labels = read_jsonl(labels_path)
    label_case_ids = {row["case_id"] for row in labels}
    hidden_label_case_ids = sorted(label_case_ids & set(validation["unlabeled_case_ids"]))

    claim_check = run_script(
        "scripts/check_no_benchmark_claim.py",
        "README.md",
        "reports/v0.9-machine-evidence-report.md",
        "docs/design-v0.9-machine-evidence.md",
        "data/v0.9/dataset_card.md",
        "release/v0.9.0.md",
        "release/v0.9-machine-evidence/README.md",
        "release/v0.9-machine-evidence/author-approval-packet.md",
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

    proxy_report = json.loads((ROOT / "review" / "reviewer-proxy-adjudication.json").read_text(encoding="utf-8"))
    custody_report = json.loads(custody_path.read_text(encoding="utf-8"))

    failures: list[dict[str, Any]] = []
    if missing:
        failures.append({"missing_files": missing})
    if validation.get("legacy_label_field_rows") != 0:
        failures.append({"legacy_label_field_rows": validation.get("legacy_label_field_rows")})
    if validation.get("unlabeled_splits") != ["hidden_holdout"]:
        failures.append({"unlabeled_splits": validation.get("unlabeled_splits")})
    if hidden_label_case_ids:
        failures.append({"hidden_label_case_ids": hidden_label_case_ids})
    if build_report["returncode"] != 0:
        failures.append({"build_report": build_report})
    if report.get("status") != "pass_machine_evidence_public_label_scoring":
        failures.append({"machine_evidence_report_status": report.get("status")})
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
    if proxy_report.get("reviewer_source") != "machine_proxy":
        failures.append({"reviewer_source": proxy_report.get("reviewer_source")})
    if proxy_report.get("human_reviewer_claim_allowed") is not False:
        failures.append({"proxy_human_reviewer_claim_allowed": proxy_report.get("human_reviewer_claim_allowed")})
    if custody_report.get("custody_status") != "sealed_not_scored_publicly":
        failures.append({"custody_status": custody_report.get("custody_status")})
    private_issues = private_text_issues(
        [
            ROOT / "README.md",
            ROOT / "data" / "v0.9" / "dataset_card.md",
            ROOT / "docs" / "design-v0.9-machine-evidence.md",
            ROOT / "release" / "v0.9.0.md",
            ROOT / "release" / "v0.9-machine-evidence" / "README.md",
            ROOT / "release" / "v0.9-machine-evidence" / "author-approval-packet.md",
            ROOT / "reports" / "v0.9-machine-evidence-report.json",
            ROOT / "reports" / "v0.9-machine-evidence-report.md",
        ]
    )
    if private_issues:
        failures.append({"private_text_issues": private_issues})
    if claim_check["returncode"] != 0:
        failures.append({"claim_check": claim_check})
    if network_check["returncode"] != 0:
        failures.append({"network_check": network_check})

    status = "pass_machine_evidence_release_ready" if not failures else "fail_machine_evidence_release_ready"
    readiness = {
        "schema_version": "ach-v09-machine-evidence-readiness/v1",
        "status": status,
        "case_count": validation["case_count"],
        "positive_label_count": validation["positive_label_count"],
        "clean_control_count": validation["clean_control_count"],
        "unlabeled_case_count": validation["unlabeled_case_count"],
        "unlabeled_splits": validation["unlabeled_splits"],
        "hidden_holdout_case_count": custody_report.get("hidden_holdout_case_count"),
        "machine_evidence_report": "reports/v0.9-machine-evidence-report.json",
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
