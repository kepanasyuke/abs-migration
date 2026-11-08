"""Кейс 05. Проводки: двойная запись, разбаланс и хронология."""

from __future__ import annotations

from itertools import groupby
from operator import itemgetter
from typing import Any


def delta(rows: list[dict[str, Any]]) -> float:
    return round(sum(row["dt"] - row["kt"] for row in rows), 2)


def is_balanced(rows: list[dict[str, Any]]) -> bool:
    return delta(rows) == 0


def group_by_account(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = itemgetter("account")
    ordered = sorted(rows, key=key)
    return [{"account": name, "rows": list(group)} for name, group in groupby(ordered, key=key)]


def unbalanced(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    broken = [item for item in group_by_account(rows) if not is_balanced(item["rows"])]
    return [{"account": item["account"], "delta": delta(item["rows"])} for item in broken]


def chronology_ok(rows: list[dict[str, Any]]) -> bool:
    dates = [row["oper_date"] for row in rows]
    return dates == sorted(dates)


def reason(item: dict[str, Any]) -> str:
    return f"Счёт {item['account']}: разбаланс {item['delta']} руб."
