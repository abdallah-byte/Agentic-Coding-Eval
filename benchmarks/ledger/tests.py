"""Public behavioral tests for ledger-v1. Run via agentbench CLI."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from decimal import Decimal
from pathlib import Path


def load_candidate(path: Path):
    spec = importlib.util.spec_from_file_location("candidate_solution", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not import candidate")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.aggregate_ledger


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.solve = staticmethod(load_candidate(Path(sys.argv[1])))

    def test_aggregation_and_negative_amounts(self):
        data = "entry_id,account,amount\n1, cash ,10.20\n2,cash,-2.05\n3,bank,0.00\n"
        self.assertEqual(self.solve(data), {"cash": Decimal("8.15"), "bank": Decimal("0.00")})

    def test_quoted_comma_is_data(self):
        data = 'entry_id,account,amount\n1,"operations, east",1.00\n'
        self.assertEqual(self.solve(data), {"operations, east": Decimal("1.00")})

    def test_decimal_precision(self):
        data = "entry_id,account,amount\n1,a,0.10\n2,a,0.20\n"
        result = self.solve(data)
        self.assertIsInstance(result["a"], Decimal)
        self.assertEqual(result["a"], Decimal("0.30"))

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            self.solve("entry_id,account,amount\n1,a,1.00\n1,b,2.00\n")

    def test_bad_header_rejected(self):
        for data in ("", "id,account,amount\n1,a,1.00\n", "entry_id,account,amount,extra\n1,a,1.00,z\n"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.solve(data)

    def test_invalid_amounts_rejected(self):
        for amount in ("NaN", "Infinity", "1", "1.2", "not-a-number"):
            with self.subTest(amount=amount), self.assertRaises(ValueError):
                self.solve(f"entry_id,account,amount\n1,a,{amount}\n")

    def test_missing_or_extra_fields_rejected(self):
        for row in ("1,a", "1,a,1.00,unexpected", ",a,1.00", "1,,1.00"):
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.solve(f"entry_id,account,amount\n{row}\n")

    def test_account_text_is_data(self):
        data = 'entry_id,account,amount\n1,"$(touch hacked)",1.00\n'
        self.assertEqual(self.solve(data), {"$(touch hacked)": Decimal("1.00")})


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)

