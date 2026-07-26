from datetime import date

from ai_agent import CareAgent, _resolve_conflicts, _validate_draft
from care_knowledge import retrieve_guidelines
from pawpal_system import Owner, Pet, Task


def _owner():
    return Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2)


# --- Retrieval -------------------------------------------------------------


def test_retrieve_guidelines_prioritizes_dog_topics_for_a_dog():
    dog = Pet(name="Rex", animal_type="dog", breed="Golden Retriever")

    results = retrieve_guidelines(dog, top_k=5)

    assert results, "expected at least one matching guideline"
    assert all(doc.doc_id.startswith("dog-") or "dog" in doc.keywords for doc in results)


def test_retrieve_guidelines_matches_cat_topics_for_a_cat():
    cat = Pet(name="Whiskers", animal_type="cat")

    results = retrieve_guidelines(cat, top_k=5)

    doc_ids = {doc.doc_id for doc in results}
    assert "cat-litter" in doc_ids or "cat-feeding" in doc_ids


def test_retrieve_guidelines_surfaces_medication_doc_when_pet_has_meds():
    dog = Pet(name="Rex", animal_type="dog", medications=["heartworm pill"])

    results = retrieve_guidelines(dog, top_k=5)

    assert any(doc.doc_id == "medication" for doc in results)


def test_retrieve_guidelines_returns_empty_for_blank_profile():
    pet = Pet(name="Ghost", animal_type="")

    assert retrieve_guidelines(pet) == []


# --- Draft validation --------------------------------------------------------


def test_validate_draft_accepts_well_formed_draft():
    draft = {
        "title": "Walk",
        "type": "exercise",
        "duration_minutes": 30,
        "due_time": "8:00 AM",
        "frequency": "daily",
        "priority": "high",
        "rationale": "Dogs need daily exercise.",
    }

    cleaned = _validate_draft(draft)

    assert cleaned["title"] == "Walk"
    assert cleaned["duration_minutes"] == 30
    assert cleaned["priority"] == "high"


def test_validate_draft_rejects_missing_title():
    draft = {"type": "exercise", "duration_minutes": 30, "priority": "high"}

    assert _validate_draft(draft) is None


def test_validate_draft_rejects_out_of_bounds_duration():
    draft = {"title": "Walk", "type": "exercise", "duration_minutes": 10000, "priority": "high"}

    assert _validate_draft(draft) is None


def test_validate_draft_defaults_unknown_priority_to_medium():
    draft = {"title": "Walk", "type": "exercise", "duration_minutes": 10, "priority": "urgent!!"}

    cleaned = _validate_draft(draft)

    assert cleaned["priority"] == "medium"


def test_validate_draft_drops_unparseable_due_time():
    draft = {
        "title": "Walk",
        "type": "exercise",
        "duration_minutes": 10,
        "priority": "medium",
        "due_time": "not a time",
    }

    cleaned = _validate_draft(draft)

    assert cleaned["due_time"] is None


# --- Conflict resolution -----------------------------------------------------


def test_resolve_conflicts_nudges_candidate_away_from_existing_task():
    existing = Task(title="Feed", type="feeding", duration_minutes=15, due_time="8:00 AM")
    candidate = Task(title="Walk", type="exercise", duration_minutes=30, due_time="8:00 AM")
    warnings = []

    _resolve_conflicts(candidate, [existing], warnings)

    assert candidate.due_time != "8:00 AM"
    assert warnings == []


def test_resolve_conflicts_leaves_non_conflicting_task_untouched():
    existing = Task(title="Feed", type="feeding", duration_minutes=15, due_time="8:00 AM")
    candidate = Task(title="Walk", type="exercise", duration_minutes=30, due_time="6:00 PM")
    warnings = []

    _resolve_conflicts(candidate, [existing], warnings)

    assert candidate.due_time == "6:00 PM"


# --- End-to-end fallback path (no live API call) -----------------------------


def test_plan_care_tasks_offline_fallback_produces_valid_tasks():
    dog = Pet(name="Rex", animal_type="dog", breed="Golden Retriever", preferred_time_of_day="morning")
    owner = _owner()

    agent = CareAgent()
    agent.client = None  # force the offline fallback path regardless of environment

    result = agent.plan_care_tasks(pet=dog, owner=owner, existing_tasks=[], max_tasks=3)

    assert result.used_llm is False
    assert result.tasks, "fallback should still produce at least one task"
    for task in result.tasks:
        assert 1 <= task.duration_minutes <= 240
        assert task.priority in {"low", "medium", "high"}
        assert task.frequency in {"daily", "weekly", "one-time"}


def test_plan_care_tasks_avoids_conflicts_with_existing_schedule():
    dog = Pet(name="Rex", animal_type="dog", breed="Golden Retriever")
    owner = _owner()
    existing = Task(title="Walk", type="exercise", duration_minutes=30, due_time="8:00 AM")

    agent = CareAgent()
    agent.client = None

    result = agent.plan_care_tasks(pet=dog, owner=owner, existing_tasks=[existing], max_tasks=3)

    conflicting = [t for t in result.tasks if t.due_time == "8:00 AM"]
    assert conflicting == []
