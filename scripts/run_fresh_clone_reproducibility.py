#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "https://github.com/ctxgov/agent-context-evals.git"
DEFAULT_REF = "v0.10.0"
DEFAULT_OUTPUT = ROOT / "release" / "v0.11-fresh-clone-reproducibility" / "fresh-clone-receipt.json"


def sanitize(text: str, tmp_root: Path, clone_dir: Path) -> str:
    sanitized = text.replace(str(clone_dir), "<fresh-clone-repo>")
    sanitized = sanitized.replace(str(tmp_root), "<fresh-clone-tempdir>")
    sanitized = re.sub(r"/private/tmp/[^\s'\"<>]+", "<fresh-clone-tempdir>", sanitized)
    sanitized = re.sub(r"/tmp/[^\s'\"<>]+", "<fresh-clone-tempdir>", sanitized)
    sanitized = re.sub(r"/var/folders/[^\s'\"<>]+", "<fresh-clone-tempdir>", sanitized)
    return sanitized


def compact_lines(text: str, tmp_root: Path, clone_dir: Path, *, limit: int = 24) -> list[str]:
    lines = [sanitize(line.strip(), tmp_root, clone_dir) for line in text.splitlines() if line.strip()]
    if len(lines) <= limit:
        return lines
    return [*lines[: limit // 2], "...", *lines[-(limit // 2) :]]


def summarize_json_stdout(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    keys = [
        "schema_version",
        "status",
        "case_count",
        "positive_label_count",
        "clean_control_count",
        "unlabeled_case_count",
        "hidden_holdout_case_count",
        "publication_allowed",
        "public_benchmark_claim_allowed",
        "human_reviewer_claim_allowed",
        "adoption_claim_allowed",
        "provider_model_calls_allowed",
        "package_release_claim_allowed",
    ]
    return {key: payload[key] for key in keys if key in payload}


def run_command(
    command: list[str],
    *,
    cwd: Path | None,
    display_command: str,
    tmp_root: Path,
    clone_dir: Path,
    include_stdout_summary: bool = False,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    summary: dict[str, Any] = {
        "command": display_command,
        "returncode": result.returncode,
        "stdout_lines": compact_lines(result.stdout, tmp_root, clone_dir),
        "stderr_lines": compact_lines(result.stderr, tmp_root, clone_dir),
    }
    if include_stdout_summary:
        summary["stdout_summary"] = summarize_json_stdout(result.stdout)
    return summary


def build_receipt(repo_url: str, ref: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="agent-context-evals-fresh-clone-") as tmp_name:
        tmp_root = Path(tmp_name)
        clone_dir = tmp_root / "repo"
        clone = run_command(
            ["git", "-c", "advice.detachedHead=false", "clone", "--depth", "1", "--branch", ref, repo_url, str(clone_dir)],
            cwd=None,
            display_command=f"git -c advice.detachedHead=false clone --depth 1 --branch {ref} {repo_url} <fresh-clone-repo>",
            tmp_root=tmp_root,
            clone_dir=clone_dir,
        )

        source_commit = ""
        checks: list[dict[str, Any]] = []
        if clone["returncode"] == 0:
            commit = run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=clone_dir,
                display_command="git rev-parse HEAD",
                tmp_root=tmp_root,
                clone_dir=clone_dir,
            )
            if commit["returncode"] == 0 and commit["stdout_lines"]:
                source_commit = commit["stdout_lines"][0]

            v10 = run_command(
                ["python3", "scripts/check_v10_saved_trace_readiness.py"],
                cwd=clone_dir,
                display_command="python3 scripts/check_v10_saved_trace_readiness.py",
                tmp_root=tmp_root,
                clone_dir=clone_dir,
                include_stdout_summary=True,
            )
            checks.append(v10)

            tests = run_command(
                ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=clone_dir,
                display_command="python3 -m unittest discover -s tests -v",
                tmp_root=tmp_root,
                clone_dir=clone_dir,
            )
            checks.append(tests)

    failures = []
    if clone["returncode"] != 0:
        failures.append({"clone_returncode": clone["returncode"]})
    for check in checks:
        if check["returncode"] != 0:
            failures.append({"command": check["command"], "returncode": check["returncode"]})

    return {
        "schema_version": "ach-fresh-clone-reproducibility-v0.11",
        "status": "pass_fresh_clone_reproducibility" if not failures else "fail_fresh_clone_reproducibility",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generated_by": "scripts/run_fresh_clone_reproducibility.py",
        "release_version": "v0.11.0",
        "receipt_scope": "fresh clone of the v0.10.0 public local evidence path, published by v0.11.0",
        "source_repo": repo_url,
        "source_ref": ref,
        "source_commit": source_commit,
        "fresh_clone": True,
        "worktree_reused": False,
        "clone_depth": 1,
        "clone": clone,
        "checks": checks,
        "claim_boundaries": {
            "public_benchmark_claim_allowed": False,
            "security_claim_allowed": False,
            "provider_model_compatibility_claim_allowed": False,
            "adoption_claim_allowed": False,
            "human_reviewer_claim_allowed": False,
            "package_release_claim_allowed": False,
            "stable_protocol_claim_allowed": False,
        },
        "default_eval_network_allowed": False,
        "release_operation_network_required": True,
        "local_private_paths_published": False,
        "publication_allowed": True,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a public-safe fresh-clone reproducibility receipt.")
    parser.add_argument("--repo-url", default=DEFAULT_REPO)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    receipt = build_receipt(args.repo_url, args.ref)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output.relative_to(ROOT)), "status": receipt["status"]}, sort_keys=True))
    return 0 if receipt["status"] == "pass_fresh_clone_reproducibility" else 1


if __name__ == "__main__":
    raise SystemExit(main())
