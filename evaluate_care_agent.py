"""Behavioral reliability evaluation for CareAgent — distinct from the unit tests
in tests/test_ai_agent.py, which check individual functions in isolation.

This runs the *full* plan_care_tasks() pipeline end-to-end across a handful of
representative (and deliberately awkward/edge-case) pet scenarios, checks each
result against a human-readable pass/fail criterion, and writes the results to
eval_results.md as a markdown table plus a one-line summary — so reliability
can be read without re-running anything, and re-run deterministically by
anyone (no API key required; uses the same offline fallback path the app
falls back to in production).

Run it with:
    python evaluate_care_agent.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple

from ai_agent import AgentResult, CareAgent
from pawpal_system import Owner, Pet, Task

Check = Callable[[AgentResult], Tuple[bool, str]]


@dataclass
class Scenario:
    name: str
    pet: Pet
    owner: Owner
    existing_tasks: List[Task]
    criteria: str
    check: Check
    max_tasks: int = 3


def _valid_bounds(task: Task) -> bool:
    return (
        1 <= task.duration_minutes <= 240
        and task.priority in {"low", "medium", "high"}
        and task.frequency in {"daily", "weekly", "one-time"}
    )


def check_produces_valid_grounded_tasks(result: AgentResult) -> Tuple[bool, str]:
    if not result.tasks:
        return False, "expected at least one drafted task, got none"
    if not result.sources:
        return False, "expected retrieved sources to be non-empty"
    if not all(_valid_bounds(t) for t in result.tasks):
        return False, "a drafted task violated duration/priority/frequency bounds"
    return True, f"{len(result.tasks)} task(s), {len(result.sources)} source(s), all within bounds"


def check_no_conflict_with_existing(result: AgentResult) -> Tuple[bool, str]:
    conflicting = [t for t in result.tasks if t.due_time == "7:00 AM"]
    if conflicting:
        return False, f"{len(conflicting)} drafted task(s) still collide with the existing 7:00 AM task"
    if result.warnings:
        return True, f"conflict resolved with a logged warning: {result.warnings}"
    return True, "no drafted task collides with the pet's existing 7:00 AM task"

def check_relevant_guideline_prioritized(result: AgentResult) -> Tuple[bool, str]:
    if not any("senior" in source.lower() for source in result.sources):
        return False, "expected the senior-pet guideline to be retrieved for a senior, medicated dog"
    return True, f"senior-pet guideline retrieved among: {result.sources}"


def check_handles_unknown_species_gracefully(result: AgentResult) -> Tuple[bool, str]:
    # No guideline in the knowledge base matches "iguana" - the correct, honest
    # behavior is zero suggestions, not a crash and not a fabricated guess.
    if result.tasks or result.sources:
        return False, "expected no tasks/sources for a species outside the knowledge base"
    if not result.explanation:
        return False, "expected an explanation even when nothing was drafted"
    return True, "returned an empty, explained result instead of crashing or guessing"


def check_max_tasks_is_respected(result: AgentResult) -> Tuple[bool, str]:
    if len(result.tasks) > 1:
        return False, f"max_tasks=1 was requested but {len(result.tasks)} tasks were drafted"
    return True, f"{len(result.tasks)} task(s) drafted, within the requested max_tasks=1"


def check_offline_fallback_used(result: AgentResult) -> Tuple[bool, str]:
    if result.used_llm:
        return False, "expected the offline fallback path (client forced to None) but used_llm=True"
    return True, "used_llm=False, confirming the offline fallback path actually ran"


def _owner() -> Owner:
    return Owner(name="Jordan", age=29, gender="", location="Austin, TX", years_owned=3)


SCENARIOS: List[Scenario] = [
    Scenario(
        name="Dog, empty schedule",
        pet=Pet(name="Rex", animal_type="dog", breed="Golden Retriever", preferred_time_of_day="morning"),
        owner=_owner(),
        existing_tasks=[],
        criteria="Produces >=1 grounded, in-bounds task from retrieved sources",
        check=check_produces_valid_grounded_tasks,
    ),
    Scenario(
        name="Cat, conflicting existing task",
        pet=Pet(name="Whiskers", animal_type="cat", breed="Siamese", preferred_time_of_day="evening"),
        owner=_owner(),
        existing_tasks=[Task(title="Feed Whiskers", type="feeding", duration_minutes=10, due_time="7:00 AM")],
        criteria="No drafted task collides with the existing 7:00 AM task",
        check=check_no_conflict_with_existing,
    ),
    Scenario(
        name="Senior dog on medication",
        pet=Pet(name="Biscuit", animal_type="dog", breed="Senior Labrador", medications=["arthritis medication"]),
        owner=_owner(),
        existing_tasks=[],
        criteria="Retrieves the senior-pet guideline, not just generic dog guidelines",
        check=check_relevant_guideline_prioritized,
    ),
    Scenario(
        name="Unknown species (iguana)",
        pet=Pet(name="Iggy", animal_type="iguana"),
        owner=_owner(),
        existing_tasks=[],
        criteria="Handles a species outside the knowledge base gracefully (no crash, no fabrication)",
        check=check_handles_unknown_species_gracefully,
    ),
    Scenario(
        name="max_tasks is respected",
        pet=Pet(name="Rex", animal_type="dog", breed="Golden Retriever"),
        owner=_owner(),
        existing_tasks=[],
        criteria="Requesting max_tasks=1 drafts at most 1 task",
        check=check_max_tasks_is_respected,
        max_tasks=1,
    ),
    Scenario(
        name="Offline fallback path actually runs",
        pet=Pet(name="Rex", animal_type="dog", breed="Golden Retriever"),
        owner=_owner(),
        existing_tasks=[],
        criteria="used_llm is False when the client is unavailable",
        check=check_offline_fallback_used,
    ),
]


def run() -> None:
    agent = CareAgent()
    agent.client = None  # force the offline fallback path for a reproducible, key-free evaluation

    rows = []
    passed = 0
    for scenario in SCENARIOS:
        result = agent.plan_care_tasks(
            pet=scenario.pet,
            owner=scenario.owner,
            existing_tasks=scenario.existing_tasks,
            max_tasks=scenario.max_tasks,
        )
        ok, detail = scenario.check(result)
        passed += int(ok)
        rows.append((scenario.name, scenario.criteria, "Pass" if ok else "Fail", detail))

    total = len(SCENARIOS)
    summary = (
        f"{passed} out of {total} reliability checks passed "
        f"({100 * passed // total}%) against the offline-fallback pipeline."
    )

    lines = [
        "# CareAgent Reliability Evaluation",
        "",
        "Generated by `evaluate_care_agent.py` — end-to-end behavioral checks against",
        "`CareAgent.plan_care_tasks()`, run with the offline fallback path forced on so",
        "results are deterministic and reproducible with no API key required.",
        "",
        f"**Summary:** {summary}",
        "",
        "| Scenario | Evaluation Criteria | Result | Detail |",
        "|---|---|---|---|",
    ]
    for name, criteria, status, detail in rows:
        lines.append(f"| {name} | {criteria} | {status} | {detail} |")
    lines.append("")

    report = "\n".join(lines)
    with open("eval_results.md", "w", encoding="utf-8") as f:
        f.write(report)

    print(summary)
    for name, criteria, status, detail in rows:
        print(f"[{status}] {name} - {criteria} :: {detail}")
    print("\nFull report written to eval_results.md")


if __name__ == "__main__":
    run()
