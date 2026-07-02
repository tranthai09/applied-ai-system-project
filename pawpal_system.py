from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

_TIME_FORMATS = ("%H:%M", "%I:%M%p", "%I:%M %p", "%I%p", "%I %p")


def parse_time_string(value: Optional[str]) -> Optional[time]:
    """Parse flexible time text ('8am', '8:30 AM', '17:00') into a time object."""
    if not value:
        return None
    cleaned = value.strip().upper().replace(".", "")
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).time()
        except ValueError:
            continue
    return None


@dataclass
class Task:
    title: str
    type: str
    duration_minutes: int
    due_time: Optional[str] = None
    frequency: str = "daily"
    owner_preference: Optional[str] = None
    is_completed: bool = False
    priority: Optional[str] = None
    pet: Optional["Pet"] = field(default=None, compare=False, repr=False)

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.is_completed = True

    def get_due_time(self) -> Optional[time]:
        """Return due_time parsed into a comparable time object, or None if unset/unparseable."""
        return parse_time_string(self.due_time)

    def matches_owner_preference(self, owner: "Owner") -> bool:
        """Return whether this task matches the owner's preferences."""
        if not self.owner_preference:
            return True

        preference = self.owner_preference.lower()

        if self.pet is not None:
            if self.pet.preferred_time_of_day is None:
                return False
            return preference == self.pet.preferred_time_of_day.lower()

        owner_context = f"{owner.name} {owner.location} {owner.gender}".lower()
        general_preferences = {"any", "morning", "afternoon", "evening", "daily", "regular"}

        return preference in general_preferences or preference in owner_context


@dataclass
class Pet:
    name: str
    animal_type: str
    breed: Optional[str] = None
    preferred_time_of_day: Optional[str] = None
    medications: List[str] = field(default_factory=list)
    care_needs: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Register a task as belonging to this pet's care needs."""
        task.pet = self
        if task not in self.care_needs:
            self.care_needs.append(task)

    def do_task(self, task: Task) -> None:
        """Record that the pet performed a care task."""
        if task in self.care_needs:
            task.mark_complete()


class Owner:
    def __init__(
        self,
        name: str,
        age: int,
        gender: str,
        location: str,
        years_owned: int,
        pets: Optional[List[Pet]] = None,
        tasks: Optional[List[Task]] = None,
    ) -> None:
        """Initialize an owner with their profile info, pets, and tasks."""
        self.name = name
        self.age = age
        self.gender = gender
        self.location = location
        self.years_owned = years_owned
        self.pets: List[Pet] = pets or []
        self.tasks: List[Task] = tasks or []

    def owns_pets(self) -> bool:
        """Return True if the owner currently has any registered pets."""
        return bool(self.pets)

    def get_all_tasks(self) -> List[Task]:
        """Return every task owned directly or via any registered pet, deduplicated."""
        all_tasks: List[Task] = list(self.tasks)
        for pet in self.pets:
            for task in pet.care_needs:
                if task not in all_tasks:
                    all_tasks.append(task)
        return all_tasks

    def complete_task(self, task: Task) -> None:
        """Mark a task as completed for the owner."""
        task.mark_complete()

    def has_availability(self) -> bool:
        """Determine whether the owner has available time to do tasks."""
        return any(not task.is_completed for task in self.get_all_tasks())

    def set_task_priority(self, task: Task, priority: str) -> None:
        """Update the priority level for a task."""
        task.priority = priority

    def edit_task(self, task: Task, **changes) -> None:
        """Edit task attributes such as duration, due time, or preference."""
        for key, value in changes.items():
            if hasattr(task, key):
                setattr(task, key, value)

    def add_task(self, task: Task, pet: Optional[Pet] = None) -> None:
        """Add a task, assigning it to a pet's care needs or to the owner directly."""
        if pet is not None:
            pet.add_task(task)
        elif task not in self.tasks:
            task.pet = None
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from wherever it is currently owned."""
        if task.pet is not None:
            if task in task.pet.care_needs:
                task.pet.care_needs.remove(task)
            task.pet = None
        elif task in self.tasks:
            self.tasks.remove(task)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet for the owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner's registered pets."""
        if pet in self.pets:
            self.pets.remove(pet)

    def generate_daily_plan(self) -> "Scheduler":
        """Create a daily schedule using the owner's tasks and pets."""
        scheduler = Scheduler()
        scheduler.create_daily_schedule(self)
        return scheduler


