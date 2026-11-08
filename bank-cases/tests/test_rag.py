"""Тесты кейса 07: 240 проверок ассистента по банковским регламентам."""

from __future__ import annotations

import pytest

from cases import rag

QUESTIONS = [
    ("Как закрыть счёт при блокировке?", "rko", "rko-1"),
    ("Какие документы нужны для открытия расчётного счёта?", "rko", "rko-2"),
    ("Досрочное погашение кредита и пересчёт процентов", "credit", "credit-1"),
    ("Куда переносим начисленные проценты 47427?", "credit", "credit-2"),
    ("Пролонгация депозита и начисление процентов", "deposit", "deposit-1"),
    ("Расторжение депозитного договора", "deposit", "deposit-2"),
]
BANK = [(question, domain, doc) for question, domain, doc in QUESTIONS for _ in range(10)]
REFUSALS = [
    "Какой курс биткоина сегодня",
    "Регламент по ипотеке в иностранной валюте",
    "Сколько стоит лицензия на облако",
    "Как настроить принтер",
    "Где взять отпуск в мае",
    "Что такое криптобиржа",
]


@pytest.mark.parametrize(("question", "domain", "doc"), BANK)
def test_retrieval_finds_expected_document(question: str, domain: str, doc: str) -> None:
    assert doc in [item["id"] for item in rag.retrieve(question, domain)]


@pytest.mark.parametrize(("question", "domain", "doc"), BANK)
def test_answer_cites_source(question: str, domain: str, doc: str) -> None:
    assert rag.build(question, domain)["sources"][0] == doc


@pytest.mark.parametrize(("question", "domain", "doc"), BANK)
def test_answer_is_not_refusal_for_known_topic(question: str, domain: str, doc: str) -> None:
    reply = rag.build(question, domain)
    assert reply["answer"] != rag.REFUSAL and doc in reply["sources"]


@pytest.mark.parametrize("question", REFUSALS)
@pytest.mark.parametrize("domain", (None, "rko", "credit", "deposit"))
def test_unknown_topic_gets_refusal(question: str, domain: str | None) -> None:
    reply = rag.build(question, domain)
    assert reply["answer"] == rag.REFUSAL and reply["sources"] == []


def test_domain_filter_excludes_foreign_documents() -> None:
    assert all(item["domain"] == "credit" for item in rag.retrieve("кредит проценты", "credit"))


def test_limit_applies_to_retrieval() -> None:
    assert len(rag.retrieve("счёт кредит депозит", None, limit=1)) <= 1


def test_answered_flag_follows_sources() -> None:
    assert rag.answered(rag.build("Пролонгация депозита", "deposit")) is True


def test_answered_false_on_refusal() -> None:
    assert rag.answered(rag.build("Как настроить принтер")) is False


def test_score_is_zero_for_unrelated_text() -> None:
    assert rag.score("принтер картридж", rag.DOCS[0]) == 0
