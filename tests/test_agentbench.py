from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentbench.cli import evaluate, evaluate_trace


ROOT = Path(__file__).resolve().parent.parent


class AgentBenchTests(unittest.TestCase):
    def test_reference_candidate_passes(self):
        result = evaluate(ROOT / "examples/candidates/fixed.py", ROOT / "examples/traces/fixed.json")
        self.assertTrue(result["tests_passed"], result["test_output"])
        self.assertEqual(result["total_points"], 100)

    def test_starter_exposes_failures(self):
        result = evaluate(ROOT / "benchmarks/ledger/starter.py", ROOT / "examples/traces/starter.json")
        self.assertFalse(result["tests_passed"])
        self.assertEqual(result["functional_points"], 0)

    def test_inconsistent_trace_gets_no_workflow_credit(self):
        result = evaluate(ROOT / "benchmarks/ledger/starter.py", ROOT / "examples/traces/fixed.json")
        self.assertFalse(result["checks"]["last_test_matches_runner"])
        self.assertEqual(result["workflow_points"], 0)

    def test_out_of_scope_edit_loses_credit(self):
        trace = {
            "task_id": "ledger-v1",
            "steps": [
                {"action": "plan", "summary": "Inspect, edit, test."},
                {"action": "inspect", "path": "solution.py"},
                {"action": "edit", "path": "other.py"},
                {"action": "test", "result": "pass"},
                {"action": "final", "summary": "Done"},
            ],
        }
        result = evaluate_trace(trace, True)
        self.assertFalse(result["checks"]["edits_in_scope"])
        self.assertEqual(result["workflow_points"], 30)

    def test_missing_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                evaluate(Path(temp) / "missing.py", ROOT / "examples/traces/fixed.json")


if __name__ == "__main__":
    unittest.main()

