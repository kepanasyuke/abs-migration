"""Тесты кейса 06: 240 проверок полноты BPMN-процесса переключения."""

from __future__ import annotations

from itertools import combinations

import pytest

from cases import cutover

CONTROL_SETS = [combo for size in range(5) for combo in combinations(cutover.REQUIRED, size)]
PROCESSES = [{"id": f"cutover-{index}", "controls": list(controls)} for index, controls in enumerate(CONTROL_SETS)]
STEPS = [
    {"id": f"step-{index}", "role": "analyst" if index % 2 else "", "output": "документ" if index % 3 else ""}
    for index in range(12)
]
PROCESSES_WITH_STEPS = [
    {"id": f"process-{index}", "controls": list(CONTROL_SETS[index % len(CONTROL_SETS)]), "steps": STEPS}
    for index in range(46)
]


@pytest.mark.parametrize("process", PROCESSES_WITH_STEPS)
def test_gaps_only_from_required_controls(process: dict[str, object]) -> None:
    assert set(cutover.gaps(process)) <= set(cutover.REQUIRED)


@pytest.mark.parametrize("process", PROCESSES_WITH_STEPS)
def test_gaps_are_complement_of_controls(process: dict[str, object]) -> None:
    assert set(cutover.gaps(process)) == set(cutover.REQUIRED) - set(process["controls"])


@pytest.mark.parametrize("process", PROCESSES_WITH_STEPS)
def test_readiness_matches_gaps(process: dict[str, object]) -> None:
    report = cutover.readiness(process)
    assert report["ready"] is (not cutover.gaps(process)) and report["process"] == process["id"]


@pytest.mark.parametrize("process", PROCESSES_WITH_STEPS)
def test_coverage_reflects_missing_controls(process: dict[str, object]) -> None:
    assert cutover.coverage(process) == round(1 - len(cutover.gaps(process)) / 4, 2)


@pytest.mark.parametrize("process", PROCESSES_WITH_STEPS)
def test_blocking_requires_critical_gap(process: dict[str, object]) -> None:
    critical = set(cutover.critical(process)) & {"rollback", "checkpoint"}
    assert cutover.blocking(process) is bool(critical)


@pytest.mark.parametrize("process", PROCESSES_WITH_STEPS)
def test_semantic_gaps_find_incomplete_steps(process: dict[str, object]) -> None:
    gaps = cutover.semantic_gaps(process)
    assert len(gaps) == len([step for step in STEPS if not step["role"] or not step["output"]])


def test_full_control_set_is_ready() -> None:
    assert cutover.readiness({"id": "full", "controls": list(cutover.REQUIRED)})["ready"] is True


def test_process_without_controls_is_blocked() -> None:
    assert cutover.blocking({"id": "empty", "controls": []}) is True


def test_all_control_combinations_covered() -> None:
    assert len(CONTROL_SETS) == 16


def test_missing_semantic_gaps_when_all_steps_complete() -> None:
    steps = [{"id": "s1", "role": "analyst", "output": "акт"}]
    assert cutover.semantic_gaps({"id": "ok", "steps": steps}) == []
