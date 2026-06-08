#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


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


def private_text_issues(paths: list[Path]) -> list[dict[str, Any]]:
    forbidden = ["/Users/", "/private/tmp", "/var/folders/", "BEGIN PRIVATE KEY", "sk-", "ghp_", "gho_"]
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
    receipt_path = ROOT / "release" / "v0.11-fresh-clone-reproducibility" / "fresh-clone-receipt.json"
    release_notes_path = ROOT / "release" / "v0.11.0.md"
    required_files = [
        receipt_path,
        release_notes_path,
        ROOT / "scripts" / "run_fresh_clone_reproducibility.py",
        ROOT / "scripts" / "check_v11_fresh_clone_receipt.py",
        ROOT / "tests" / "test_v11_fresh_clone_reproducibility.py",
        ROOT / ".github" / "workflows" / "ci.yml",
    ]
    missing = require_files(required_files)
    receipt: dict[str, Any] = {}
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    failures: list[dict[str, Any]] = []
    if missing:
        failures.append({"missing_files": missing})
    expected_fields = {
        "schema_version": "ach-fresh-clone-reproducibility-v0.11",
        "status": "pass_fresh_clone_reproducibility",
        "release_version": "v0.11.0",
        "source_repo": "https://github.com/ctxgov/agent-context-evals.git",
        "source_ref": "v0.10.0",
        "fresh_clone": True,
        "worktree_reused": False,
        "local_private_paths_published": False,
        "publication_allowed": True,
    }
    for key, expected in expected_fields.items():
        if receipt.get(key) != expected:
            failures.append({key: receipt.get(key)})
    if not isinstance(receipt.get("source_commit"), str) or len(receipt.get("source_commit", "")) < 7:
        failures.append({"source_commit": receipt.get("source_commit")})

    checks = receipt.get("checks", [])
    check_by_command = {entry.get("command"): entry for entry in checks if isinstance(entry, dict)}
    for command in [
        "python3 scripts/check_v10_saved_trace_readiness.py",
        "python3 -m unittest discover -s tests -v",
    ]:
        entry = check_by_command.get(command)
        if not entry:
            failures.append({"missing_check": command})
        elif entry.get("returncode") != 0:
            failures.append({"failed_check": command, "returncode": entry.get("returncode")})
    v10_summary = check_by_command.get("python3 scripts/check_v10_saved_trace_readiness.py", {}).get("stdout_summary", {})
    if v10_summary.get("status") != "pass_saved_trace_machine_evidence_release_ready":
        failures.append({"v10_readiness_status": v10_summary.get("status")})

    boundaries = receipt.get("claim_boundaries", {})
    for field in [
        "public_benchmark_claim_allowed",
        "security_claim_allowed",
        "provider_model_compatibility_claim_allowed",
        "adoption_claim_allowed",
        "human_reviewer_claim_allowed",
        "package_release_claim_allowed",
        "stable_protocol_claim_allowed",
    ]:
        if boundaries.get(field) is not False:
            failures.append({field: boundaries.get(field)})

    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    if "check_v11_fresh_clone_receipt.py" not in ci_text:
        failures.append({"ci_entrypoint": "missing check_v11_fresh_clone_receipt.py"})

    claim_check = run_script(
        "scripts/check_no_benchmark_claim.py",
        "README.md",
        "release/v0.11.0.md",
        "release/v0.11-fresh-clone-reproducibility/fresh-clone-receipt.json",
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
    if claim_check["returncode"] != 0:
        failures.append({"claim_check": claim_check})
    if network_check["returncode"] != 0:
        failures.append({"network_check": network_check})

    private_issues = private_text_issues(
        [
            ROOT / "README.md",
            release_notes_path,
            receipt_path,
        ]
    )
    if private_issues:
        failures.append({"private_text_issues": private_issues})

    status = "pass_fresh_clone_reproducibility_release_ready" if not failures else "fail_fresh_clone_reproducibility_release_ready"
    readiness = {
        "schema_version": "ach-v11-fresh-clone-reproducibility-readiness/v0",
        "status": status,
        "receipt": "release/v0.11-fresh-clone-reproducibility/fresh-clone-receipt.json",
        "source_ref": receipt.get("source_ref"),
        "source_commit": receipt.get("source_commit"),
        "publication_allowed": not failures,
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
