"""Кейс 03. Сверка остатков: расхождение legacy и целевой АБС по счетам."""

from __future__ import annotations


def diff(legacy: float, target: float) -> float:
    return round(target - legacy, 2)


def _index(rows: list[dict[str, object]]) -> dict[tuple[str, str], float]:
    return {(str(row["account"]), str(row["currency"])): float(row["balance"]) for row in rows}


def row(client: dict[str, object], base: dict[tuple[str, str], float]) -> dict[str, object]:
    key = (str(client["account"]), str(client["currency"]))
    return {"account": key[0], "currency": key[1], "delta": diff(base.get(key, 0.0), float(client["balance"]))}


def reconcile(legacy: list[dict[str, object]], target: list[dict[str, object]]) -> list[dict[str, object]]:
    base = _index(legacy)
    return [row(client, base) for client in target]


def _cause(currency: str, duplicate: bool, manual: bool, small: bool) -> str:
    base = "duplicate" if duplicate else "manual" if manual else "rounding" if small else "rate"
    return base if base != "rate" or currency != "RUB" else "missing_posting"


def classify(cell: dict[str, object]) -> str:
    duplicate, manual = bool(cell.get("duplicate")), bool(cell.get("manual"))
    return _cause(str(cell.get("currency", "RUB")), duplicate, manual, abs(float(cell["delta"])) < 0.01)


def explain(cells: list[dict[str, object]]) -> list[dict[str, object]]:
    return [{**cell, "cause": classify(cell)} for cell in cells]


def grouped(cells: list[dict[str, object]]) -> dict[str, int]:
    causes = sorted({str(cell["cause"]) for cell in cells})
    return {cause: len([cell for cell in cells if cell["cause"] == cause]) for cause in causes}


def is_explained(cell: dict[str, object]) -> bool:
    return str(cell.get("cause", "unknown")) != "unknown"
