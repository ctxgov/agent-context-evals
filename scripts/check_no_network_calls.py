#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


NETWORK_IMPORTS = {
    "requests",
    "aiohttp",
    "http.client",
    "urllib.request",
}
NETWORK_CALLS = {
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "requests.request",
    "aiohttp.ClientSession",
    "urllib.request.urlopen",
    "http.client.HTTPConnection",
    "http.client.HTTPSConnection",
    "socket.create_connection",
}


def python_files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(child for child in path.rglob("*.py") if child.is_file()))
        elif path.suffix == ".py":
            found.append(path)
    return found


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def check_file(path: Path) -> list[dict[str, object]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [{"path": str(path), "line": exc.lineno or 0, "issue": f"syntax error: {exc.msg}"}]

    violations: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in NETWORK_IMPORTS:
                    violations.append({"path": str(path), "line": node.lineno, "issue": f"network import {name}"})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in NETWORK_IMPORTS:
                violations.append({"path": str(path), "line": node.lineno, "issue": f"network import {module}"})
        elif isinstance(node, ast.Call):
            name = dotted_name(node.func)
            if name in NETWORK_CALLS:
                violations.append({"path": str(path), "line": node.lineno, "issue": f"network call {name}"})
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check default eval paths for network imports and calls.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    files = python_files(args.paths)
    violations: list[dict[str, object]] = []
    for path in files:
        violations.extend(check_file(path))
    if violations:
        print("network check failed: default local eval path contains network behavior", file=sys.stderr)
        print(json.dumps({"violations": violations}, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({"checked_python_files": len(files), "violations": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
