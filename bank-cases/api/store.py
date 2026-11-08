"""Хранилище платформы: SQLite mig.db со схемой и детерминированными сидами."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("mig.db")

SCHEMA = """
create table if not exists legacy_field(
    id text primary key, table_name text, field text, data_type text, domain text, rows integer, nulls integer);
create table if not exists cft_field(name text primary key);
create table if not exists mapping(src text primary key, target text, score integer, status text, wave integer);
create table if not exists client(id text primary key, inn text, bik text, account text, balance real);
create table if not exists balance(
    account text, currency text, legacy real, cft real, wave integer, primary key(account, currency, wave));
create table if not exists posting(
    id integer primary key autoincrement, account text, oper_date text, dt real, kt real);
create table if not exists rule(id text primary key, title text, domain text, state text, sql text, cases text);
create table if not exists doc(id text primary key, domain text, text text);
create table if not exists domain(
    name text primary key, weight real, progress real, defects integer, gaps integer, dq integer);
create table if not exists service(
    name text primary key, version text, rps integer, p95 integer, status text, note text);
create table if not exists wave(n integer primary key, date text, state text, progress integer);
create table if not exists control(key text primary key, label text, enabled integer);
create table if not exists step(id text primary key, name text, role text, output text);
create table if not exists audit(
    id integer primary key autoincrement, ts text, user text, action text, payload text);
