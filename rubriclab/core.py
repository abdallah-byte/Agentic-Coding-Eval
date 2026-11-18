"""Input validation and descriptive analysis for human response ratings."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DIMENSIONS = ("accuracy", "instruction_following", "clarity", "safety")
WEIGHTS = {"accuracy": 0.4, "instruction_following": 0.3, "clarity": 0.2, "safety": 0.1}
CHOICES = ("A", "B", "tie")


class DataError(ValueError):
    """Raised when a JSONL dataset breaks the published evaluation schema."""


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        raise DataError(f"File does not exist: {path}")
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DataError(f"{path}:{line_no}: invalid JSON: {exc.msg}") from exc
        if not isinstance(row, dict):
            raise DataError(f"{path}:{line_no}: each row must be an object")
        rows.append(row)
    if not rows:
        raise DataError(f"{path}: no records found")
    return rows


def _string(value: Any, field: str, minimum: int = 1) -> str:
    if not isinstance(value, str) or len(value.strip()) < minimum:
        raise DataError(f"{field} must be a string with at least {minimum} nonblank characters")
    return value


def validate(tasks: list[dict[str, Any]], annotations: list[dict[str, Any]]) -> list[str]:
    """Check structural correctness and return nonfatal review warnings."""
    task_by_id: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks, 1):
        prefix = f"task row {index}"
        task_id = _string(task.get("id"), f"{prefix}.id")
        if task_id in task_by_id:
            raise DataError(f"Duplicate task id: {task_id}")
        _string(task.get("category"), f"{prefix}.category")
        _string(task.get("prompt"), f"{prefix}.prompt")
        _string(task.get("reference_notes"), f"{prefix}.reference_notes")
        responses = task.get("responses")
        if not isinstance(responses, dict) or set(responses) != {"A", "B"}:
            raise DataError(f"{prefix}.responses must contain exactly A and B")
        for label in ("A", "B"):
            _string(responses[label], f"{prefix}.responses.{label}")
        task_by_id[task_id] = task

    seen: set[tuple[str, str]] = set()
    warnings: list[str] = []
    for index, annotation in enumerate(annotations, 1):
        prefix = f"annotation row {index}"
        task_id = _string(annotation.get("task_id"), f"{prefix}.task_id")
        annotator = _string(annotation.get("annotator"), f"{prefix}.annotator")
        if task_id not in task_by_id:
            raise DataError(f"{prefix}: unknown task id {task_id}")
        key = (task_id, annotator)
        if key in seen:
            raise DataError(f"Duplicate annotation for task {task_id} by {annotator}")
        seen.add(key)
        ratings = annotation.get("ratings")
        if not isinstance(ratings, dict) or set(ratings) != {"A", "B"}:
            raise DataError(f"{prefix}.ratings must contain exactly A and B")
        for label in ("A", "B"):
            rating = ratings[label]
            if not isinstance(rating, dict):
                raise DataError(f"{prefix}.ratings.{label} must be an object")
            for dimension in DIMENSIONS:
                score = rating.get(dimension)
                if type(score) is not int or not 0 <= score <= 4:
                    raise DataError(f"{prefix}.ratings.{label}.{dimension} must be an integer from 0 to 4")
            _string(rating.get("rationale"), f"{prefix}.ratings.{label}.rationale", 12)
            evidence = _string(rating.get("evidence"), f"{prefix}.ratings.{label}.evidence")
            if evidence not in task_by_id[task_id]["responses"][label]:
                raise DataError(f"{prefix}.ratings.{label}.evidence must quote that response exactly")
        choice = annotation.get("preference")
        if choice not in CHOICES:
            raise DataError(f"{prefix}.preference must be A, B, or tie")
        _string(annotation.get("preference_reason"), f"{prefix}.preference_reason", 12)
        a_score = weighted_score(ratings["A"])
        b_score = weighted_score(ratings["B"])
        if choice == "A" and b_score - a_score >= 1:
            warnings.append(f"{task_id}/{annotator}: preference A differs from rubric scores; review rationale")
        elif choice == "B" and a_score - b_score >= 1:
            warnings.append(f"{task_id}/{annotator}: preference B differs from rubric scores; review rationale")
    return warnings


def weighted_score(rating: dict[str, Any]) -> float:
    return sum(rating[dimension] * WEIGHTS[dimension] for dimension in DIMENSIONS)


def cohen_kappa(pairs: list[tuple[str, str]]) -> float | None:
    """Unweighted nominal Cohen's kappa; None means it cannot be estimated."""
    if not pairs:
        return None
    n = len(pairs)
    first = Counter(a for a, _ in pairs)
    second = Counter(b for _, b in pairs)
    observed = sum(a == b for a, b in pairs) / n
    expected = sum(first[choice] * second[choice] for choice in CHOICES) / (n * n)
    if expected == 1:
        return 1.0 if observed == 1 else None
    return (observed - expected) / (1 - expected)


def analyze(tasks: list[dict[str, Any]], annotations: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce descriptive statistics without claiming model performance."""
    warnings = validate(tasks, annotations)
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for annotation in annotations:
        by_task[annotation["task_id"]].append(annotation)

    pairs: list[tuple[str, str]] = []
    disagreements: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    for task in tasks:
        task_id = task["id"]
        entries = sorted(by_task[task_id], key=lambda row: row["annotator"])
        counts = Counter(entry["preference"] for entry in entries)
        if len(entries) == 2:
            pairs.append((entries[0]["preference"], entries[1]["preference"]))
            if entries[0]["preference"] != entries[1]["preference"]:
                disagreements.append({"task_id": task_id, "votes": dict(counts)})
        elif len(entries) > 2:
            warnings.append(f"{task_id}: more than two annotators; excluded from pairwise kappa")
        elif len(entries) == 0:
            warnings.append(f"{task_id}: no annotations")
        task_rows.append({
            "id": task_id,
            "category": task["category"],
            "prompt": task["prompt"],
            "reference_notes": task["reference_notes"],
            "responses": task["responses"],
            "votes": dict(counts),
            "annotations": entries,
        })

    score_sums = {label: 0.0 for label in ("A", "B")}
    for entry in annotations:
        for label in ("A", "B"):
            score_sums[label] += weighted_score(entry["ratings"][label])
    total = len(annotations)
    return {
        "task_count": len(tasks),
        "annotation_count": total,
        "annotator_count": len({entry["annotator"] for entry in annotations}),
        "preference_counts": dict(Counter(entry["preference"] for entry in annotations)),
        "mean_scores": {label: round(score_sums[label] / total, 2) for label in ("A", "B")},
        "paired_task_count": len(pairs),
        "agreement_rate": round(sum(a == b for a, b in pairs) / len(pairs), 3) if pairs else None,
        "cohen_kappa": round(cohen_kappa(pairs), 3) if pairs else None,
        "disagreements": disagreements,
        "warnings": warnings,
        "tasks": task_rows,
    }
