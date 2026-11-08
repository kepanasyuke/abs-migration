"""Тесты кейса 04: 240 проверок разбора бизнес-правил в SQL-заготовку."""

from __future__ import annotations

import pytest

from cases import rule2sql

SAMPLES = {
    "interest": "При досрочном закрытии кредита начисленные проценты переносим на 47427",
    "deposit": "Депозит юридического лица: пролонгация и начисление процентов",
    "payment": "Платёжное поручение в статусе «принято» отражаем в проводках",
    "account": "Сальдо по счёту должно совпадать с обороткой на конец дня",
    "client": "Дубли клиентов по совпадению ИНН объединяем перед загрузкой",
    "card": "Операции по карте без авторизации относим в карантин",
}
TEXTS = [(name, f"{sample} (вариант {variant})") for name, sample in SAMPLES.items() for variant in range(1, 11)]
DOMAINS = ("rko", "credit", "deposit", "posting")


@pytest.mark.parametrize(("name", "text"), TEXTS)
def test_keyword_detected(name: str, text: str) -> None:
    assert rule2sql.keyword(text) == name


@pytest.mark.parametrize(("name", "text"), TEXTS)
def test_sql_template_selected(name: str, text: str) -> None:
    assert rule2sql.to_sql(text, "credit") == rule2sql.TEMPLATES[name]


@pytest.mark.parametrize(("name", "text"), TEXTS)
def test_edge_cases_non_empty(name: str, text: str) -> None:
    assert rule2sql.edge_cases(text) == rule2sql.CASES[name]


@pytest.mark.parametrize(("name", "text"), TEXTS)
def test_draft_requires_review(name: str, text: str) -> None:
    draft = rule2sql.validate(text, name)
    assert draft["needs_review"] is True and draft["domain"] == name


@pytest.mark.parametrize("domain", DOMAINS)
def test_unknown_rule_falls_back_to_manual(domain: str) -> None:
    draft = rule2sql.validate("Правило без ключевых слов", domain)
    assert draft["needs_review"] is False and "select" in str(draft["sql"])


def test_generated_sql_is_select() -> None:
    assert all(rule2sql.to_sql(text, "credit").startswith("select") for _, text in TEXTS)


def test_rule_text_preserved_in_draft() -> None:
    text = "Депозит: пролонгация договора"
    assert rule2sql.validate(text, "deposit")["rule"] == text


def test_unknown_rule_gets_default_case() -> None:
    assert rule2sql.edge_cases("ничего не распознано") == ["правило не распознано"]
