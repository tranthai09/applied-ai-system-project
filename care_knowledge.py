"""Local retrieval knowledge base of pet care guidelines.

This is the "retrieval" half of the AI Care Assistant's RAG pipeline: a small
set of species/breed/situation-specific care documents, plus a keyword-overlap
retriever that scores documents against a pet's profile (and an optional free
text query). The retrieved documents are handed to CareAgent (ai_agent.py),
which uses them as grounding context for the LLM prompt and as the source of
truth for the deterministic fallback path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class CareGuideline:
    doc_id: str
    keywords: Sequence[str]
    title: str
    text: str
    suggested_task: dict = field(default_factory=dict)


CARE_GUIDELINES: List[CareGuideline] = [
    CareGuideline(
        doc_id="dog-exercise",
        keywords=("dog", "exercise", "walk", "energy"),
        title="Daily exercise for dogs",
        text=(
            "Most dogs need at least one 20-30 minute walk or active play session "
            "daily to manage energy and weight. High-energy breeds (retrievers, "
            "shepherds, terriers) often benefit from a second shorter walk."
        ),
        suggested_task={
            "title": "Walk",
            "type": "exercise",
            "duration_minutes": 30,
            "due_time": "8:00 AM",
            "frequency": "daily",
            "priority": "high",
        },
    ),
    CareGuideline(
        doc_id="dog-feeding",
        keywords=("dog", "feeding", "food", "meal"),
        title="Feeding schedule for dogs",
        text=(
            "Adult dogs typically do well on two measured meals a day, spaced "
            "roughly 8-12 hours apart, at consistent times to support digestion "
            "and housetraining."
        ),
        suggested_task={
            "title": "Feed",
            "type": "feeding",
            "duration_minutes": 10,
            "due_time": "7:00 AM",
            "frequency": "daily",
            "priority": "high",
        },
    ),
    CareGuideline(
        doc_id="dog-grooming",
        keywords=("dog", "grooming", "brush", "coat"),
        title="Grooming for dogs",
        text=(
            "Weekly brushing keeps a dog's coat healthy and reduces shedding; "
            "longer-haired breeds may need brushing several times a week."
        ),
        suggested_task={
            "title": "Brush coat",
            "type": "grooming",
            "duration_minutes": 15,
            "due_time": "6:00 PM",
            "frequency": "weekly",
            "priority": "low",
        },
    ),
    CareGuideline(
        doc_id="cat-litter",
        keywords=("cat", "litter", "cleaning", "box"),
        title="Litter box maintenance for cats",
        text=(
            "Litter boxes should be scooped at least once daily; cats are "
            "sensitive to a dirty box and may avoid it if it isn't kept clean."
        ),
        suggested_task={
            "title": "Clean litter box",
            "type": "cleaning",
            "duration_minutes": 10,
            "due_time": "8:00 AM",
            "frequency": "daily",
            "priority": "medium",
        },
    ),
    CareGuideline(
        doc_id="cat-feeding",
        keywords=("cat", "feeding", "food", "meal"),
        title="Feeding schedule for cats",
        text=(
            "Adult cats generally do best on two scheduled meals a day rather "
            "than free-feeding, which helps with weight management and lets an "
            "owner notice appetite changes early."
        ),
        suggested_task={
            "title": "Feed",
            "type": "feeding",
            "duration_minutes": 5,
            "due_time": "7:00 AM",
            "frequency": "daily",
            "priority": "high",
        },
    ),
    CareGuideline(
        doc_id="cat-enrichment",
        keywords=("cat", "enrichment", "play", "indoor"),
        title="Enrichment for indoor cats",
        text=(
            "Indoor cats benefit from at least one daily active play session "
            "(e.g. a wand toy) to prevent boredom and destructive behavior."
        ),
        suggested_task={
            "title": "Play session",
            "type": "enrichment",
            "duration_minutes": 15,
            "due_time": "5:00 PM",
            "frequency": "daily",
            "priority": "medium",
        },
    ),
    CareGuideline(
        doc_id="medication",
        keywords=("medication", "meds", "medicine", "pill"),
        title="Administering medication",
        text=(
            "Medications are most effective when given at the same time every "
            "day; pair the dose with feeding time to build a consistent habit "
            "and reduce the chance of a missed dose."
        ),
        suggested_task={
            "title": "Give medication",
            "type": "medication",
            "duration_minutes": 5,
            "due_time": "7:00 AM",
            "frequency": "daily",
            "priority": "high",
        },
    ),
    CareGuideline(
        doc_id="senior-pet",
        keywords=("senior", "old", "aging", "arthritis"),
        title="Care adjustments for senior pets",
        text=(
            "Senior pets often need shorter, gentler exercise sessions and more "
            "frequent but lighter meals; watch for mobility changes that may "
            "signal joint pain."
        ),
        suggested_task={
            "title": "Gentle walk",
            "type": "exercise",
            "duration_minutes": 15,
            "due_time": "9:00 AM",
            "frequency": "daily",
            "priority": "medium",
        },
    ),
    CareGuideline(
        doc_id="puppy-kitten",
        keywords=("puppy", "kitten", "young", "training"),
        title="Care for puppies and kittens",
        text=(
            "Young animals need more frequent, smaller meals (3-4 times daily) "
            "and short training/socialization sessions rather than one long one."
        ),
        suggested_task={
            "title": "Training session",
            "type": "enrichment",
            "duration_minutes": 10,
            "due_time": "4:00 PM",
            "frequency": "daily",
            "priority": "medium",
        },
    ),
    CareGuideline(
        doc_id="other-pet-general",
        keywords=("other", "small", "general", "habitat"),
        title="General care for small/other pets",
        text=(
            "For pets outside cats/dogs (birds, rabbits, reptiles, etc.), daily "
            "habitat checks (food, water, temperature/cleanliness) are the most "
            "commonly missed care task."
        ),
        suggested_task={
            "title": "Habitat check",
            "type": "cleaning",
            "duration_minutes": 10,
            "due_time": "8:00 AM",
            "frequency": "daily",
            "priority": "medium",
        },
    ),
]


def _pet_query_terms(pet, query: Optional[str] = None) -> List[str]:
    """Build the bag of keyword terms describing a pet (plus any free-text query)."""
    terms: List[str] = [pet.animal_type or ""]
    if pet.breed:
        terms.append(pet.breed)
    if pet.preferred_time_of_day:
        terms.append(pet.preferred_time_of_day)
    if pet.medications:
        terms.append("medication")
        terms.extend(pet.medications)
    if query:
        terms.append(query)
    return [term.lower() for term in " ".join(terms).split()]


def retrieve_guidelines(pet, query: Optional[str] = None, top_k: int = 3) -> List[CareGuideline]:
    """Retrieve the top_k care guidelines most relevant to a pet's profile.

    Scores each guideline by how many of its keywords exactly match one of the
    pet's profile terms (animal_type, breed words, preferred_time_of_day,
    medications) plus any free-text query, so e.g. "Golden Retriever" matches
    the "dog" guidelines (via animal_type) and a medication name matches the
    medication guideline. Matching is whole-word rather than substring so a
    word like "golden" can't accidentally match a keyword like "old". Ties
    break by doc_id for deterministic ordering (important for reproducible
    fallback behavior when no LLM is available).
    """
    terms = set(_pet_query_terms(pet, query))
    if not terms:
        return []

    scored = []
    for guideline in CARE_GUIDELINES:
        score = sum(1 for keyword in guideline.keywords if keyword in terms)
        if score > 0:
            scored.append((score, guideline))

    scored.sort(key=lambda pair: (-pair[0], pair[1].doc_id))
    return [guideline for _, guideline in scored[:top_k]]
