"""AI Care Assistant: a RAG + agentic layer on top of the PawPal+ scheduler.

Pipeline, each step logged to pawpal_agent.log:
  1. Retrieve species/breed/situation-specific care guidelines (care_knowledge.py).
  2. Ask Claude to draft candidate tasks grounded in that retrieved context,
     returned as schema-validated JSON (falls back to a deterministic,
     template-based draft if no API key is configured or the call fails).
  3. Validate every drafted task against hard constraints (duration bounds,
     allowed priority/frequency values) before it ever becomes a Task object.
  4. Agentically resolve scheduling conflicts against the pet's existing tasks
     by nudging due_time forward, reusing Scheduler's own conflict-detection
     logic so "no conflict" means the same thing everywhere in the app.

CareAgent.plan_care_tasks() is the single entry point the UI and CLI call.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from care_knowledge import CareGuideline, retrieve_guidelines
from pawpal_system import Owner, Pet, Scheduler, Task, parse_time_string

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    filename="pawpal_agent.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("pawpal_agent")

MODEL = "claude-opus-4-8"
MIN_DURATION_MINUTES = 1
MAX_DURATION_MINUTES = 240
ALLOWED_PRIORITIES = {"low", "medium", "high"}
ALLOWED_FREQUENCIES = {"daily", "weekly", "one-time"}

TASK_PROPOSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string"},
                    "duration_minutes": {"type": "integer"},
                    "due_time": {"type": "string"},
                    "frequency": {"type": "string", "enum": sorted(ALLOWED_FREQUENCIES)},
                    "priority": {"type": "string", "enum": sorted(ALLOWED_PRIORITIES)},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "title",
                    "type",
                    "duration_minutes",
                    "due_time",
                    "frequency",
                    "priority",
                    "rationale",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["tasks"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are a veterinary care planning assistant embedded in a pet care scheduler. "
    "Given a pet's profile and a set of retrieved care guidelines, propose specific, "
    "actionable daily/weekly care tasks. Ground every suggestion in the guidelines "
    "provided — do not invent medical advice beyond them. Keep durations realistic "
    "(a few minutes to an hour) and due times in the format '7:30 AM'."
)


@dataclass
class AgentResult:
    tasks: List[Task] = field(default_factory=list)
    explanation: str = ""
    sources: List[str] = field(default_factory=list)
    used_llm: bool = False
    warnings: List[str] = field(default_factory=list)


def _format_time(value: datetime) -> str:
    return value.strftime("%I:%M %p").lstrip("0")


def _build_prompt(pet: Pet, owner: Owner, guidelines: List[CareGuideline], max_tasks: int) -> str:
    guideline_text = "\n\n".join(
        f"[{g.doc_id}] {g.title}\n{g.text}" for g in guidelines
    ) or "(no specific guidelines matched this pet's profile)"

    return (
        f"Pet: {pet.name}, species={pet.animal_type}, breed={pet.breed or 'unknown'}, "
        f"preferred_time_of_day={pet.preferred_time_of_day or 'any'}, "
        f"medications={', '.join(pet.medications) or 'none'}.\n"
        f"Owner: {owner.name}, location={owner.location or 'unknown'}.\n\n"
        f"Retrieved care guidelines:\n{guideline_text}\n\n"
        f"Propose at most {max_tasks} care tasks for this pet, each grounded in the "
        f"guidelines above."
    )


def _fallback_tasks(guidelines: List[CareGuideline], max_tasks: int) -> List[dict]:
    """Deterministic, template-based drafts used when the LLM is unavailable."""
    drafts = []
    for guideline in guidelines[:max_tasks]:
        template = dict(guideline.suggested_task)
        if not template:
            continue
        template.setdefault("rationale", guideline.title)
        drafts.append(template)
    return drafts


def _validate_draft(draft: dict) -> Optional[dict]:
    """Return a cleaned draft dict, or None (with a logged reason) if invalid."""
    title = str(draft.get("title") or "").strip()
    task_type = str(draft.get("type") or "").strip()
    if not title or not task_type:
        logger.warning("Rejected task draft: missing title/type (%r)", draft)
        return None

    try:
        duration = int(draft.get("duration_minutes"))
    except (TypeError, ValueError):
        logger.warning("Rejected task draft %r: non-integer duration_minutes", title)
        return None
    if not (MIN_DURATION_MINUTES <= duration <= MAX_DURATION_MINUTES):
        logger.warning("Rejected task draft %r: duration_minutes %s out of bounds", title, duration)
        return None

    priority = str(draft.get("priority") or "medium").lower()
    if priority not in ALLOWED_PRIORITIES:
        logger.warning("Task draft %r: unknown priority %r, defaulting to medium", title, priority)
        priority = "medium"

    frequency = str(draft.get("frequency") or "daily").lower()
    if frequency not in ALLOWED_FREQUENCIES:
        logger.warning("Task draft %r: unknown frequency %r, defaulting to daily", title, frequency)
        frequency = "daily"

    due_time = draft.get("due_time") or None
    if due_time and parse_time_string(due_time) is None:
        logger.warning("Task draft %r: unparseable due_time %r, dropping it", title, due_time)
        due_time = None

    return {
        "title": title,
        "type": task_type,
        "duration_minutes": duration,
        "due_time": due_time,
        "frequency": frequency,
        "priority": priority,
    }


def _resolve_conflicts(candidate: Task, existing_tasks: List[Task], warnings: List[str]) -> None:
    """Nudge candidate.due_time forward in 30-minute steps until it no longer
    overlaps any existing task, reusing Scheduler's own overlap check so a
    task the agent adds can't create the exact conflicts the scheduler warns
    about. Gives up after 3 hours of nudging and just logs a warning.
    """
    if candidate.get_due_time() is None:
        return

    others = [t for t in existing_tasks if t.get_due_time() is not None and not t.is_completed]
    max_attempts = 6
    for _ in range(max_attempts):
        if not any(Scheduler._windows_overlap(candidate, other) for other in others):
            return
        current = datetime.combine(datetime.min, candidate.get_due_time())
        candidate.due_time = _format_time(current + timedelta(minutes=30))

    message = f"Could not fully resolve a scheduling conflict for '{candidate.title}'."
    logger.warning(message)
    warnings.append(message)


class CareAgent:
    def __init__(self, api_key: Optional[str] = None, model: str = MODEL) -> None:
        self.model = model
        self.client = None
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        except Exception as error:  # noqa: BLE001 - any import/construction failure disables the LLM path
            logger.info("Anthropic client unavailable, will use offline fallback: %s", error)
            self.client = None

    def _call_llm(self, prompt: str) -> Optional[List[dict]]:
        if self.client is None:
            return None
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                output_config={"format": {"type": "json_schema", "schema": TASK_PROPOSAL_SCHEMA}, "effort": "low"},
                messages=[{"role": "user", "content": prompt}],
            )
            if response.stop_reason == "refusal":
                logger.warning("LLM refused the care-task request; using offline fallback.")
                return None
            text = next(block.text for block in response.content if block.type == "text")
            data = json.loads(text)
            logger.info("LLM proposed %d candidate task(s).", len(data.get("tasks", [])))
            return data.get("tasks", [])
        except Exception as error:  # noqa: BLE001 - any API/parse failure falls back to offline drafts
            logger.warning("LLM call failed (%s); using offline fallback.", error)
            return None

    def plan_care_tasks(
        self,
        pet: Pet,
        owner: Owner,
        existing_tasks: Optional[List[Task]] = None,
        max_tasks: int = 3,
        query: Optional[str] = None,
    ) -> AgentResult:
        existing_tasks = existing_tasks or []
        warnings: List[str] = []

        guidelines = retrieve_guidelines(pet, query=query)
        logger.info(
            "Retrieved %d guideline(s) for %s: %s",
            len(guidelines),
            pet.name,
            [g.doc_id for g in guidelines],
        )

        prompt = _build_prompt(pet, owner, guidelines, max_tasks)
        raw_drafts = self._call_llm(prompt)
        used_llm = raw_drafts is not None
        if raw_drafts is None:
            raw_drafts = _fallback_tasks(guidelines, max_tasks)

        tasks: List[Task] = []
        for draft in raw_drafts[:max_tasks]:
            cleaned = _validate_draft(draft)
            if cleaned is None:
                continue
            candidate = Task(
                title=cleaned["title"],
                type=cleaned["type"],
                duration_minutes=cleaned["duration_minutes"],
                due_time=cleaned["due_time"],
                frequency=cleaned["frequency"],
                priority=cleaned["priority"],
                owner_preference=pet.preferred_time_of_day,
            )
            _resolve_conflicts(candidate, existing_tasks + tasks, warnings)
            tasks.append(candidate)

        sources = [f"{g.title} ({g.doc_id})" for g in guidelines]
        if used_llm:
            explanation = (
                f"Claude drafted {len(tasks)} task(s) for {pet.name} grounded in "
                f"{len(guidelines)} retrieved guideline(s): {', '.join(g.doc_id for g in guidelines) or 'none'}."
            )
        else:
            explanation = (
                f"Used offline template fallback (no LLM available) to draft {len(tasks)} "
                f"task(s) for {pet.name} from {len(guidelines)} retrieved guideline(s)."
            )
        logger.info(explanation)

        return AgentResult(
            tasks=tasks,
            explanation=explanation,
            sources=sources,
            used_llm=used_llm,
            warnings=warnings,
        )
