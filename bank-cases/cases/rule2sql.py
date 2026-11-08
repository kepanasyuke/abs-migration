"""Кейс 04. Правило трансформации: текст банка, SQL-заготовка и граничные случаи."""

from __future__ import annotations

TEMPLATES = {
    "interest": (
        "select credit_id, sum(amount) as interest from cft.interest "
        "where close_type = 'EARLY' group by credit_id"
    ),
    "deposit": "select deposit_id, sum(amount) as balance from cft.deposit where state = 'ACTIVE' group by deposit_id",
    "payment": "select doc_id, sum(amount) as total from cft.payment where status = 'ACCEPTED' group by doc_id",
    "account": "select account, round(sum(dt_amount) - sum(kt_amount), 2) as balance from cft.posting group by account",
    "client": "select client_id, count(*) as accounts from cft.account group by client_id having count(*) > 1",
    "card": "select card_id, count(*) as operations from cft.card_operation group by card_id",
}

MARKERS = {
    "payment": ("платёж", "платеж", "перевод"),
    "deposit": ("депозит", "вклад"),
    "account": ("счёт", "счет", "сальдо"),
    "client": ("клиент", "дубл"),
    "card": ("карт",),
    "interest": ("процент", "interest"),
}

CASES = {
    "interest": ["нулевая сумма", "частичное досрочное погашение", "закрытие в выходной день"],
    "deposit": ["нулевой остаток", "пролонгация", "закрытие в последний день месяца"],
    "payment": ["отклонённый документ", "частичное исполнение", "возврат платежа"],
    "account": ["красное сальдо", "закрытый период", "счёт без проводок"],
    "client": ["совпадение ИНН", "омонимы", "клиент без счетов"],
    "card": ["перевыпуск карты", "операция без авторизации", "чарджбэк"],
}

UNKNOWN = "manual"


def keyword(text: str) -> str:
    lowered = text.lower()
    matches = (name for name, markers in MARKERS.items() if any(marker in lowered for marker in markers))
    return next(matches, UNKNOWN)


def to_sql(text: str, domain: str) -> str:
    fallback = f"select /* {domain}: ручной разбор */ 1"
    return TEMPLATES.get(keyword(text), fallback)


def edge_cases(text: str) -> list[str]:
    return CASES.get(keyword(text), ["правило не распознано"])


def validate(text: str, domain: str) -> dict[str, object]:
    sql = to_sql(text, domain)
    return {"rule": text, "domain": domain, "sql": sql, "status": "draft", "needs_review": keyword(text) in TEMPLATES}
