"""Command-line interface for dataset validation and report generation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import DataError, analyze, read_jsonl, validate
from .report import render_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate paired AI responses with a human rubric")
    parser.add_argument("command", choices=("validate", "report"))
    parser.add_argument("--tasks", type=Path, default=Path("examples/tasks.jsonl"))
    parser.add_argument("--annotations", type=Path, default=Path("examples/annotations.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation.html"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary for report command")
    args = parser.parse_args(argv)
    try:
        tasks = read_jsonl(args.tasks)
        annotations = read_jsonl(args.annotations)
        warnings = validate(tasks, annotations)
        if args.command == "validate":
            print(f"Valid: {len(tasks)} tasks, {len(annotations)} annotations")
            for warning in warnings:
                print(f"Review: {warning}")
            return 0
        summary = analyze(tasks, annotations)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render_html(summary), encoding="utf-8")
        if args.json:
            compact = {key: value for key, value in summary.items() if key != "tasks"}
            print(json.dumps(compact, ensure_ascii=False, indent=2))
        else:
            print(f"Wrote {args.output}")
        return 0
    except (DataError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

