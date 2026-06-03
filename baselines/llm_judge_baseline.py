from __future__ import annotations

import argparse
import json
from pathlib import Path


FINDING_TYPES = [
    "stale_claim",
    "conflicting_policy",
    "unsupported_release_claim",
    "unsafe_action_guidance",
    "hidden_terminal_failure",
    "missing_source_coverage",
    "missing_rollback",
    "unbounded_consequence",
    "missing_model_state_surface",
    "none",
]

PROMPT_VERSION = "v0.3-offline-judge"


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _visible_case(case: dict) -> dict:
    return {
        key: value
        for key, value in case.items()
        if key
        not in {
            "expected_finding_type",
            "expected_evidence_span",
            "rationale",
            "must_flag",
            "start_char",
            "end_char",
        }
    }


def build_prompt(case: dict) -> str:
    visible = _visible_case(case)
    taxonomy = "\n".join(f"- {finding_type}" for finding_type in FINDING_TYPES)
    return f"""You are labeling one Agent Context Health case.

Allowed finding_type values:
{taxonomy}

Return one JSON object with exactly these fields:
{{"case_id": "{visible.get("case_id", "")}", "finding_type": "...", "evidence_span": "...", "confidence": 0.0, "rationale": "..."}}

Rules:
- Use "none" only when no listed context-health hazard is present.
- For a positive finding, evidence_span must be a minimal exact substring from ai_context.
- Do not infer from project reputation, author intent, or external knowledge.
- Prefer the hazard that would most directly mislead the next AI agent run.

Case:
{json.dumps(visible, indent=2, sort_keys=True)}
"""


def _prompt_rows(cases: list[dict]) -> list[dict]:
    return [
        {
            "case_id": case["case_id"],
            "prompt_version": PROMPT_VERSION,
            "prompt": build_prompt(case),
        }
        for case in cases
    ]


def _validate_decision(decision: dict, cases_by_id: dict[str, dict]) -> dict:
    case_id = str(decision.get("case_id", ""))
    if case_id not in cases_by_id:
        raise ValueError(f"review decision references unknown case_id: {case_id}")

    finding_type = str(decision.get("finding_type", ""))
    if finding_type not in FINDING_TYPES:
        raise ValueError(f"invalid finding_type for {case_id}: {finding_type}")

    evidence_span = str(decision.get("evidence_span", ""))
    ai_context = str(cases_by_id[case_id].get("ai_context", ""))
    if finding_type != "none" and evidence_span not in ai_context:
        raise ValueError(f"evidence_span for {case_id} is not an exact substring of ai_context")

    return {
        "case_id": case_id,
        "finding_type": finding_type,
        "evidence_span": evidence_span,
        "confidence": float(decision.get("confidence", 0.0)),
        "rationale": str(decision.get("rationale", "")),
        "source": "llm_judge_baseline_offline_decisions",
        "prompt_version": PROMPT_VERSION,
    }


def _load_review_decisions(path: Path | None, cases_by_id: dict[str, dict]) -> list[dict]:
    if path is None:
        return []
    return [_validate_decision(row, cases_by_id) for row in read_jsonl(path)]


def run_offline_judge(
    cases: Path,
    output: Path,
    manifest: Path | None = None,
    prompt_output: Path | None = None,
    *,
    provider: str = "disabled",
    model: str = "offline-review-template",
    review_decisions: Path | None = None,
    allow_provider_call: bool = False,
) -> dict:
    if allow_provider_call:
        raise ValueError("Provider/model calls are intentionally unsupported by this offline baseline.")

    case_rows = read_jsonl(cases)
    cases_by_id = {str(row["case_id"]): row for row in case_rows}
    prompt_path = prompt_output or output.with_suffix(".prompts.jsonl")
    manifest_path = manifest or output.with_suffix(".manifest.json")
    decision_rows = _load_review_decisions(review_decisions, cases_by_id)
    predictions = [row for row in decision_rows if row["finding_type"] != "none"]

    write_jsonl(prompt_path, _prompt_rows(case_rows))
    write_jsonl(output, predictions)

    manifest_payload = {
        "baseline": "llm_judge_baseline",
        "version": PROMPT_VERSION,
        "status": "offline_decisions" if review_decisions else "dry_run",
        "claim_boundary": "This baseline prepares or ingests offline judge decisions; it does not call an LLM provider.",
        "cases": str(cases),
        "case_count": len(case_rows),
        "output": str(output),
        "prompt_output": str(prompt_path),
        "review_decisions": str(review_decisions) if review_decisions else None,
        "offline_decision_count": len(decision_rows),
        "provider": provider,
        "model": model,
        "side_effects": {
            "provider_or_model_call_performed": False,
            "network_access_required": False,
            "writes_predictions_only_from_review_decisions": True,
        },
        "prompt_contract": {
            "allowed_finding_types": FINDING_TYPES,
            "requires_exact_evidence_span": True,
            "labels_exposed_to_prompt": False,
        },
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline LLM-judge harness. It writes prompts and can ingest offline decisions, but performs no model call."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--prompt-output", type=Path)
    parser.add_argument("--provider", default="disabled")
    parser.add_argument("--model", default="offline-review-template")
    parser.add_argument("--review-decisions", type=Path)
    parser.add_argument("--allow-provider-call", action="store_true")
    args = parser.parse_args()

    try:
        run_offline_judge(
            args.cases,
            args.output,
            args.manifest,
            args.prompt_output,
            provider=args.provider,
            model=args.model,
            review_decisions=args.review_decisions,
            allow_provider_call=args.allow_provider_call,
        )
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
