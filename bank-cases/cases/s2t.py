"""Кейс 01. Source-to-Target Mapping: профиль колонок и ранжирование кандидатов."""

from __future__ import annotations

from collections.abc import Iterable
from operator import itemgetter

from cases.common import cosine


def similarity(source: str, target: str) -> float:
    return cosine(source, target)


def candidate(source: str, target: str) -> dict[str, object]:
    return {"source": source, "target": target, "score": similarity(source, target)}


def rank(source: str, targets: Iterable[str], limit: int = 5) -> list[dict[str, object]]:
    return sorted((candidate(source, name) for name in targets), key=itemgetter("score"), reverse=True)[:limit]


def match_level(score: float) -> str:
    return "auto" if score >= 0.9 else "review" if score >= 0.7 else "manual"


def profile_sql(table: str, column: str) -> str:
    return (
        f"select count(*) total, count(distinct {column}) uniq, "
        f"count(*) filter (where {column} is null) nulls from legacy.{table}"
    )


def profile(row: dict[str, int]) -> dict[str, float]:
    fill = 1 - int(row["nulls"]) / max(int(row["total"]), 1)
    return {**row, "fill_rate": round(fill, 4)}
