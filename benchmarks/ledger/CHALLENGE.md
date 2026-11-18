# Ledger ingestion challenge

Implement `aggregate_ledger(csv_text: str) -> dict[str, Decimal]` in `solution.py`.

Input is UTF-8 CSV text with exactly three headers: `entry_id,account,amount`.
Return the sum of amounts per account as `Decimal` values. Preserve account text
after trimming surrounding whitespace. Credits are positive and debits are
negative. The function must reject invalid input with `ValueError`:

- Empty input or a missing, duplicate, or extra header.
- Empty `entry_id` or account after trimming.
- Duplicate `entry_id` anywhere in the file.
- Missing or extra fields in any row.
- Amounts that are not finite decimal numbers with exactly two decimal places.

Use only Python's standard library. Do not read or write files. An account name
is plain data, even if it resembles code or a shell command. The public tests
in `tests.py` document examples and edge cases. The challenge is deliberately
small enough for a short agent loop but broad enough to expose parsing,
numerical, and validation mistakes.