"""

TABLES = ("legacy_field", "cft_field", "mapping", "client", "balance", "posting", "rule", "doc",
          "domain", "service", "wave", "control", "step", "audit")

LEGACY = [
    ("f1", "PAYMENT_DOC", "SUMMA", "NUMBER(15,2)", "РКО", 184320, 12),
    ("f2", "PAYMENT_DOC", "DATA_DOC", "DATE", "РКО", 184320, 0),
    ("f3", "PAYMENT_DOC", "NSCHET", "VARCHAR2(20)", "РКО", 184320, 340),
    ("f4", "PAYMENT_DOC", "VAL", "CHAR(3)", "РКО", 184320, 0),
    ("f5", "CLIENT", "NAIM", "VARCHAR2(120)", "Клиенты", 96200, 4),
    ("f6", "CLIENT", "KOD", "NUMBER(10)", "Клиенты", 96200, 0),
    ("f7", "CREDIT", "KREDIT_ID", "NUMBER(10)", "Кредиты", 41200, 0),
    ("f8", "CREDIT", "SUMMA_VYDACHI", "NUMBER(15,2)", "Кредиты", 41200, 0),
    ("f9", "DEPOSIT", "OSTATOK", "NUMBER(15,2)", "Депозиты", 18700, 0),
    ("f10", "POSTING", "SCHET_DT", "VARCHAR2(20)", "Проводки", 4820000, 0),
    ("f11", "POSTING", "SCHET_KT", "VARCHAR2(20)", "Проводки", 4820000, 0),
    ("f12", "SCHET", "BIK", "CHAR(9)", "Счета", 143000, 310),
]

CFT = ["AMOUNT", "DOC_DATE", "PAYER_ACCOUNT", "CURRENCY", "CLIENT_NAME", "CLIENT_CODE",
       "CREDIT_ID", "CREDIT_AMOUNT", "BALANCE", "ACCOUNT_DT", "ACCOUNT_KT", "BIK"]

CLIENTS = [
    ("CL-0001", "7707083893", "044525225", "40817810099910004312", 125000.0),
    ("CL-0002", "7707083894", "044525225", "40817810099910004313", 8400.5),
    ("CL-0004", "770708389", "044525225", "40817810099910004314", 12500.0),
    ("CL-0006", "7707083893", "444525225", "40817810099910004316", 77000.0),
    ("CL-0011", "7707083893", "044525226", "40817810099910004318", -64000.0),
    ("CL-0012", "7830000001", "044030653", "408178104000000000", 200.0),
]

BALANCES = [
    ("40817810000000000001", "RUB", 125000.0, 125000.0, 5),
    ("40702810000000000011", "RUB", 1743000.0, 1735000.0, 5),
    ("47427810000000000021", "RUB", 43700.0, 43700.01, 5),
    ("40817810000000000001", "USD", 1500.0, 1512.4, 5),
    ("30102810000000000041", "RUB", 500000.0, 500000.0, 5),
    ("47400810000000000062", "RUB", 0.0, 345.6, 5),
    ("40817810000000000002", "RUB", 8400.5, 8400.5, 4),
    ("40702810000000000012", "RUB", 98000.0, 97300.0, 4),
]

POSTINGS = [
    ("47427810000000000021", "2026-11-03", 112500.0, 112500.0),
    ("47427810000000000022", "2026-11-03", 43000.0, 43000.5),
    ("40702810000000000011", "2026-11-03", 2500000.0, 2500000.0),
    ("70601810000000000071", "2026-11-04", 310000.0, 309999.99),
    ("47400810000000000062", "2026-10-31", 0.0, 345.6),
]

RULES = [
    ("R-114", "Проценты при досрочном закрытии", "Кредиты", "draft",
     "select credit_id, sum(amount) as interest from cft.interest where close_type = 'EARLY' group by credit_id",
     "нулевая сумма|частичное досрочное|закрытие в выходной"),
    ("R-121", "Депозит: пролонгация", "Депозиты", "approved",
     "select deposit_id, sum(amount) as balance from cft.deposit where state = 'ACTIVE' group by deposit_id",
     "нулевой остаток|пролонгация|последний день месяца"),
    ("R-133", "Платёж в проводках", "РКО", "approved",
     "select doc_id, sum(amount) as total from cft.payment where status = 'ACCEPTED' group by doc_id",
     "отклонённый документ|частичное исполнение|возврат"),
    ("R-140", "Сальдо по счёту", "Счета", "review",
     "select account, round(sum(dt_amount) - sum(kt_amount), 2) as balance from cft.posting group by account",
     "красное сальдо|закрытый период|счёт без проводок"),
    ("R-152", "Дубли клиентов", "Клиенты", "approved",
     "select client_id, count(*) as accounts from cft.account group by client_id having count(*) > 1",
     "совпадение ИНН|омонимы|клиент без счетов"),
]

DOCS = [
    ("rko-1", "рко", "Закрытие счёта при блокировке по решению налогового органа"),
    ("rko-2", "рко", "Открытие расчётного счёта: комплект документов и сроки"),
    ("credit-1", "кредиты", "Досрочное погашение кредита: пересчёт процентов и проводки"),
    ("credit-2", "кредиты", "Начисление резерва по кредиту и перенос на 47427"),
    ("deposit-1", "депозиты", "Депозит: пролонгация договора и начисление процентов"),
]

DOMAINS = [
    ("РКО", 0.3, 0.94, 4, 2, 60),
    ("Кредиты", 0.25, 0.78, 11, 6, 240),
    ("Депозиты", 0.15, 0.86, 5, 3, 95),
    ("Счета", 0.2, 0.91, 6, 1, 40),
    ("Проводки", 0.1, 0.62, 18, 9, 410),
]

SERVICES = [
    ("gateway", "2.4.11", 128, 41, "ok", "auth · rate limit · audit"),
    ("s2t-svc", "2.4.3", 27, 62, "ok", "карта полей и подтверждение"),
    ("dq-svc", "2.4.7", 14, 118, "ok", "профиль домена до загрузки"),
    ("recon-svc", "2.3.9", 9, 210, "warn", "сальдо legacy vs ЦФТ"),
    ("rule-svc", "2.4.1", 6, 87, "ok", "правило → SQL-черновик"),
    ("posting-svc", "2.4.5", 88, 35, "ok", "двойная запись и хронология"),
    ("cutover-svc", "2.2.4", 3, 24, "ok", "полнота процесса"),
    ("assist-svc", "1.9.2", 11, 640, "ok", "вопросы по регламентам"),
    ("tower-svc", "2.4.0", 4, 55, "ok", "готовность и прогноз"),
]

WAVES = [(1, "12.09", "closed", 100), (2, "10.10", "closed", 100), (3, "24.10", "closed", 100),
         (4, "01.11", "closed", 100), (5, "08.11", "active", 12), (6, "22.11", "planned", 0)]

CONTROLS = [("owner", "Владелец шага", 1), ("rollback", "Точка отката", 0),
            ("window", "Окно простоя", 1), ("checkpoint", "Критерий готовности", 0)]

STEPS = [
    ("ST-01", "Остановка приёма платежей", "операционный блок", "приказ"),
    ("ST-02", "Финальная выгрузка остатков", "DBA", "дамп"),
    ("ST-03", "Загрузка в ЦФТ-Банк", "", "лог загрузки"),
    ("ST-04", "Сверка остатков", "аналитик", "отчёт"),
    ("ST-05", "Включение операций", "операционный блок", ""),
    ("ST-06", "План отката", "архитектор", "регламент"),
]


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def rows(sql: str, params: tuple = ()) -> list[dict]:
    with connect() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def one(sql: str, params: tuple = ()) -> dict | None:
    with connect() as connection:
        row = connection.execute(sql, params).fetchone()
        return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> None:
    with connect() as connection:
        connection.execute(sql, params)
        connection.commit()


def init_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)
        migrate(connection)
        connection.commit()
    seed_if_empty()


def migrate(connection: sqlite3.Connection) -> None:
    columns = [row[1] for row in connection.execute("pragma table_info(audit)").fetchall()]
    if "user" not in columns:
        connection.execute("alter table audit add column user text")


def seed_if_empty() -> None:
    if one("select count(*) as total from legacy_field")["total"]:
        return
    with connect() as connection:
        seed_core(connection)
        seed_runtime(connection)
        connection.commit()


def seed_core(connection: sqlite3.Connection) -> None:
    connection.executemany("insert into legacy_field values (?, ?, ?, ?, ?, ?, ?)", LEGACY)
    connection.executemany("insert into cft_field values (?)", [(name,) for name in CFT])
    connection.executemany("insert into client values (?, ?, ?, ?, ?)", CLIENTS)
    connection.executemany("insert into balance values (?, ?, ?, ?, ?)", BALANCES)
    connection.executemany(
        "insert into posting(account, oper_date, dt, kt) values (?, ?, ?, ?)", POSTINGS)


def seed_runtime(connection: sqlite3.Connection) -> None:
    connection.executemany("insert into rule values (?, ?, ?, ?, ?, ?)", RULES)
    connection.executemany("insert into doc values (?, ?, ?)", DOCS)
    connection.executemany("insert into domain values (?, ?, ?, ?, ?, ?)", DOMAINS)
    connection.executemany("insert into service values (?, ?, ?, ?, ?, ?)", SERVICES)
    connection.executemany("insert into wave values (?, ?, ?, ?)", WAVES)
    connection.executemany("insert into control values (?, ?, ?)", CONTROLS)
    connection.executemany("insert into step values (?, ?, ?, ?)", STEPS)


def reset_db() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)
        migrate(connection)
        for table in TABLES:
            connection.execute(f"delete from {table}")
        connection.commit()
    seed_if_empty()


def audit(action: str, payload: str, user: str = "system") -> None:
    execute("insert into audit(ts, user, action, payload) values (datetime('now'), ?, ?, ?)",
            (user, action, payload))


def audit_tail(limit: int = 50) -> list[dict]:
    return rows("select * from audit order by id desc limit ?", (limit,))
