"""Кейс 07. Ассистент по домену: поиск по регламентам с обязательным источником."""

from __future__ import annotations

from cases.common import keywords

REFUSAL = "В загруженных документах нет ответа на этот вопрос."

DOCS = [
    {"id": "rko-1", "domain": "rko", "text": "Закрытие счёта при блокировке по решению налогового органа"},
    {"id": "rko-2", "domain": "rko", "text": "Открытие расчётного счёта: комплект документов и сроки"},
    {"id": "credit-1", "domain": "credit", "text": "Досрочное погашение кредита: пересчёт процентов и проводки"},
    {"id": "credit-2", "domain": "credit", "text": "Начисление резерва по кредиту и перенос на 47427"},
    {"id": "deposit-1", "domain": "deposit", "text": "Депозит: пролонгация договора и начисление процентов"},
    {"id": "deposit-2", "domain": "deposit", "text": "Расторжение депозитного договора юридического лица"},
]


def score(question: str, doc: dict[str, str]) -> int:
    return len(keywords(question) & keywords(doc["text"]))


def retrieve(question: str, domain: str | None = None, limit: int = 2) -> list[dict[str, str]]:
    pool = [doc for doc in DOCS if domain is None or doc["domain"] == domain]
    ranked = sorted(pool, key=lambda doc: score(question, doc), reverse=True)
    return [doc for doc in ranked[:limit] if score(question, doc) > 0]


def compose(question: str, chunks: list[dict[str, str]]) -> str:
    source = chunks[0] if chunks else None
    return f"По вопросу «{question}»: {source['text']} (источник {source['id']})." if source else REFUSAL


def build(question: str, domain: str | None = None) -> dict[str, object]:
    chunks = retrieve(question, domain)
    return {"answer": compose(question, chunks), "sources": [chunk["id"] for chunk in chunks]}


def answered(reply: dict[str, object]) -> bool:
    return bool(reply.get("sources"))
