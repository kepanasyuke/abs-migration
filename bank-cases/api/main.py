"""FastAPI-сервис платформы миграции АБС → ЦФТ-Банк поверх SQLite mig.db."""

from __future__ import annotations

import asyncio
import json
import random
import secrets
from collections.abc import AsyncIterator, Callable
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from api import logic, store
from cases import cutover as cutover_case
from cases import dq as dq_case
from cases import postings as postings_case
from cases import rag as rag_case
from cases import reconcile as reconcile_case
from cases import rule2sql as rule_case
from cases import tower as tower_case

VERSION = "2.4.11"
APP_HTML = Path(__file__).resolve().parents[2] / "abs-migration-desktop.html"
DOMAIN_CODES = {"РКО": "rko", "Кредиты": "credit", "Депозиты": "deposit", "Все": None}
CHECKS = (("inn", dq_case.inn_valid), ("bik", dq_case.bik_valid), ("account", dq_case.account_valid))

USERS = {
    "analyst": {"password": "analyst123", "name": "Анна Соколова", "role": "analyst",
                "role_title": "системный аналитик"},
    "architect": {"password": "architect123", "name": "Илья Петров", "role": "architect",
                  "role_title": "архитектор миграции"},
    "auditor": {"password": "auditor123", "name": "Ольга Ли", "role": "auditor",
                "role_title": "аудитор"},
}

PERMS = {
    "analyst": ("mapping.confirm", "dq.scan", "rules.compile", "assist.ask", "csv.export"),
    "architect": ("mapping.confirm", "dq.scan", "rules.compile", "assist.ask", "csv.export",
                  "cutover.control", "cutover.schedule", "wave.start", "audit.read"),
    "auditor": ("csv.export", "audit.read"),
}

SESSIONS: dict[str, dict] = {}

