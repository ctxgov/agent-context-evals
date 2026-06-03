from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline no-op baseline for future LLM-judge comparisons. It intentionally performs no model call."
    )
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "baseline": "llm_judge_baseline",
        "status": "not_run",
        "reason": "No provider/model calls are allowed in the v0.1 local benchmark skeleton.",
        "cases": str(args.cases),
    }
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
