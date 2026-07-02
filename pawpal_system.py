from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
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
    due_date: Optional[date] = None
    frequency: str = "daily"
    owner_preference: Optional[str] = None
    is_completed: bool = False
    priority: Optional[str] = None
    pet: Optional["Pet"] = field(default=None, compare=False, repr=False)
    owner: Optional["Owner"] = field(default=None, compare=False, repr=False)

    def mark_complete(self) -> Optional["Task"]:
        """Mark the task completed and roll a daily/weekly task forward.

        Sets is_completed, then calls next_occurrence() to build the next
        instance. If one is produced, it's registered with whichever of
        pet/owner currently holds this task, so it shows up in future
        schedules without any extra wiring from the caller.

        Returns:
            The newly spawned Task, or None if this task doesn't recur
            (frequency isn't "daily"/"weekly").
        """
        self.is_completed = True

        next_task = self.next_occurrence()
        registrar = self.pet or self.owner
        if next_task is not None and registrar is not None:
            registrar.add_task(next_task)
        return next_task

    def next_occurrence(self) -> Optional["Task"]:
        """Build the next instance of a recurring task, advancing due_date.

        Daily tasks advance by timedelta(days=1); weekly tasks advance by
        timedelta(weeks=1) from due_date (or from today if due_date was
        never set). Every other field is copied as-is onto the clone, and
        is_completed resets to False since it's a fresh occurrence.

        Returns:
            A new Task with due_date shifted forward, or None if frequency
            is anything other than "daily"/"weekly" (i.e. not recurring).
        """
        frequency = (self.frequency or "").strip().lower()
        if frequency == "daily":
            delta = timedelta(days=1)
        elif frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None

        next_due_date = (self.due_date or date.today()) + delta

        return Task(
            title=self.title,
            type=self.type,
            duration_minutes=self.duration_minutes,
            due_time=self.due_time,
            due_date=next_due_date,
            frequency=self.frequency,
            owner_preference=self.owner_preference,
            priority=self.priority,
        )

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
        task.owner = None
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
        else:
            task.pet = None
            task.owner = self
            if task not in self.tasks:
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
        if "," in frequency:
            names = {part.strip() for part in frequency.split(",")}
            return [day for day in self.days_of_week if day.lower() in names]
        for day in self.days_of_week:
            if day.lower() == frequency:
                return [day]
        return list(self.days_of_week)

    def sort_by_time(self, day: str) -> List[Task]:
        """Sort a day's tasks in place by due time only, ignoring priority.

        Uses task.get_due_time() (a parsed time object, not the raw string)
        as the sort key so times compare correctly regardless of the
        original text format ("8am" vs "8:00 AM" vs "08:00"). Tasks with no
        parseable due time sort last via the time.max fallback.

        Args:
            day: A key into self.daily_tasks, e.g. "Monday".

        Returns:
            The same list object, now sorted (mutated in place).
        """
        day_tasks = self.daily_tasks.get(day, [])
        day_tasks.sort(key=lambda task: task.get_due_time() or time.max)
        return day_tasks

    def tasks_due_on(self, target_date: date) -> List[Task]:
        """Return every unique scheduled task whose actual due_date is target_date.

        The weekday-template buckets in daily_tasks repeat by frequency, not by
        calendar date, so this checks each task's own due_date directly.

        Args:
            target_date: The calendar date to match against each task's due_date.

        Returns:
            Matching tasks, deduplicated by identity (a task can appear in
            multiple weekday buckets but should only be reported once).
        """
        seen_ids = set()
        due: List[Task] = []
        for day_tasks in self.daily_tasks.values():
            for task in day_tasks:
                if task.due_date == target_date and id(task) not in seen_ids:
                    seen_ids.add(id(task))
                    due.append(task)
        return due

    def filter_tasks(
        self,
        day: Optional[str] = None,
        pet: Optional[Pet] = None,
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Task]:
        """Return tasks narrowed by day, pet/pet name, and/or completion status.

        Filters are applied cumulatively (AND, not OR) in this order: day,
        then pet, then pet_name, then status. Any filter left as None is
        skipped entirely.

        Args:
            day: Restrict to this weekday's bucket; omit to search every day
                (deduplicated by identity, since a recurring task can appear
                in more than one weekday bucket).
            pet: Restrict to tasks belonging to this exact Pet instance.
            pet_name: Restrict to tasks whose pet's name matches, case-insensitive.
            status: "completed" or "pending"; omit for either.

        Returns:
            The filtered list of tasks.
        """
        if day is not None:
            tasks: List[Task] = list(self.daily_tasks.get(day, []))
        else:
            seen_ids = set()
            tasks = []
            for day_tasks in self.daily_tasks.values():
                for task in day_tasks:
                    if id(task) not in seen_ids:
                        seen_ids.add(id(task))
                        tasks.append(task)

        if pet is not None:
            tasks = [task for task in tasks if task.pet is pet]
        if pet_name is not None:
            tasks = [
                task
                for task in tasks
                if task.pet is not None and task.pet.name.lower() == pet_name.lower()
            ]
        if status == "completed":
            tasks = [task for task in tasks if task.is_completed]
        elif status == "pending":
            tasks = [task for task in tasks if not task.is_completed]

        return tasks

    def get_conflicts(self, day: Optional[str] = None) -> List[Tuple[Task, Task]]:
        """Return pairs of tasks on a day whose time windows overlap.

        Overlaps are flagged whether the tasks belong to the same pet (the pet
        can't be fed and walked at once) or to different pets (the owner can't
        be in two places at once), since either way one person/pet can't do both.
        Completed tasks and tasks with no parseable due_time are excluded before
        comparing, since neither can meaningfully conflict.

        This is an O(n^2) pairwise scan of each day's tasks — fine for a
        handful of daily tasks, but not built to scale to large task counts.

        Args:
            day: Check only this weekday; omit to check every day.

        Returns:
            (task_a, task_b) pairs whose due-time windows overlap.
        """
        days = [day] if day else self.days_of_week
        conflicts: List[Tuple[Task, Task]] = []
        for scheduled_day in days:
            day_tasks = [
                task
                for task in self.daily_tasks.get(scheduled_day, [])
                if task.get_due_time() is not None and not task.is_completed
            ]
            for i, task_a in enumerate(day_tasks):
                for task_b in day_tasks[i + 1 :]:
                    if self._windows_overlap(task_a, task_b):
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

    def get_conflict_warnings(self, day: Optional[str] = None) -> List[str]:
        """Return human-readable warning strings for overlapping tasks.

        Lightweight by design: any unexpected error during detection (e.g. a
        malformed time) is caught and turned into a single warning string
        instead of propagating and crashing the program.

        Args:
            day: Check only this weekday; omit to check every day.

        Returns:
            One formatted warning string per conflicting pair from
            get_conflicts(), e.g. "Warning: 'Walk Rex' (9:30 AM) overlaps
            with 'Brush Rex' (9:30 AM) - both scheduled for Rex.". Empty
            list if there are no conflicts.
        """
        try:
            conflicts = self.get_conflicts(day)
        except Exception as error:  # noqa: BLE001 - intentionally broad, non-crashing fallback
            return [f"Warning: could not check for scheduling conflicts ({error})."]

        warnings: List[str] = []
        for task_a, task_b in conflicts:
            same_pet = task_a.pet is not None and task_a.pet is task_b.pet
            who = task_a.pet.name if same_pet and task_a.pet else "the owner"
            reason = (
                f"both scheduled for {who}"
                if same_pet
                else "the owner can't be in two places at once"
            )
            warnings.append(
                f"Warning: '{task_a.title}' ({task_a.due_time}) overlaps with "
                f"'{task_b.title}' ({task_b.due_time}) - {reason}."
            )
        return warnings

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

        warnings = self.get_conflict_warnings()
        if warnings:
            lines.append(f"Warning: {len(warnings)} scheduling conflict(s) detected.")

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
