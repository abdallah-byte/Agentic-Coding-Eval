"""Reference candidate for the public ledger-v1 benchmark."""

import csv
import io
import re
from decimal import Decimal, InvalidOperation

AMOUNT = re.compile(r"^[+-]?\d+\.\d{2}$")


def aggregate_ledger(csv_text: str) -> dict[str, Decimal]:
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("CSV text is empty")
    reader = csv.reader(io.StringIO(csv_text, newline=""), strict=True)
    try:
        header = next(reader)
        if header != ["entry_id", "account", "amount"]:
            raise ValueError("Expected entry_id,account,amount header")
        totals: dict[str, Decimal] = {}
        ids: set[str] = set()
        for row in reader:
            if len(row) != 3:
                raise ValueError("Each row needs exactly three fields")
            entry_id, account, amount_text = (part.strip() for part in row)
            if not entry_id or not account:
                raise ValueError("entry_id and account are required")
            if entry_id in ids:
                raise ValueError(f"Duplicate entry_id: {entry_id}")
            ids.add(entry_id)
            if not AMOUNT.fullmatch(amount_text):
                raise ValueError(f"Invalid amount: {amount_text}")
            try:
                amount = Decimal(amount_text)
            except InvalidOperation as exc:
                raise ValueError(f"Invalid amount: {amount_text}") from exc
            if not amount.is_finite():
                raise ValueError("Amount must be finite")
            totals[account] = totals.get(account, Decimal("0.00")) + amount
        return totals
    except csv.Error as exc:
        raise ValueError("Malformed CSV") from exc

