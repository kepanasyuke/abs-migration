"""Сопоставление полей legacy → ЦФТ по совпадению токенов с учётом синонимов."""

from __future__ import annotations

SYNONYMS = {
    "summa": "amount",
    "data": "date",
    "nschet": "account",
    "schet": "account",
    "val": "currency",
    "valuta": "currency",
    "naim": "name",
    "kod": "code",
    "kredit": "credit",
    "dep": "deposit",
    "ostatok": "balance",
    "ost": "balance",
    "proc": "rate",
    "stavka": "rate",
    "zakr": "close",
    "nomer": "number",
    "doc": "doc",
    "oper": "oper",
}

AUTO = 0.9
REVIEW = 0.6


def tokens(value: str) -> list[str]:
    parts = value.lower().replace("ё", "е").replace(".", "_").split("_")
    return [SYNONYMS.get(part, part) for part in parts if part]


def dice(left: str, right: str) -> float:
    shared = len([token for token in tokens(left) if token in tokens(right)])
    return round(2 * shared / (len(tokens(left)) + len(tokens(right))), 2)


def best(source: str, targets: list[str]) -> tuple[str, float]:
    scored = sorted(((name, dice(source, name)) for name in targets), key=lambda pair: pair[1], reverse=True)
    return scored[0]


def status(score: float) -> str:
    return "auto" if score >= AUTO else "review" if score >= REVIEW else "manual"
