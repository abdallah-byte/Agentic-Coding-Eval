"""Run a coding challenge and inspect an agent's recorded workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "ledger-v1"
ALLOWED_EDIT = "solution.py"


def evaluate_trace(trace: dict[str, Any], tests_passed: bool) -> dict[str, Any]:
    """Score trace properties; these are explicitly self-reported workflow events."""
    if trace.get("task_id") != TASK_ID:
        raise ValueError(f"trace.task_id must be {TASK_ID}")
    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("trace.steps must be a nonempty list")
    allowed_actions = {"plan", "inspect", "edit", "test", "final"}
    for i, step in enumerate(steps, 1):
        if not isinstance(step, dict) or step.get("action") not in allowed_actions:
            raise ValueError(f"step {i} has an invalid action")
        if step["action"] in {"inspect", "edit"} and not isinstance(step.get("path"), str):
            raise ValueError(f"step {i} needs a path")
        if step["action"] == "test" and step.get("result") not in {"pass", "fail"}:
            raise ValueError(f"step {i} needs result pass or fail")
        if step["action"] == "plan" and not str(step.get("summary", "")).strip():
            raise ValueError(f"step {i} needs a plan summary")
        if step["action"] == "final" and not str(step.get("summary", "")).strip():
            raise ValueError(f"step {i} needs a summary")

    actions = [step["action"] for step in steps]
    planned_before_edit = "plan" in actions and "edit" in actions and actions.index("plan") < actions.index("edit")
    inspected_before_edit = any(
        step["action"] == "inspect" and step.get("path") == ALLOWED_EDIT
        and "edit" in actions[i + 1:]
        for i, step in enumerate(steps)
    )
    scoped_edits = "edit" in actions and all(
        step.get("path") == ALLOWED_EDIT for step in steps if step["action"] == "edit"
    )
    edit_positions = [i for i, action in enumerate(actions) if action == "edit"]
    test_positions = [i for i, action in enumerate(actions) if action == "test"]
    tested_after_last_edit = bool(edit_positions and test_positions and max(test_positions) > max(edit_positions))
    final_step = steps[-1]
    finished_after_test = bool(final_step["action"] == "final" and test_positions and max(test_positions) < len(steps) - 1)
    reported_result = steps[max(test_positions)]["result"] if test_positions else None
    consistent = reported_result == ("pass" if tests_passed else "fail")
    checks = {
        "planned_before_edit": planned_before_edit,
        "inspected_before_edit": inspected_before_edit,
        "edits_in_scope": scoped_edits,
        "tested_after_last_edit": tested_after_last_edit,
        "finished_after_test": finished_after_test,
        "last_test_matches_runner": consistent,
    }
    workflow_points = 10 * sum(checks[key] for key in (
        "planned_before_edit", "inspected_before_edit", "edits_in_scope", "tested_after_last_edit"
    ))
    if not consistent or not finished_after_test:
        workflow_points = 0
    return {"checks": checks, "workflow_points": workflow_points}


def evaluate(candidate: Path, trace_path: Path, timeout: int = 8) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parent.parent
    if not candidate.is_file():
        raise ValueError(f"candidate file does not exist: {candidate}")
    if not trace_path.is_file():
        raise ValueError(f"trace file does not exist: {trace_path}")
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    if not isinstance(trace, dict):
        raise ValueError("trace must be a JSON object")
    test_script = project_root / "benchmarks" / "ledger" / "tests.py"
    try:
        run = subprocess.run(
            [sys.executable, str(test_script), str(candidate.resolve())],
            capture_output=True, text=True, timeout=timeout, check=False,
            cwd=project_root,
        )
        passed = run.returncode == 0
        test_output = (run.stdout + run.stderr)[-12000:]
    except subprocess.TimeoutExpired:
        passed = False
        test_output = f"Test process exceeded {timeout} seconds."
    trace_result = evaluate_trace(trace, passed)
    return {
        "task_id": TASK_ID,
        "candidate": str(candidate),
        "tests_passed": passed,
        "test_output": test_output,
        "functional_points": 60 if passed else 0,
        **trace_result,
        "total_points": (60 if passed else 0) + trace_result["workflow_points"],
        "limitations": "Trace events are self-reported; only candidate behavior is independently tested. Tests execute local Python code and are not a sandbox.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate an agentic coding solution and workflow trace")
    parser.add_argument("--candidate", type=Path, required=True, help="Trusted local Python solution file")
    parser.add_argument("--trace", type=Path, required=True, help="Agent workflow trace JSON")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args(argv)
    try:
        result = evaluate(args.candidate, args.trace)
        report = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report + "\n", encoding="utf-8")
            print(f"Wrote {args.output}")
        print(report)
        return 0 if result["tests_passed"] else 1
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

