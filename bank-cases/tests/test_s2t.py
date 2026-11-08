"""Тесты кейса 01: 240 проверок по 60 сочетаниям полей."""

from __future__ import annotations

import pytest

from cases import s2t

PREFIXES = ("client", "account", "payment", "credit", "deposit", "balance")
SUFFIXES = ("id", "name", "date", "amount", "currency", "status", "code", "type", "owner", "branch")
PAIRS = [(prefix, suffix) for prefix in PREFIXES for suffix in SUFFIXES]
SCORES = tuple(round(index / 59, 4) for index in range(60))
LEVELS = {"manual": 0, "review": 1, "auto": 2}


@pytest.mark.parametrize(("prefix", "suffix"), PAIRS)
def test_similarity_stays_in_unit_range(prefix: str, suffix: str) -> None:
    assert 0.0 <= s2t.similarity(f"{prefix}_{suffix}", f"cft_{suffix}") <= 1.0


@pytest.mark.parametrize(("prefix", "suffix"), PAIRS)
def test_similarity_is_symmetric(prefix: str, suffix: str) -> None:
    assert s2t.similarity(f"{prefix}_{suffix}", suffix) == s2t.similarity(suffix, f"{prefix}_{suffix}")


@pytest.mark.parametrize(("prefix", "suffix"), PAIRS)
def test_rank_returns_sorted_slice(prefix: str, suffix: str) -> None:
    ranked = s2t.rank(f"{prefix}_{suffix}", SUFFIXES, limit=3)
    assert len(ranked) <= 3 and ranked == sorted(ranked, key=lambda item: item["score"], reverse=True)


@pytest.mark.parametrize("score", SCORES)
def test_match_level_grows_with_score(score: float) -> None:
    lower = s2t.match_level(max(score - 0.1, 0.0))
    assert LEVELS[s2t.match_level(score)] >= LEVELS[lower]


def test_match_level_boundaries() -> None:
    assert (s2t.match_level(0.95), s2t.match_level(0.7), s2t.match_level(0.69)) == ("auto", "review", "manual")


def test_profile_counts_fill_rate() -> None:
    assert s2t.profile({"total": 1000, "uniq": 900, "nulls": 250})["fill_rate"] == 0.75


def test_profile_survives_empty_table() -> None:
    assert s2t.profile({"total": 0, "uniq": 0, "nulls": 0})["fill_rate"] == 1.0


def test_profile_sql_names_source_table() -> None:
    assert "legacy.programbank_payment" in s2t.profile_sql("programbank_payment", "summa")
