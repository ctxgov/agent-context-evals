from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


CTXGOV_TO_EVAL = {
    "stale_context": "stale_claim",
    "conflicting_instruction": "conflicting_policy",
    "unsupported_claim": "unsupported_release_claim",
    "release_link_404": "unsupported_release_claim",
    "package_registry_unverified": "unsupported_release_claim",
    "release_artifact_missing": "unsupported_release_claim",
    "action_or_publication_without_evidence": "unsafe_action_guidance",
    "terminal_failure_hidden": "hidden_terminal_failure",
    "memory_without_lifecycle_or_rollback": "missing_rollback",
    "memory_missing_source_coverage": "missing_source_coverage",
    "memory_missing_rollback": "missing_rollback",
    "memory_unbounded_consequence": "unbounded_consequence",
    "memory_missing_model_state_surface": "missing_model_state_surface",
    "task_shard_schema_conflict": "conflicting_policy",
    "task_shard_unapproved_side_effect": "unsafe_action_guidance",
    "task_shard_missing_rollback": "missing_rollback",
}

SINGLE_LABEL_PRIORITY_BY_FAMILY = {
    "release_integrity_claim_lint_eval": ["unsupported_release_claim"],
    "session_continuity_hidden_holdout_eval": ["hidden_terminal_failure", "stale_claim"],
    "task_shard_context_control_eval": ["conflicting_policy", "unsafe_action_guidance", "missing_rollback"],
    "memory_xray_l1_eval": [
        "missing_source_coverage",
        "missing_rollback",
        "unbounded_consequence",
        "missing_model_state_surface",
    ],
}


def read_cases(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def map_ctxgov_finding(finding_type: str) -> str | None:
    return CTXGOV_TO_EVAL.get(finding_type)


def prediction_from_ctxgov_finding(case_id: str, finding: dict[str, Any]) -> dict | None:
    ctxgov_finding_type = str(finding.get("finding_type", ""))
    mapped = map_ctxgov_finding(ctxgov_finding_type)
    if mapped is None:
        return None
    evidence_span = str(finding.get("evidence_span") or finding.get("reason") or "")
    return {
        "case_id": case_id,
        "finding_type": mapped,
        "evidence_span": evidence_span,
        "confidence": 0.7,
        "source": "ctxgov_doctor",
        "ctxgov_finding_type": ctxgov_finding_type,
    }


def select_ctxgov_predictions(case: dict, predictions: list[dict]) -> list[dict]:
    """Project multi-finding doctor output onto the current single-label eval rows."""

    priority = SINGLE_LABEL_PRIORITY_BY_FAMILY.get(str(case.get("benchmark_family", "")))
    if not priority:
        return predictions

    for finding_type in priority:
        selected = [prediction for prediction in predictions if prediction["finding_type"] == finding_type]
        if selected:
            return selected[:1]
    return predictions


def materialize_case_workspace(case: dict, root: Path) -> Path:
    case_dir = root / case["case_id"]
    logs_dir = case_dir / "logs"
    docs_dir = case_dir / "docs"
    memory_dir = case_dir / "memory"
    logs_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)

    text = str(case.get("ai_context", ""))
    source = str(case.get("source", "")).lower()
    (case_dir / "AGENTS.md").write_text(text + "\n", encoding="utf-8")
    if "terminal" in source or "log" in source or "failed" in text.lower():
        (logs_dir / "terminal.log").write_text(text + "\n", encoding="utf-8")
    if "release" in text.lower() or "claim" in source:
        (docs_dir / "public-claims.md").write_text(text + "\n", encoding="utf-8")
    if "memory" in source or "memory" in text.lower() or "rollback" in text.lower():
        (memory_dir / "session-summary.md").write_text(text + "\n", encoding="utf-8")
    return case_dir


