"""Кейс 06. Cut-over: полнота BPMN-процесса переключения на ЦФТ-Банк."""

from __future__ import annotations

REQUIRED = ("owner", "rollback", "window", "checkpoint")
CRITICAL = ("rollback", "checkpoint")


def gaps(process: dict[str, object]) -> list[str]:
    controls = set(process.get("controls", ()))
    return [name for name in REQUIRED if name not in controls]


def readiness(process: dict[str, object]) -> dict[str, object]:
    missing = gaps(process)
    return {"process": process.get("id"), "gaps": missing, "ready": not missing}


def critical(process: dict[str, object]) -> list[str]:
    return [name for name in gaps(process) if name in CRITICAL]


def semantic_gaps(process: dict[str, object]) -> list[str]:
    steps = process.get("steps", [])
    return [str(step.get("id")) for step in steps if not step.get("output") or not step.get("role")]


def coverage(process: dict[str, object]) -> float:
    return round(1 - len(gaps(process)) / len(REQUIRED), 2)


def blocking(process: dict[str, object]) -> bool:
    return bool(critical(process))
