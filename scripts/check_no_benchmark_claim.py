#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


BLOCKED_PHRASES = [
    "public benchmark results",
    "public benchmark result",
    "public benchmark claim",
    "security guarantee",
    "provider compatibility",
    "stable protocol",
    "adoption is proven",
    "universal benchmark",
    "hallucination prevention",
]
BOUNDARY_WORDS = [
    "no ",
    "not ",
    "not a ",
    "not public",
    "do not ",
    "does not ",
    "without ",
    "blocked",
    "requires",
    "before",
    "defer",
    "limitation",
    "scaffold",
    "local-only",
    "local only",
    "gate",
    "policy",
]


def iter_lines(path: Path) -> list[tuple[int, str]]:
    return list(enumerate(path.read_text(encoding="utf-8").splitlines(), start=1))


def is_bounded(context: str, phrase: str) -> bool:
    lower = context.lower()
    phrase_index = lower.find(phrase)
    if phrase_index == -1:
        return True
    window_start = max(0, phrase_index - 80)
    window_end = min(len(lower), phrase_index + len(phrase) + 80)
    window = lower[window_start:window_end]
    return any(marker in window for marker in BOUNDARY_WORDS)


def check(paths: list[Path]) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for path in paths:
        if not path.exists():
            violations.append({"path": str(path), "line": 0, "phrase": "missing file"})
            continue
        lines = iter_lines(path)
        for offset, (line_number, line) in enumerate(lines):
            lower = line.lower()
            for phrase in BLOCKED_PHRASES:
                if phrase not in lower:
                    continue
                context_lines = [
                    lines[index][1]
                    for index in range(max(0, offset - 2), min(len(lines), offset + 3))
                ]
                context = "\n".join(context_lines)
                if not is_bounded(context, phrase):
                    violations.append(
                        {
                            "path": str(path),
                            "line": line_number,
                            "phrase": phrase,
                            "text": line.strip(),
                        }
                    )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Block unbounded benchmark/security/adoption claims.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    violations = check(args.paths)
    if violations:
        print(
            "claim check failed: unbounded public benchmark or adjacent claim wording found",
            file=sys.stderr,
        )
        print(json.dumps({"violations": violations}, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({"checked_files": len(args.paths), "violations": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
