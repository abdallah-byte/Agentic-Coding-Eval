"""Self-contained HTML report with no network or JavaScript dependencies."""

from __future__ import annotations

from html import escape
from typing import Any

from .core import DIMENSIONS, weighted_score


def _h(value: Any) -> str:
    return escape(str(value), quote=True)


def _metric(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def render_html(summary: dict[str, Any]) -> str:
    rows: list[str] = []
    for task in summary["tasks"]:
        response_cards = []
        for label in ("A", "B"):
            response_cards.append(
                f'<div class="response"><div class="eyebrow">Response {label}</div>'
                f'<pre>{_h(task["responses"][label])}</pre></div>'
            )
        annotation_cards = []
        for entry in task["annotations"]:
            rating_lines = []
            for label in ("A", "B"):
                rating = entry["ratings"][label]
                scores = " · ".join(f"{name.replace('_', ' ').title()} {rating[name]}/4" for name in DIMENSIONS)
                rating_lines.append(
                    f'<div class="rating"><strong>{label}: {weighted_score(rating):.1f}/4 weighted</strong>'
                    f'<span class="scoreline">{_h(scores)}</span>'
                    f'<p>{_h(rating["rationale"])}</p>'
                    f'<p class="evidence">Evidence: “{_h(rating["evidence"])}”</p></div>'
                )
            annotation_cards.append(
                f'<div class="annotation"><div class="annotation-head"><strong>{_h(entry["annotator"])}</strong>'
                f'<span class="pill">Prefers {_h(entry["preference"])}</span></div>'
                f'{"".join(rating_lines)}<p class="reason"><strong>Why:</strong> '
                f'{_h(entry["preference_reason"])}</p></div>'
            )
        votes = ", ".join(f"{label}: {task['votes'].get(label, 0)}" for label in ("A", "B", "tie"))
        rows.append(
            f'<section class="task"><div class="task-head"><span class="eyebrow">{_h(task["id"])} · '
            f'{_h(task["category"])}</span><span class="vote">{_h(votes)}</span></div>'
            f'<h2>{_h(task["prompt"])}</h2>'
            f'<p class="reference"><strong>Reference notes:</strong> {_h(task["reference_notes"])}</p>'
            f'<div class="response-grid">{"".join(response_cards)}</div>'
            f'<div class="annotation-grid">{"".join(annotation_cards)}</div></section>'
        )
    warnings = "".join(f"<li>{_h(item)}</li>" for item in summary["warnings"])
    disagreements = "".join(f"<li>{_h(row['task_id'])}: {_h(row['votes'])}</li>" for row in summary["disagreements"])
    preferences = summary["preference_counts"]
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RubricLab | Evaluation report</title>
<style>
:root {{ color-scheme: light; --ink:#172329; --muted:#627479; --border:#d9e3e2; --bg:#f3f7f5; --accent:#006d61; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif; }}
.wrap {{ max-width:1100px; padding:40px 24px 80px; margin:auto; }}
h1 {{ font-size:clamp(2rem,4vw,3.25rem); line-height:1.1; margin:.2em 0; letter-spacing:-.04em; }}
h2 {{ font-size:1.25rem; line-height:1.35; margin:10px 0; }}
p {{ margin:.6em 0; }}
.intro {{ color:var(--muted); max-width:750px; }}
.eyebrow {{ color:var(--accent); font-weight:750; font-size:.76rem; text-transform:uppercase; letter-spacing:.09em; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin:30px 0; }}
.card,.task,.note {{ background:white; border:1px solid var(--border); border-radius:16px; }}
.card {{ padding:18px; }} .card strong {{ display:block; font-size:1.8rem; letter-spacing:-.04em; }}
.card span {{ color:var(--muted); font-size:.84rem; }}
.note {{ padding:20px 24px; margin:18px 0 30px; }} .note h2 {{ margin-top:0; }}
.note ul {{ padding-left:22px; margin-bottom:0; }}
.task {{ padding:24px; margin:22px 0; box-shadow:0 3px 18px #153d3110; }}
.task-head,.annotation-head {{ display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
.vote,.pill {{ background:#eaf4f1; color:#075e55; border-radius:999px; padding:4px 10px; font-size:.82rem; font-weight:650; }}
.reference {{ color:var(--muted); }}
.response-grid,.annotation-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); gap:14px; margin-top:18px; }}
.response,.annotation {{ border:1px solid var(--border); border-radius:12px; padding:16px; min-width:0; }}
pre {{ white-space:pre-wrap; overflow-wrap:anywhere; font:inherit; margin:10px 0 0; }}
.annotation {{ background:#fbfdfc; }} .rating {{ border-top:1px solid var(--border); margin-top:14px; padding-top:14px; }}
.rating strong,.scoreline {{ display:block; }} .scoreline,.evidence {{ color:var(--muted); font-size:.88rem; }}
.reason {{ border-top:1px solid var(--border); padding-top:12px; }}
footer {{ color:var(--muted); font-size:.85rem; margin-top:30px; }}
</style>
</head>
<body><main class="wrap">
<div class="eyebrow">Human evaluation portfolio · synthetic examples</div>
<h1>AI response evaluation report</h1>
<p class="intro">A transparent review of paired responses using a 0–4 rubric, exact evidence quotes, written rationales, and independent preference votes. These are demonstration ratings, not claims about a live model.</p>
<div class="cards">
<div class="card"><strong>{summary['task_count']}</strong><span>tasks</span></div>
<div class="card"><strong>{summary['annotation_count']}</strong><span>annotations</span></div>
<div class="card"><strong>{summary['annotator_count']}</strong><span>annotators</span></div>
<div class="card"><strong>{_metric(summary['agreement_rate'])}</strong><span>pairwise preference agreement</span></div>
<div class="card"><strong>{_metric(summary['cohen_kappa'])}</strong><span>Cohen's kappa</span></div>
</div>
<div class="note"><h2>At a glance</h2>
<p>Preferences: A {preferences.get('A', 0)} · B {preferences.get('B', 0)} · tie {preferences.get('tie', 0)}. Mean weighted score: A {summary['mean_scores']['A']:.2f}/4 · B {summary['mean_scores']['B']:.2f}/4.</p>
<p><strong>Method:</strong> accuracy 40%, instruction following 30%, clarity 20%, safety 10%. Preference is independently recorded; score conflicts are flagged for review. Kappa uses only tasks with exactly two annotations.</p>
<p><strong>Disagreements:</strong> {len(summary['disagreements'])} of {summary['paired_task_count']} paired tasks.</p>
{f'<ul>{disagreements}</ul>' if disagreements else ''}
{f'<p><strong>Review warnings:</strong></p><ul>{warnings}</ul>' if warnings else ''}
</div>
{''.join(rows)}
<footer>RubricLab · Synthetic, locally stored examples. No external API calls or uploaded data.</footer>
</main></body></html>'''
