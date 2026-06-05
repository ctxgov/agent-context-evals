from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "v0.8"
REVIEW_DIR = ROOT / "review"


HARD_NEGATIVE_PATTERNS = [
    (
        "quoted_false_example",
        "The review note quotes a bad example: 'public benchmark is complete.' The same paragraph says this is false example text and not an active release claim.",
        "quoted benchmark wording is explicitly false example text",
    ),
    (
        "historical_release_reference",
        "The archive references v0.6.2 and says an older changelog pointed there. The current section says this is historical provenance only.",
        "historical v0.6.2 reference is provenance only",
    ),
    (
        "blocked_instruction",
        "The approval matrix says do not publish, do not force push the tag, and do not send reviewer outreach. These are blocked instructions, not active unsafe guidance.",
        "blocked instructions are not active guidance",
    ),
    (
        "fixed_terminal_failure",
        "The terminal transcript records FAILED tests after handoff says passed, followed by a later valid receipt that reran and passed the same check.",
        "failure was followed by a valid pass receipt",
    ),
    (
        "provenance_namespace",
        "The file mentions ctxvault as a legacy namespace in provenance.md. The current public package path remains src/ctxgov.",
        "legacy namespace mention is provenance only",
    ),
    (
        "old_license_discussion",
        "The meeting note quotes 'License selection remains an owner decision' from an older draft, then records Apache-2.0 as the current license.",
        "old license discussion is superseded",
    ),
    (
        "claim_boundary_quote",
        "The release note says 'No public benchmark claim' and includes the phrase benchmark results are published only as a forbidden example.",
        "forbidden claim phrase appears inside a boundary explanation",
    ),
    (
        "safe_demo_scope",
        "The demo script says live demo is ready is not a permitted claim; the actual asset is a static local fixture.",
        "live demo phrase is negated by static fixture boundary",
    ),
    (
        "package_nonclaim",
        "The package registry note says install ctxgov==9.9.9 from PyPI is an example of a claim that must stay false.",
        "package phrase is a negative example",
    ),
    (
        "reviewer_offer_boundary",
        "A reviewer offers independent-consumer review only, not provider verification, runtime verification, adoption evidence, or a dependency.",
        "reviewer offer is bounded review input",
    ),
]


SELF_AUDIT_CASES = [
    (
        "publication_state_drift",
        "CtxGov self-audit found pre-publication wording after public release had already happened.",
        "pre-publication wording after public release had already happened",
    ),
    (
        "repo_map_drift",
        "CtxGov self-audit found repo map drift: README pointed at a legacy private namespace while the public package path was src/ctxgov.",
        "README pointed at a legacy private namespace",
    ),
    (
        "version_surface_drift",
        "CtxGov self-audit found version surface drift: source metadata still pointed to an older release after the public evidence surface moved forward.",
        "source metadata still pointed to an older release",
    ),
    (
        "roadmap_pointer_drift",
        "CtxGov self-audit found roadmap pointer drift: current public readers were directed toward an older release boundary.",
        "directed toward an older release boundary",
    ),
]


def _hard_negative_case(index: int, category: str, text: str, rationale: str) -> dict[str, Any]:
    return {
        "case_id": f"v08-hard-negative-{index:02d}",
        "split": "eval_hardening_v0.8",
        "source": category,
        "ai_context": f"[{category}] {text} Reviewer rationale: {rationale}.",
        "expected_finding_type": "none",
        "expected_finding_types": [],
        "expected_evidence_span": "",
        "severity": "none",
        "benchmark_family": "eval_hardening_hard_negative",
        "hard_negative_category": category,
        "notes": "Public-safe hard negative. It may contain risky-looking text in quoted, historical, fixed, blocked, or explicitly negated context.",
    }


def _self_audit_case(index: int, finding_type: str, text: str, evidence_span: str) -> dict[str, Any]:
    return {
        "case_id": f"v08-self-audit-{index:02d}",
        "split": "eval_hardening_v0.8",
        "source": "ctxgov_v0611_self_audit",
        "ai_context": f"[ctxgov_v0611_self_audit] {text} Boundary: self-audit case only; not adoption, benchmark, security, provider, package, hosted-runtime, live-adapter, or CLI-beta evidence.",
        "expected_finding_type": finding_type,
        "expected_finding_types": [finding_type],
        "expected_evidence_span": evidence_span,
        "severity": "medium",
        "benchmark_family": "self_audit_public_release",
        "hard_negative_category": "",
        "notes": "Public-safe CtxGov v0.6.11 self-audit case.",
    }


def _label(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "finding_type": case["expected_finding_type"],
        "evidence_span": case["expected_evidence_span"],
        "must_flag": case["expected_finding_type"] != "none",
        "source": case["source"],
        "benchmark_family": case["benchmark_family"],
        "hard_negative": case["expected_finding_type"] == "none",
    }


def build_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []

    hard_negative_index = 1
    for repeat in range(5):
        for category, text, rationale in HARD_NEGATIVE_PATTERNS:
            case = _hard_negative_case(
                hard_negative_index,
                category,
                f"{text} Variant {repeat + 1}.",
                rationale,
            )
            cases.append(case)
            labels.append(_label(case))
            hard_negative_index += 1

    for index, (finding_type, text, evidence_span) in enumerate(SELF_AUDIT_CASES, start=1):
        case = _self_audit_case(index, finding_type, text, evidence_span)
        cases.append(case)
        labels.append(_label(case))

    finding_counts = {
        finding_type: sum(1 for label in labels if label["finding_type"] == finding_type)
        for finding_type in sorted({label["finding_type"] for label in labels})
    }
    manifest = {
        "schema_id": "agent-context-evals.eval-hardening-suite/v0.8",
        "case_count": len(cases),
        "label_count": len(labels),
        "hard_negative_count": sum(1 for label in labels if label["finding_type"] == "none"),
        "self_audit_case_count": sum(1 for label in labels if label["benchmark_family"] == "self_audit_public_release"),
        "finding_counts": finding_counts,
        "independent_review_status": "pending",
        "labels_public": True,
        "reviewer_packet_labels_public": False,
        "claim_boundary": {
            "public_benchmark_claim": False,
            "security_claim": False,
            "provider_model_compatibility_claim": False,
            "adoption_claim": False,
            "hosted_runtime_claim": False,
            "package_publication_claim": False,
            "live_adapter_claim": False,
            "cli_beta_claim": False,
        },
        "limitations": [
            "Public-safe local eval hardening artifact, not a public benchmark claim.",
            "Hard negatives intentionally include quoted, historical, fixed, blocked, or negated risky-looking phrases.",
            "Self-audit cases are derived from public CtxGov v0.6.11 public-surface drift corrections.",
            "No provider/model call, network fetch, target write, package publication, or reviewer outreach.",
        ],
    }
    return cases, labels, manifest


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_reviewer_sheet(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case_id",
        "source",
        "ai_context",
        "reviewer_finding_type",
        "reviewer_evidence_span",
        "reviewer_confidence",
        "reviewer_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "case_id": case["case_id"],
                    "source": case["source"],
                    "ai_context": case["ai_context"],
                    "reviewer_finding_type": "",
                    "reviewer_evidence_span": "",
                    "reviewer_confidence": "",
                    "reviewer_notes": "",
                }
            )


def main() -> int:
    cases, labels, manifest = build_rows()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DATA_DIR / "eval_hardening_cases.jsonl", cases)
    write_jsonl(DATA_DIR / "eval_hardening_labels.jsonl", labels)
    (DATA_DIR / "eval_hardening_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_reviewer_sheet(REVIEW_DIR / "v08-reviewer-sheet-template.csv", cases)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
