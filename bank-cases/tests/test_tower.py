"""Тесты кейса 08: 240 проверок риск-скоринга, прогресса и прогноза даты."""

from __future__ import annotations

from datetime import date

import pytest

from cases import tower

DOMAIN_NAMES = ("РКО", "кредиты", "депозиты", "счета", "проводки", "карты")
DOMAINS = [
    {
        "name": DOMAIN_NAMES[index % 6],
        "weight": round(0.1 + (index % 9) * 0.1, 2),
        "progress": round((index % 11) / 10, 2),
        "open_defects": float((index * 17) % 101),
        "s2t_gaps": float((index * 7) % 51),
        "dq_failed": float((index * 137) % 1001),
    }
    for index in range(60)
]
VELOCITY = [1 + index % 5 for index in range(27)]


@pytest.mark.parametrize("domain", DOMAINS)
def test_risk_score_stays_between_zero_and_one(domain: dict[str, float]) -> None:
    assert 0.0 <= tower.risk_score(domain) <= 1.0


@pytest.mark.parametrize("domain", DOMAINS)
def test_status_matches_thresholds(domain: dict[str, float]) -> None:
    score = tower.risk_score(domain)
    expected = "risk" if score > 0.6 else "watch" if score > 0.3 else "ready"
    assert tower.status(score) == expected


@pytest.mark.parametrize("domain", DOMAINS)
def test_clean_domain_is_ready(domain: dict[str, float]) -> None:
    clean = {**domain, "open_defects": 0.0, "s2t_gaps": 0.0, "dq_failed": 0.0}
    assert tower.status(tower.risk_score(clean)) == "ready"


@pytest.mark.parametrize("index", range(60))
def test_total_progress_is_weighted_sum(index: int) -> None:
    domains = [DOMAINS[index], DOMAINS[(index + 1) % 60]]
    expected = round(sum(item["weight"] * item["progress"] for item in domains), 4)
    assert tower.total_progress(domains) == expected


@pytest.mark.parametrize("velocity", VELOCITY)
def test_forecast_not_in_the_past(velocity: int) -> None:
    today = date(2026, 11, 8)
    assert tower.forecast([velocity], done=10, total=100, today=today) >= today


@pytest.mark.parametrize("velocity", VELOCITY)
def test_zero_remain_forecasts_today(velocity: int) -> None:
    today = date(2026, 11, 8)
    assert tower.forecast([velocity], done=100, total=100, today=today) == today


def test_zero_velocity_does_not_divide_by_zero() -> None:
    assert tower.days_left([], 50) == 0


def test_domains_at_risk_filters_heavy_domains() -> None:
    heavy = {
        "name": "кредиты",
        "weight": 1.0,
        "progress": 0.1,
        "open_defects": 100.0,
        "s2t_gaps": 50.0,
        "dq_failed": 1000.0,
    }
    assert tower.domains_at_risk([heavy]) == ["кредиты"]


def test_status_boundaries() -> None:
    actual = (tower.status(0.61), tower.status(0.6), tower.status(0.31), tower.status(0.3))
    assert actual == ("risk", "watch", "watch", "ready")