app = FastAPI(title="АБС-Миграция API", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
store.init_db()


class ConfirmIn(BaseModel):
    src: str
    target: str = ""


class RuleIn(BaseModel):
    text: str
    domain: str = "Кредиты"


class AskIn(BaseModel):
    question: str
    domain: str | None = None


class ControlIn(BaseModel):
    key: str
    value: bool


class ScheduleIn(BaseModel):
    date: str


class LoginIn(BaseModel):
    user: str
    password: str


def current_user(authorization: str = Header(default="")) -> dict:
    session = SESSIONS.get(authorization.replace("Bearer ", "").strip())
    if not session:
        raise HTTPException(status_code=401, detail="требуется вход")
    return session


def require(permission: str) -> Callable[..., dict]:
    def guard(session: dict = Depends(current_user)) -> dict:
        allowed = PERMS.get(session["role"], ())
        if permission not in allowed:
            raise HTTPException(status_code=403, detail=f"нет права {permission}")
        return session
    return guard


GUARD_CONFIRM = require("mapping.confirm")
GUARD_DQ = require("dq.scan")
GUARD_RULES = require("rules.compile")
GUARD_ASSIST = require("assist.ask")
GUARD_CONTROL = require("cutover.control")
GUARD_SCHEDULE = require("cutover.schedule")
GUARD_WAVE = require("wave.start")
GUARD_AUDIT = require("audit.read")


@app.post("/api/v1/auth/login")
def login(payload: LoginIn) -> dict:
    account = USERS.get(payload.user)
    if not account or account["password"] != payload.password:
        raise HTTPException(status_code=401, detail="неверный логин или пароль")
    token = secrets.token_urlsafe(18)
    session = {"token": token, "user": payload.user, "name": account["name"],
               "role": account["role"], "role_title": account["role_title"]}
    SESSIONS[token] = session
    store.audit("auth.login", payload.user, payload.user)
    return {**session, "perms": list(PERMS[account["role"]])}


@app.get("/api/v1/auth/me")
def me(session: dict = Depends(current_user)) -> dict:
    return {**session, "perms": list(PERMS.get(session["role"], ()))}


@app.post("/api/v1/auth/logout")
def logout(session: dict = Depends(current_user)) -> dict:
    SESSIONS.pop(session["token"], None)
    store.audit("auth.logout", session["user"], session["user"])
    return {"ok": True}


@app.get("/api/v1/audit")
def audit_log(session: dict = Depends(GUARD_AUDIT), limit: int = 50) -> dict:
    return {"items": store.audit_tail(limit), "actor": session["user"]}


@app.get("/app")
def app_page() -> FileResponse:
    return FileResponse(APP_HTML, media_type="text/html")


@app.get("/api/v1/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": VERSION,
        "db": "sqlite://api/mig.db",
        "services": len(store.rows("select name from service")),
        "wave": store.one("select max(n) as wave from wave")["wave"],
    }


@app.get("/api/v1/s2t/fields")
def s2t_fields(wave: int = 5) -> dict:
    targets = [row["name"] for row in store.rows("select name from cft_field")]
    legacy = store.rows("select * from legacy_field order by id")
    return {"wave": wave, "items": [mapping_item(row, targets) for row in legacy]}


def mapping_item(field: dict, targets: list[str]) -> dict:
    target, score = logic.best(field["field"], targets)
    return {"src": f"{field['table_name']}.{field['field']}", "type": field["data_type"], "dom": field["domain"],
            "tgt": target, "score": round(score * 100), "status": logic.status(score)}


@app.post("/api/v1/s2t/confirm")
def s2t_confirm(payload: ConfirmIn, session: dict = Depends(GUARD_CONFIRM)) -> dict:
    store.execute(
        "insert into mapping(src, target, status, wave) values (?, ?, 'confirmed', 5) "
        "on conflict(src) do update set status = 'confirmed', target = excluded.target",
        (payload.src, payload.target),
    )
    store.audit("s2t.confirm", payload.src, session["user"])
    return {"ok": True, "src": payload.src, "status": "confirmed"}


@app.get("/api/v1/dq/scan/{table}")
def dq_scan(table: str, session: dict = Depends(GUARD_DQ)) -> dict:
    clients = store.rows("select * from client order by id")
    issues = [issue_item(row) for row in clients if issue_rules(row)]
    store.audit("dq.scan", table, session["user"])
    return {"table": table, "rows": len(clients), "issues": issues}


def issue_rules(row: dict) -> list[str]:
    rules = [name for name, check in CHECKS if not check(row[name])]
    return rules + ["balance"] if row["balance"] < 0 else rules


def issue_item(row: dict) -> dict:
    rules = issue_rules(row)
    return {"id": row["id"], "inn": row["inn"], "bik": row["bik"], "account": row["account"],
            "balance": row["balance"], "rules": rules, "severity": dq_case.severity(len(rules), 1)}


@app.get("/api/v1/recon/{wave}")
def recon(wave: int) -> dict:
    items = [recon_item(row) for row in store.rows("select * from balance where wave = ? order by account", (wave,))]
    return {"wave": wave, "items": items, "total": round(sum(abs(item["delta"]) for item in items), 2)}


def recon_item(row: dict) -> dict:
    delta = reconcile_case.diff(row["legacy"], row["cft"])
    cause = reconcile_case.classify({"delta": delta, "currency": row["currency"]})
    return {"account": row["account"], "currency": row["currency"], "legacy": row["legacy"],
            "cft": row["cft"], "delta": delta, "cause": cause}


@app.get("/api/v1/rules")
def rules_list() -> dict:
    items = store.rows("select * from rule order by id")
    return {"items": [{**row, "cases": row["cases"].split("|")} for row in items]}


@app.post("/api/v1/rules/compile")
def rules_compile(payload: RuleIn, session: dict = Depends(GUARD_RULES)) -> dict:
    draft = rule_case.validate(payload.text, payload.domain)
    store.audit("rule.compile", payload.text[:120], session["user"])
    return {"rule": draft["rule"], "sql": draft["sql"], "domain": payload.domain,
            "cases": rule_case.edge_cases(payload.text), "needs_review": draft["needs_review"]}


@app.get("/api/v1/postings/balance")
def postings_balance() -> dict:
    items = [posting_item(row) for row in store.rows("select * from posting order by account")]
    unbalanced = [item for item in items if item["delta"] != 0]
    total = round(sum(abs(item["delta"]) for item in unbalanced), 2)
    return {"items": items, "unbalanced": len(unbalanced), "total": total}


def posting_item(row: dict) -> dict:
    return {"account": row["account"], "date": row["oper_date"], "dt": row["dt"], "kt": row["kt"],
            "delta": postings_case.delta([{"dt": row["dt"], "kt": row["kt"]}])}


@app.get("/api/v1/cutover/{run}")
def cutover_state(run: str) -> dict:
    controls = {row["key"]: bool(row["enabled"]) for row in store.rows("select * from control")}
    steps = store.rows("select * from step order by id")
    process = {"id": run, "controls": [key for key, value in controls.items() if value], "steps": steps}
    return {"run": run, "controls": controls, "steps": steps, "gaps": cutover_case.gaps(process),
            "critical": cutover_case.critical(process), "coverage": cutover_case.coverage(process),
            "ready": not cutover_case.gaps(process), "semantic_gaps": cutover_case.semantic_gaps(process)}


@app.post("/api/v1/cutover/controls")
def cutover_controls(payload: ControlIn, session: dict = Depends(GUARD_CONTROL)) -> dict:
    store.execute("update control set enabled = ? where key = ?", (1 if payload.value else 0, payload.key))
    store.audit("cutover.control", payload.key, session["user"])
    return cutover_state("cutover-wave-5")


@app.post("/api/v1/cutover/schedule")
def cutover_schedule(payload: ScheduleIn, session: dict = Depends(GUARD_SCHEDULE)) -> dict:
    store.audit("cutover.schedule", payload.date, session["user"])
    return {"ok": True, "date": payload.date}


@app.post("/api/v1/assist/ask")
def assist(payload: AskIn, session: dict = Depends(GUARD_ASSIST)) -> dict:
    reply = rag_case.build(payload.question, DOMAIN_CODES.get(payload.domain or "Все"))
    store.audit("assist.ask", payload.question[:120], session["user"])
    return {"answer": reply["answer"], "sources": reply["sources"]}


@app.get("/api/v1/tower/readiness")
def tower_readiness() -> dict:
    domains = store.rows("select * from domain")
    items = [domain_item(domain) for domain in domains]
    return {"domains": items, "total": tower_case.total_progress(domains),
            "forecast": tower_case.forecast([4, 5, 4, 6], done=62, total=100, today=date(2026, 11, 8)).isoformat()}


def domain_item(domain: dict) -> dict:
    score = tower_risk(domain)
    return {**domain, "risk": score, "status": tower_case.status(score)}


def tower_risk(domain: dict) -> float:
    payload = {"open_defects": domain["defects"], "s2t_gaps": domain["gaps"], "dq_failed": domain["dq"]}
    return tower_case.risk_score(payload)


@app.get("/api/v1/services")
def services() -> dict:
    return {"items": store.rows("select * from service order by name")}


@app.get("/api/v1/docs")
def docs() -> dict:
    return {"items": store.rows("select * from doc order by id")}


@app.get("/api/v1/waves")
def waves() -> dict:
    return {"items": store.rows("select * from wave order by n")}


@app.post("/api/v1/waves/{number}/start")
def wave_start(number: int, session: dict = Depends(GUARD_WAVE)) -> dict:
    store.execute("update wave set state = 'running', progress = 8 where n = ?", (number,))
    store.audit("wave.start", str(number), session["user"])
    job = f"job-{number}-{store.one('select count(*) as total from audit')['total']}"
    return {"wave": number, "state": "running", "progress": 8, "job": job}


@app.get("/api/v1/waves/{number}/progress")
async def wave_progress(number: int) -> StreamingResponse:
    return StreamingResponse(progress_stream(number), media_type="text/event-stream")


async def progress_stream(number: int) -> AsyncIterator[str]:
    for percent in (8, 18, 27, 36, 45, 54, 63, 72, 81, 90, 100):
        state = "closed" if percent == 100 else "running"
        store.execute("update wave set progress = ?, state = ? where n = ?", (percent, state, number))
        yield "data: " + json.dumps({"wave": number, "percent": percent, "state": state}) + "\n\n"
        await asyncio.sleep(0.4)


@app.get("/api/v1/services/telemetry")
def telemetry() -> dict:
    return {"items": [telemetry_item(row) for row in store.rows("select * from service order by name")]}


def telemetry_item(row: dict) -> dict:
    drift = random.randint(-4, 6)
    return {**row, "rps": max(row["rps"] + drift, 1), "p95": max(row["p95"] + drift * 2, 12)}


@app.post("/api/v1/admin/reset")
def admin_reset() -> dict:
    store.reset_db()
    return {"ok": True, "status": "reseeded"}
