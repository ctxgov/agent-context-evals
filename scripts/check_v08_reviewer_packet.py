from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    issues: list[dict[str, str]] = []
    required_paths = [
        ROOT / "data" / "v0.8" / "eval_hardening_cases.jsonl",
        ROOT / "data" / "v0.8" / "eval_hardening_labels.jsonl",
        ROOT / "data" / "v0.8" / "eval_hardening_manifest.json",
        ROOT / "review" / "v08-reviewer-sheet-template.csv",
        ROOT / "review" / "v08-reviewer-protocol.md",
        ROOT / "review" / "v08-adjudication-log-template.md",
    ]
    for path in required_paths:
        if not path.exists():
            issues.append({"kind": "missing_file", "path": str(path.relative_to(ROOT))})

    if not issues:
        _check_manifest(issues)
        _check_reviewer_sheet(issues)
        _check_text_boundaries(issues)

    report = {
        "schema_id": "agent-context-evals.v08-reviewer-packet-check/v1",
        "status": "pass" if not issues else "fail",
        "issue_count": len(issues),
        "issues": issues,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not issues else 1


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _check_manifest(issues: list[dict[str, str]]) -> None:
    manifest_path = ROOT / "data" / "v0.8" / "eval_hardening_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = _read_jsonl(ROOT / "data" / "v0.8" / "eval_hardening_cases.jsonl")
    labels = _read_jsonl(ROOT / "data" / "v0.8" / "eval_hardening_labels.jsonl")
    if manifest.get("schema_id") != "agent-context-evals.eval-hardening-suite/v0.8":
        issues.append({"kind": "schema_id", "path": str(manifest_path.relative_to(ROOT))})
    if manifest.get("case_count") != len(cases) or manifest.get("label_count") != len(labels):
        issues.append({"kind": "count_mismatch", "path": str(manifest_path.relative_to(ROOT))})
    if manifest.get("hard_negative_count", 0) < 50:
        issues.append({"kind": "hard_negative_count", "path": str(manifest_path.relative_to(ROOT))})
    if manifest.get("self_audit_case_count") != 4:
        issues.append({"kind": "self_audit_case_count", "path": str(manifest_path.relative_to(ROOT))})
    if manifest.get("reviewer_packet_labels_public") is not False:
        issues.append({"kind": "reviewer_labels_public", "path": str(manifest_path.relative_to(ROOT))})
    for key, value in manifest.get("claim_boundary", {}).items():
        if value is not False:
            issues.append({"kind": "claim_boundary", "path": str(manifest_path.relative_to(ROOT)), "detail": key})


def _check_reviewer_sheet(issues: list[dict[str, str]]) -> None:
    sheet_path = ROOT / "review" / "v08-reviewer-sheet-template.csv"
    with sheet_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.seekable() and rows[0].keys() if rows else []
    forbidden_fields = {
        "expected_finding_type",
        "expected_finding_types",
        "expected_evidence_span",
        "finding_type",
        "must_flag",
        "hard_negative",
    }
    if len(rows) < 54:
        issues.append({"kind": "reviewer_sheet_row_count", "path": str(sheet_path.relative_to(ROOT))})
    if forbidden_fields & set(fieldnames):
        issues.append({"kind": "reviewer_sheet_leaks_labels", "path": str(sheet_path.relative_to(ROOT))})
    required = {"case_id", "ai_context", "reviewer_finding_type", "reviewer_evidence_span", "reviewer_notes"}
    if rows and not required.issubset(set(rows[0].keys())):
        issues.append({"kind": "reviewer_sheet_missing_fields", "path": str(sheet_path.relative_to(ROOT))})


def _check_text_boundaries(issues: list[dict[str, str]]) -> None:
    for path in [
        ROOT / "README.md",
        ROOT / "reports" / "v0.8-results.md",
        ROOT / "release" / "v0.8.0.md",
        ROOT / "review" / "v08-reviewer-protocol.md",
        ROOT / "review" / "v08-adjudication-log-template.md",
    ]:
        text = path.read_text(encoding="utf-8")
        for phrase in [
            "No public benchmark claim",
            "No provider/model call",
            "No adoption claim",
        ]:
            if phrase not in text:
                issues.append({"kind": "missing_boundary_phrase", "path": str(path.relative_to(ROOT)), "detail": phrase})
        for forbidden in ["/Users/", "BEGIN PRIVATE KEY", "sk-", "ghp_"]:
            if forbidden in text:
                issues.append({"kind": "private_or_secret_text", "path": str(path.relative_to(ROOT)), "detail": forbidden})


if __name__ == "__main__":
    raise SystemExit(main())
