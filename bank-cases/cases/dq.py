"""Кейс 02. Качество данных: контроль ИНН, БИК, счёта и сводка по домену."""

from __future__ import annotations

W10 = (2, 4, 10, 3, 5, 9, 4, 6, 8)
W11 = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
W12 = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)


def _digits(value: str) -> list[int]:
    return [int(char) for char in value]


def _control(digits: list[int], weights: tuple[int, ...]) -> int:
    return sum(digit * weight for digit, weight in zip(digits, weights, strict=False)) % 11 % 10


def inn_build(base9: str) -> str:
    """Собирает валидный 10-значный ИНН из первых девяти цифр."""
    return base9 + str(_control(_digits(base9), W10))


def _check10(value: str) -> bool:
    return _control(_digits(value[:9]), W10) == int(value[9])


def _check12(value: str) -> bool:
    return _control(_digits(value[:10]), W11) == int(value[10]) and _control(_digits(value[:11]), W12) == int(value[11])


def inn_valid(value: str) -> bool:
    checked = len(value) == 10 or len(value) == 12
    return value.isdigit() and checked and (_check10(value) if len(value) == 10 else _check12(value))


def bik_valid(value: str) -> bool:
    return len(value) == 9 and value.isdigit() and value.startswith("04")


def account_valid(value: str) -> bool:
    return len(value) == 20 and value.isdigit()


def severity(failed: int, total: int) -> str:
    return "critical" if failed / max(total, 1) > 0.05 else "warning" if failed else "ok"


def to_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def summarize(rows: list[dict[str, int]]) -> dict[str, object]:
    return {"checks": len(rows), "failed": sum(row["failed"] for row in rows), "rows": rows}
