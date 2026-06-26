from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Task:
    title: str
    type: str
    duration_minutes: int
    due_time: Optional[str] = None
    owner_preference: Optional[str] = None
    is_completed: bool = False
    priority: Optional[str] = None

    def check_off_completion(self) -> None:
        """Mark the task as completed."""
        self.is_completed = True

    def matches_owner_preference(self, owner: "Owner") -> bool:
        """Return whether this task matches the owner's preferences."""
        pass


@dataclass
class Pet:
    name: str
    animal_type: str
    preferred_time_of_day: Optional[str] = None
    medications: List[str] = field(default_factory=list)
    care_needs: List[Task] = field(default_factory=list)

    def do_task(self, task: Task) -> None:
        """Record that the pet performed a care task."""
        pass


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
        self.name = name
        self.age = age
        self.gender = gender
        self.location = location
        self.years_owned = years_owned
        self.pets: List[Pet] = pets or []
        self.tasks: List[Task] = tasks or []

    def owns_pets(self) -> bool:
        """Return True if the owner currently has any registered pets."""
        pass

    def complete_task(self, task: Task) -> None:
        """Mark a task as completed for the owner."""
        pass

    def has_availability(self) -> bool:
        """Determine whether the owner has available time to do tasks."""
        pass

    def set_task_priority(self, task: Task, priority: str) -> None:
        """Update the priority level for a task."""
        pass

    def edit_task(self, task: Task, **changes) -> None:
        """Edit task attributes such as duration, due time, or preference."""
        pass

    def add_task(self, task: Task) -> None:
        """Add a new task to the owner's task list."""
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the owner's task list."""
        pass

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet for the owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner's registered pets."""
        pass

    def generate_daily_plan(self) -> "Scheduler":
        """Create a daily schedule using the owner's tasks and pets."""
        pass


class Scheduler:
    def __init__(self, days_of_week: Optional[List[str]] = None) -> None:
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

    def create_daily_schedule(self, owner: Owner, pet: Pet) -> None:
        """Build a daily task schedule for the given owner and pet."""
        self.daily_tasks = {}
        sorted_tasks = sorted(
            owner.tasks,
            key=lambda task: (
                task.priority or "medium",
                task.due_time or "",
                task.duration_minutes,
            ),
            reverse=True,
        )

        day = self.days_of_week[0]
        self.daily_tasks[day] = sorted_tasks

    def explain_plan(self) -> str:
        """Return a text explanation for why the schedule was chosen."""
        pass

    def get_completed_tasks(self) -> List[Task]:
        """Return all tasks in the schedule that are completed."""
        pass

    def get_incomplete_tasks(self) -> List[Task]:
        """Return all tasks in the schedule that are not yet completed."""
        pass

    def track_task_duration(self, task: Task) -> int:
        """Return the total duration for the given task."""
        pass
