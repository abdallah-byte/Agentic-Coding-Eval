# Agentic Coding Eval

A small, reproducible portfolio project for evaluating coding agents. It pairs
a real programming challenge with executable tests, a structured record of the
  agent's plan/inspect/edit/test/finish workflow, and a separate human rating module.
Everything runs locally with Python's standard library; no API key is needed.

This is an independent portfolio project. It is **not** an Alignerr assessment,
product, or affiliated repository. The design targets skills described in
[Alignerr's Senior Software Engineer — Agentic Coding listing](https://www.alignerr.com/jobs/fedb7ac3-0a7a-458a-90fa-bbe058a2c7e6): building coding challenges, testing generated code, reviewing tool use, and identifying failure modes.

## What a reviewer can see

- **A concrete task:** [`ledger-v1`](benchmarks/ledger/CHALLENGE.md) asks an agent
  to turn a fragile CSV aggregator into a reliable implementation.
- **Behavioral verification:** Eight public tests cover decimal precision,
  quoted fields, duplicate IDs, malformed records, and treating input as data.
- **Workflow review:** A JSON trace records plans, inspections, edits, tests, and the
  final summary. The scorer checks ordering, edit scope, and consistency with
  independently run tests.
- **Failure comparison:** The intentionally broken starter scores poorly; the
  fixed reference candidate passes. This makes the report easy to inspect.
- **Human evaluation:** `rubriclab` validates evidence-backed paired ratings
  and renders a self-contained HTML review report.

## Quick start

Requires Python 3.10 or newer. From the repository root:

```bash
python -m unittest discover -s tests -v
python -m agentbench --candidate examples/candidates/fixed.py --trace examples/traces/fixed.json --output reports/agentic.json
python -m rubriclab validate
python -m rubriclab report --output reports/human-review.html
```

Open `reports/human-review.html` in a browser. `reports/` is ignored by Git so
you can regenerate reports without changing the source tree.

For a baseline failure, run:

```bash
python -m agentbench --candidate benchmarks/ledger/starter.py --trace examples/traces/starter.json
```

That command exits with code 1 because the candidate fails tests. This is an
expected benchmark result.

Optional local install:

```bash
python -m pip install -e .
agentbench --candidate examples/candidates/fixed.py --trace examples/traces/fixed.json
```

## Try your own coding agent

1. Give the agent [`CHALLENGE.md`](benchmarks/ledger/CHALLENGE.md) and
   [`starter.py`](benchmarks/ledger/starter.py). Ask it to produce `solution.py`.
2. Record its actions in a JSON file following
   [`fixed.json`](examples/traces/fixed.json). Each step has `action`;
   a `plan` step needs `summary`,
   `inspect`/`edit` steps need `path`, a `test` step needs `result`, and the
   last `final` step needs `summary`.
3. Run `python -m agentbench --candidate path/to/solution.py --trace path/to/trace.json`.
4. Review the JSON score and test output. The maximum is 100: 60 for behavior,
   40 for recorded workflow. A claimed final test result that conflicts with
   the independently run tests receives no workflow credit.

The trace is a **self-reported artifact**. The harness verifies candidate
behavior, but it cannot prove that every recorded agent action occurred.
Candidate Python files are executed in a subprocess, **not a security sandbox**;
run only code you trust in your local environment. The public task can also be
overfit, so a serious benchmark should add private tasks and fresh test cases.

## Human review module

`examples/tasks.jsonl` and `examples/annotations.jsonl` contain synthetic
paired-answer examples. The four dimensions are accuracy (40%), instruction
following (30%), clarity (20%), and safety (10%), each scored from 0 to 4.
Every rating requires a rationale and an exact quote from the rated answer.
The report shows preferences, disagreements, mean scores, raw agreement, and
Cohen's kappa for tasks with exactly two reviewers. Those statistics describe
the **example annotations**, not real model performance.

To use your own data:

```bash
python -m rubriclab report --tasks my-tasks.jsonl --annotations my-ratings.jsonl --output reports/my-review.html
```

## Repository layout

```text
agentbench/             Coding challenge runner and trace scorer
benchmarks/ledger/      Challenge specification, starter, public tests
examples/candidates/    Passing reference implementation
examples/traces/        Demonstration workflow traces
rubriclab/              Human rating validation and HTML report
examples/*.jsonl        Synthetic paired response ratings
tests/                  Project verification
.github/workflows/       CI on Python 3.10 and 3.12
```

## Design choices and limits

The benchmark uses standard-library tools and subprocesses so a reviewer can
run it without accounts or services. It reports observed tests and trace checks
separately, avoiding a single opaque judgment. The challenge tests are public
and cover one Python task; this is a portfolio demonstration, not a statistically
representative coding-agent leaderboard. The HTML report escapes task and
annotation text before rendering.

## License

MIT. All included tasks, responses, traces, and ratings are synthetic.

## Publish on GitHub

Create an empty repository named `agentic-coding-eval` on GitHub. Then run
these commands **inside this project folder** (replace `YOUR_USERNAME`):

```bash
git init -b main
git add .
git commit -m "Initial release"
git remote add origin https://github.com/YOUR_USERNAME/agentic-coding-eval.git
git push -u origin main
```

The `.gitignore` excludes local reports and Python cache files. Add your name,
GitHub profile, and any real evaluation examples you are allowed to share
before using the repository in an application.
