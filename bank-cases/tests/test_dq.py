"""Тесты кейса 02: 240 проверок валидаторов и сводок качества данных."""

from __future__ import annotations

import pytest

from cases import dq

REGIONS = ("77", "50", "23", "66", "78", "02")
BASES = [f"{region}{index:07d}" for region in REGIONS for index in range(1, 11)]
VALID = [dq.inn_build(base) for base in BASES]
BROKEN = [inn[:-1] + str((int(inn[-1]) + 1) % 10) for inn in VALID]
BIKS = [(f"04{700 + index}0000", True) for index in range(30)]
BIKS += [(f"03{700 + index}0000", False) for index in range(30)]
FILTERS = (0, 1, 5, 10, 20, 50, 100)
COUNTS = [
    (failed, total)
    for total in (20, 100, 1000, 10000)
    for failed in (0, 1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 999, 1000, 1500, 2000)
]


@pytest.mark.parametrize("inn", VALID)
def test_generated_inn_is_valid(inn: str) -> None:
    assert dq.inn_valid(inn)


@pytest.mark.parametrize("inn", BROKEN)
def test_broken_inn_checksum_rejected(inn: str) -> None:
    assert not dq.inn_valid(inn)


@pytest.mark.parametrize(("bik", "expected"), BIKS)
def test_bik_prefix_controls_validity(bik: str, expected: bool) -> None:
    assert dq.bik_valid(bik) is expected


@pytest.mark.parametrize(("failed", "total"), COUNTS)
def test_severity_follows_share_of_failures(failed: int, total: int) -> None:
    expected = "critical" if failed / total > 0.05 else "warning" if failed else "ok"
    assert dq.severity(failed, total) == expected


def test_known_valid_inn_accepted() -> None:
    assert dq.inn_valid("7707083893")


def test_twelve_digit_inn_accepted() -> None:
    assert dq.inn_valid("500100732259")


def test_short_inn_rejected() -> None:
    assert not dq.inn_valid("77070838")


def test_non_digit_inn_rejected() -> None:
    assert not dq.inn_valid("770708389X")


def test_account_requires_twenty_digits() -> None:
    assert dq.account_valid("40817810099910004312") and not dq.account_valid("4081781009991000431")


def test_percent_formatting() -> None:
    assert dq.to_percent(0.1234) == "12.3%"


def test_summary_counts_failures() -> None:
    rows = [{"failed": 3}, {"failed": 5}]
    assert dq.summarize(rows)["failed"] == 8


def test_zero_total_does_not_divide_by_zero() -> None:
    assert dq.severity(0, 0) == "ok"


def test_filters_cover_zero_row_case() -> None:
    assert all(dq.severity(0, total) == "ok" for total in FILTERS)