def predict_heuristic(case: dict) -> dict | None:
    text = str(case.get("ai_context", ""))
    lowered = text.lower()
    finding_type = None
    evidence = ""

    if ("failed" in lowered or "exit code 1" in lowered or "404" in lowered) and (
        "passed" in lowered or "ready" in lowered or "live" in lowered
    ):
        finding_type = "hidden_terminal_failure" if "failed" in lowered or "exit code 1" in lowered else "unsupported_release_claim"
        evidence = "FAILED" if "failed" in lowered else "404"
    elif "release" in lowered and ("404" in lowered or "missing" in lowered or "not found" in lowered):
        finding_type = "unsupported_release_claim"
        evidence = "404" if "404" in lowered else "missing"
    elif (
        ("allowed" in lowered and "not allowed" in lowered)
        or ("no network" in lowered and "network is approved" in lowered)
        or "schema import allowed and blocked" in lowered
    ):
        finding_type = "conflicting_policy"
        evidence = "schema import allowed and blocked" if "schema import allowed and blocked" in lowered else "network"
    elif any(word in lowered for word in ["deploy now", "push to main", "upload to pypi", "delete production", "apply shard"]) and (
        "without approval" in lowered
        or "without approval or rollback" in lowered
        or "approval" not in lowered
        or "rollback" not in lowered
    ):
        finding_type = "unsafe_action_guidance"
        evidence = "deploy now" if "deploy now" in lowered else "apply shard"
    elif ("blocked" in lowered or "pending approval" in lowered) and ("ready" in lowered or "published" in lowered or "passed" in lowered):
        finding_type = "stale_claim"
        evidence = "pending approval" if "pending approval" in lowered else "blocked"
    elif "source coverage" in lowered and "missing" in lowered:
        finding_type = "missing_source_coverage"
        evidence = "source coverage"
    elif "rollback" in lowered and ("missing" in lowered or "none" in lowered):
        finding_type = "missing_rollback"
        evidence = "rollback"
    elif "consequence" in lowered and ("unbounded" in lowered or "no ceiling" in lowered):
        finding_type = "unbounded_consequence"
        evidence = "consequence"
    elif "model-state surface" in lowered and ("missing" in lowered or "absent" in lowered):
        finding_type = "missing_model_state_surface"
        evidence = "model-state surface"

    if finding_type is None:
        return None
    return {
        "case_id": case["case_id"],
        "finding_type": finding_type,
        "evidence_span": evidence or text[:120],
        "confidence": 0.55,
        "source": "ctxgov_adapter_heuristic",
        "note": "Fallback heuristic mode. Does not read labels; use --mode doctor with --ctxgov-root for CtxGov doctor invocation.",
    }


def _doctor_command(ctxgov_root: Path, case_dir: Path, output_dir: Path) -> tuple[list[str], dict[str, str]]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ctxgov_root / "src")
    cmd = [
        sys.executable,
        "-m",
        "ctxgov.cli",
        "doctor",
        "--path",
        str(case_dir),
        "--output",
        str(output_dir),
        "--include-report",
    ]
    return cmd, env


def predict_with_ctxgov_doctor(case: dict, ctxgov_root: Path, workspace_root: Path) -> list[dict]:
    case_dir = materialize_case_workspace(case, workspace_root)
    output_dir = case_dir / ".ctxgov" / "health"
    cmd, env = _doctor_command(ctxgov_root, case_dir, output_dir)
    result = subprocess.run(cmd, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return []

    payload = json.loads(result.stdout)
    findings: list[dict[str, Any]] = payload.get("report", {}).get("findings", [])
    predictions = []
    seen: set[str] = set()
    for finding in findings:
        prediction = prediction_from_ctxgov_finding(case["case_id"], finding)
        if prediction is None or prediction["finding_type"] in seen:
            continue
        seen.add(prediction["finding_type"])
        predictions.append(prediction)
    return select_ctxgov_predictions(case, predictions)


def run_cases(cases: list[dict], *, mode: str, ctxgov_root: Path | None = None) -> list[dict]:
    predictions: list[dict] = []
    if mode == "doctor":
        if ctxgov_root is None:
            raise ValueError("--ctxgov-root is required for --mode doctor")
        with tempfile.TemporaryDirectory(prefix="ctxgov-eval-") as tmp:
            workspace = Path(tmp)
            for case in cases:
                predictions.extend(predict_with_ctxgov_doctor(case, ctxgov_root, workspace))
        return predictions

    for case in cases:
        prediction = predict_heuristic(case)
        if prediction:
            predictions.append(prediction)
    return predictions


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CtxGov adapter over Agent Context Health cases.")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["heuristic", "doctor"], default="heuristic")
    parser.add_argument("--ctxgov-root", type=Path)
    args = parser.parse_args()

    predictions = run_cases(read_cases(args.cases), mode=args.mode, ctxgov_root=args.ctxgov_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for prediction in predictions:
            handle.write(json.dumps(prediction, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