class Scheduler:
    def __init__(self, days_of_week: Optional[List[str]] = None) -> None:
        """Initialize a scheduler with the given days of week and an empty schedule."""
        self.days_of_week: List[str] = days_of_week or [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        self.daily_tasks: Dict[str, List[Task]] = {}

    def create_daily_schedule(self, owner: Owner, pet: Optional[Pet] = None) -> None:
        """Build a week's worth of task schedules, repeating tasks by their frequency."""
        self.daily_tasks = {day: [] for day in self.days_of_week}

        tasks = pet.care_needs if pet is not None else owner.get_all_tasks()

        for task in tasks:
            for day in self._days_for_task(task):
                self.daily_tasks[day].append(task)

        priority_rank = {"high": 3, "medium": 2, "low": 1}
        for day_tasks in self.daily_tasks.values():
            day_tasks.sort(
                key=lambda task: (
                    -priority_rank.get((task.priority or "medium").lower(), 2),
                    task.get_due_time() or time.max,
                    task.duration_minutes,
                )
            )

    def _days_for_task(self, task: Task) -> List[str]:
        """Return which scheduled days a task's frequency maps to."""
        frequency = (task.frequency or "daily").strip().lower()
        if frequency == "weekly":
            return [self.days_of_week[0]]
        for day in self.days_of_week:
            if day.lower() == frequency:
                return [day]
        return list(self.days_of_week)

    def get_conflicts(self, day: Optional[str] = None) -> List[Tuple[Task, Task]]:
        """Return pairs of same-pet tasks on a day whose time windows overlap."""
        days = [day] if day else self.days_of_week
        conflicts: List[Tuple[Task, Task]] = []
        for scheduled_day in days:
            day_tasks = [
                task
                for task in self.daily_tasks.get(scheduled_day, [])
                if task.get_due_time() is not None
            ]
            for i, task_a in enumerate(day_tasks):
                for task_b in day_tasks[i + 1 :]:
                    if task_a.pet is task_b.pet and self._windows_overlap(task_a, task_b):
                        conflicts.append((task_a, task_b))
        return conflicts

    @staticmethod
    def _windows_overlap(task_a: Task, task_b: Task) -> bool:
        """Return whether two tasks' due-time windows overlap."""
        start_a = datetime.combine(datetime.min, task_a.get_due_time())
        end_a = start_a + timedelta(minutes=task_a.duration_minutes)
        start_b = datetime.combine(datetime.min, task_b.get_due_time())
        end_b = start_b + timedelta(minutes=task_b.duration_minutes)
        return start_a < end_b and start_b < end_a

    def explain_plan(self) -> str:
        """Return a text explanation for why the schedule was chosen."""
        if not any(self.daily_tasks.values()):
            return "No schedule has been created yet."

        lines = ["Tasks are sorted by priority, then due time, then duration."]
        for day in self.days_of_week:
            day_tasks = self.daily_tasks.get(day, [])
            if not day_tasks:
                continue
            completed = sum(1 for task in day_tasks if task.is_completed)
            lines.append(
                f"{day}: {len(day_tasks)} task(s), {completed} completed, "
                f"{len(day_tasks) - completed} pending."
            )

        conflicts = self.get_conflicts()
        if conflicts:
            lines.append(
                f"Warning: {len(conflicts)} scheduling conflict(s) between overlapping "
                "tasks for the same pet."
            )

        return "\n".join(lines)

    def get_completed_tasks(self) -> List[Task]:
        """Return all unique tasks in the schedule that are completed."""
        seen_ids = set()
        completed: List[Task] = []
        for tasks in self.daily_tasks.values():
            for task in tasks:
                if task.is_completed and id(task) not in seen_ids:
                    seen_ids.add(id(task))
                    completed.append(task)
        return completed

    def get_incomplete_tasks(self) -> List[Task]:
        """Return all unique tasks in the schedule that are not yet completed."""
        seen_ids = set()
        incomplete: List[Task] = []
        for tasks in self.daily_tasks.values():
            for task in tasks:
                if not task.is_completed and id(task) not in seen_ids:
                    seen_ids.add(id(task))
                    incomplete.append(task)
        return incomplete

    def track_task_duration(self, task: Task) -> int:
        """Return the total scheduled minutes for a task across every day it appears."""
        occurrences = sum(
            1 for tasks in self.daily_tasks.values() for scheduled in tasks if scheduled is task
        )
        return task.duration_minutes * occurrences
