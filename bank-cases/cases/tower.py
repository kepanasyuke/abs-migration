"""Кейс 08. Control Tower: риск домена, прогресс и прогноз даты готовности."""

from __future__ import annotations

from datetime import date, timedelta


def risk_score(domain: dict[str, float]) -> float:
    parts = (
        0.4 * domain["open_defects"] / 100,
        0.35 * domain["s2t_gaps"] / 50,
        0.25 * domain["dq_failed"] / 1000,
    )
    return round(sum(parts), 3)


def status(score: float) -> str:
    return "risk" if score > 0.6 else "watch" if score > 0.3 else "ready"


def total_progress(domains: list[dict[str, float]]) -> float:
    return round(sum(domain["weight"] * domain["progress"] for domain in domains), 4)


def days_left(velocity: list[int], remain: int) -> int:
    average = sum(velocity) / max(len(velocity), 1)
    return round(remain / average * 7) if average else 0


def forecast(velocity: list[int], done: int, total: int, today: date | None = None) -> date:
    return (today or date.today()) + timedelta(days=days_left(velocity, total - done))


def domains_at_risk(domains: list[dict[str, float]]) -> list[str]:
    return [str(domain["name"]) for domain in domains if status(risk_score(domain)) == "risk"]
