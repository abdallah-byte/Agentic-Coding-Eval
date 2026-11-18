from __future__ import annotations

import unittest
from copy import deepcopy
from pathlib import Path

from rubriclab.core import DataError, analyze, read_jsonl, validate
from rubriclab.report import render_html


ROOT = Path(__file__).resolve().parent.parent


class RubricLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = read_jsonl(ROOT / "examples/tasks.jsonl")
        cls.annotations = read_jsonl(ROOT / "examples/annotations.jsonl")

    def test_sample_dataset_and_agreement(self):
        result = analyze(self.tasks, self.annotations)
        self.assertEqual(result["task_count"], 5)
        self.assertEqual(result["annotation_count"], 10)
        self.assertEqual(result["paired_task_count"], 5)
        self.assertEqual(len(result["disagreements"]), 1)
        self.assertAlmostEqual(result["agreement_rate"], 0.8)

    def test_evidence_must_quote_response(self):
        altered = deepcopy(self.annotations)
        altered[0]["ratings"]["A"]["evidence"] = "a fabricated quote"
        with self.assertRaises(DataError):
            validate(self.tasks, altered)

    def test_report_escapes_user_content(self):
        altered = deepcopy(self.tasks)
        altered[0]["prompt"] = "<script>alert(1)</script>"
        summary = analyze(altered, self.annotations)
        html = render_html(summary)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)


if __name__ == "__main__":
    unittest.main()

