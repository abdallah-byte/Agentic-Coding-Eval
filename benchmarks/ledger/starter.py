"""Intentionally incomplete candidate for the ledger-v1 challenge."""


def aggregate_ledger(csv_text):
    totals = {}
    for line in csv_text.splitlines()[1:]:
        entry_id, account, amount = line.split(",")
        totals[account] = totals.get(account, 0) + float(amount)
    return totals

