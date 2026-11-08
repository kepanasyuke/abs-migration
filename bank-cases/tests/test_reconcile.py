"""Тесты кейса 03: 240 проверок сверки остатков и классификации расхождений."""

from __future__ import annotations

import pytest

from cases import reconcile

ACCOUNTS = [f"40817{index:08d}" for index in range(20)]
CURRENCIES = ("RUB", "USD", "EUR")
COMBOS = [(account, currency) for account in ACCOUNTS for currency in CURRENCIES]
AMOUNTS = [round(1000.5 + index * 137.25, 2) for index in range(60)]


def _book(balance: float) -> list[dict[str, object]]:
    return [{"account": account, "currency": currency, "balance": balance} for account, currency in COMBOS]


def _pair(index: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    return _book(AMOUNTS[index % 60]), _book(AMOUNTS[(index + 7) % 60])


@pytest.mark.parametrize("index", range(60))
def test_diff_of_equal_balances_is_zero(index: int) -> None:
    assert reconcile.diff(AMOUNTS[index], AMOUNTS[index]) == 0.0


@pytest.mark.parametrize("index", range(30))
def test_diff_keeps_sign_of_shortage(index: int) -> None:
    assert reconcile.diff(AMOUNTS[index], AMOUNTS[index] - 5.5) == -5.5


@pytest.mark.parametrize(("account", "currency"), COMBOS)
@pytest.mark.parametrize("offset", (0, 1))
def test_reconcile_maps_every_target_account(account: str, currency: str, offset: int) -> None:
    legacy, target = _pair(offset)
    rows = reconcile.reconcile(legacy, target)
    found = [row for row in rows if (row["account"], row["currency"]) == (account, currency)]
    assert [row["delta"] for row in found] == [reconcile.diff(AMOUNTS[offset % 60], AMOUNTS[(offset + 7) % 60])]


@pytest.mark.parametrize(("account", "currency"), COMBOS)
def test_classify_priority_order(account: str, currency: str) -> None:
    duplicate = {"account": account, "currency": currency, "delta": 0.0, "duplicate": True, "manual": True}
    assert reconcile.classify(duplicate) == "duplicate"


def test_classify_manual_beats_rounding() -> None:
    assert reconcile.classify({"delta": 0.0, "manual": True}) == "manual"


def test_classify_small_delta_is_rounding() -> None:
    assert reconcile.classify({"delta": 0.004}) == "rounding"


def test_classify_foreign_currency_is_rate() -> None:
    assert reconcile.classify({"currency": "USD", "delta": 12.5}) == "rate"


def test_classify_default_is_missing_posting() -> None:
    assert reconcile.classify({"currency": "RUB", "delta": 12.5}) == "missing_posting"


def test_grouped_counts_every_cause() -> None:
    cells = reconcile.explain([{"delta": 0.0, "manual": True}, {"delta": 0.0}, {"delta": 9.0, "currency": "USD"}])
    assert reconcile.grouped(cells) == {"manual": 1, "rate": 1, "rounding": 1}


def test_absent_account_treated_as_zero() -> None:
    rows = reconcile.reconcile([], [{"account": "40817", "currency": "RUB", "balance": 15.0}])
    assert rows[0]["delta"] == 15.0


def test_is_explained_requires_cause() -> None:
    assert reconcile.is_explained({"cause": "rate"}) and not reconcile.is_explained({})
