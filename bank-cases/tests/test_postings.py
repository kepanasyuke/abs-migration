"""Тесты кейса 05: 240 проверок двойной записи, разбаланса и хронологии."""

from __future__ import annotations

from typing import Any

import pytest

from cases import postings

ACCOUNTS = [f"4742{index}" for index in range(6)]
AMOUNTS = [round(100.0 + index * 13.7, 2) for index in range(60)]


def _balanced(index: int) -> list[dict[str, Any]]:
    account = ACCOUNTS[index % len(ACCOUNTS)]
    day = f"2026-{1 + index % 12:02d}-{1 + index % 27:02d}"
    return [
        {"account": account, "oper_date": day, "dt": AMOUNTS[index], "kt": 0.0},
        {"account": account, "oper_date": day, "dt": 0.0, "kt": AMOUNTS[index]},
    ]


BALANCED = [_balanced(index) for index in range(60)]
BROKEN = [
    rows + [{"account": rows[0]["account"], "oper_date": rows[0]["oper_date"], "dt": 0.0, "kt": 0.01}]
    for rows in BALANCED
]


@pytest.mark.parametrize("rows", BALANCED)
def test_equal_turnover_is_balanced(rows: list[dict[str, Any]]) -> None:
    assert postings.is_balanced(rows)


@pytest.mark.parametrize("rows", BROKEN)
def test_single_kopeck_breaks_balance(rows: list[dict[str, Any]]) -> None:
    assert not postings.is_balanced(rows)


@pytest.mark.parametrize("index", range(60))
def test_delta_reports_exact_shortage(index: int) -> None:
    assert postings.delta(BROKEN[index]) == -0.01


@pytest.mark.parametrize("index", range(55))
def test_grouping_keeps_every_posting(index: int) -> None:
    rows = BALANCED[index] + [{"account": "30102", "oper_date": "2026-01-01", "dt": 5.0, "kt": 0.0}]
    grouped = postings.group_by_account(rows)
    assert sum(len(item["rows"]) for item in grouped) == len(rows)


@pytest.mark.parametrize("index", range(60))
def test_unbalanced_reports_only_broken_accounts(index: int) -> None:
    rows = BROKEN[index] + _balanced((index + 1) % len(AMOUNTS))
    assert [item["account"] for item in postings.unbalanced(rows)] == [BROKEN[index][0]["account"]]


def test_chronology_accepts_sorted_dates() -> None:
    rows = [
        {"account": "1", "oper_date": "2026-01-10", "dt": 1.0, "kt": 0.0},
        {"account": "1", "oper_date": "2026-01-11", "dt": 1.0, "kt": 0.0},
    ]
    assert postings.chronology_ok(rows)


def test_chronology_rejects_backdated_posting() -> None:
    rows = [
        {"account": "1", "oper_date": "2026-01-11", "dt": 1.0, "kt": 0.0},
        {"account": "1", "oper_date": "2026-01-10", "dt": 1.0, "kt": 0.0},
    ]
    assert not postings.chronology_ok(rows)


def test_reason_mentions_account_and_delta() -> None:
    assert postings.reason({"account": "40817", "delta": -2.5}) == "Счёт 40817: разбаланс -2.5 руб."


def test_empty_posting_set_is_balanced() -> None:
    assert postings.is_balanced([]) and postings.unbalanced([]) == []
