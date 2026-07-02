from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_marks_task_complete():
    task = Task(title="Feed", type="feeding", duration_minutes=10)
    assert task.is_completed is False

    task.mark_complete()

    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Rex", animal_type="dog")
    assert len(pet.care_needs) == 0

    task = Task(title="Walk", type="exercise", duration_minutes=20)
    pet.add_task(task)

    assert len(pet.care_needs) == 1


# --- Sorting correctness -----------------------------------------------


def test_sort_by_time_returns_chronological_order():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Dinner", type="feeding", duration_minutes=15, due_time="6pm"))
    pet.add_task(Task(title="Breakfast", type="feeding", duration_minutes=15, due_time="8am"))
    pet.add_task(Task(title="Lunch", type="feeding", duration_minutes=15, due_time="12:00 PM"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    ordered = scheduler.sort_by_time("Monday")

    assert [task.title for task in ordered] == ["Breakfast", "Lunch", "Dinner"]


def test_sort_by_time_handles_mixed_formats_and_missing_time():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="No time", type="misc", duration_minutes=5, due_time=None))
    pet.add_task(Task(title="Morning", type="misc", duration_minutes=5, due_time="7:30 AM"))
    pet.add_task(Task(title="Noon", type="misc", duration_minutes=5, due_time="12pm"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    ordered = scheduler.sort_by_time("Monday")

    # Tasks without a parseable due_time sort last.
    assert [task.title for task in ordered] == ["Morning", "Noon", "No time"]


def test_daily_schedule_sorts_by_priority_before_time():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Early low", type="misc", duration_minutes=5, due_time="6am", priority="low"))
    pet.add_task(Task(title="Late high", type="misc", duration_minutes=5, due_time="9pm", priority="high"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    ordered = scheduler.daily_tasks["Monday"]

    # High priority should be scheduled first even though it's later in the day.
    assert [task.title for task in ordered] == ["Late high", "Early low"]


# --- Recurrence logic -----------------------------------------------------


def test_mark_complete_on_daily_task_creates_next_day_task():
    pet = Pet(name="Rex", animal_type="dog")
    today = date(2026, 7, 1)
    task = Task(
        title="Walk",
        type="exercise",
        duration_minutes=20,
        frequency="daily",
        due_date=today,
    )
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.is_completed is False
    assert next_task.title == task.title
    # The new occurrence should be auto-registered with the same pet.
    assert next_task in pet.care_needs


def test_mark_complete_on_weekly_task_advances_by_one_week():
    pet = Pet(name="Rex", animal_type="dog")
    today = date(2026, 7, 1)
    task = Task(
        title="Groom",
        type="grooming",
        duration_minutes=30,
        frequency="weekly",
        due_date=today,
    )
    pet.add_task(task)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_mark_complete_on_one_off_task_does_not_recur():
    task = Task(title="Vet visit", type="appointment", duration_minutes=60, frequency="one-time")

    next_task = task.mark_complete()

    assert next_task is None
    assert task.is_completed is True


# --- Conflict detection ----------------------------------------------------


def test_get_conflicts_flags_tasks_at_the_same_time():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Walk", type="exercise", duration_minutes=30, due_time="9:00 AM"))
    pet.add_task(Task(title="Brush", type="grooming", duration_minutes=15, due_time="9:00 AM"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    conflicts = scheduler.get_conflicts("Monday")

    assert len(conflicts) == 1
    titles = {conflicts[0][0].title, conflicts[0][1].title}
    assert titles == {"Walk", "Brush"}


def test_get_conflicts_flags_overlapping_but_not_identical_times():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Walk", type="exercise", duration_minutes=30, due_time="9:00 AM"))
    pet.add_task(Task(title="Feed", type="feeding", duration_minutes=15, due_time="9:15 AM"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    conflicts = scheduler.get_conflicts("Monday")

    assert len(conflicts) == 1


def test_get_conflicts_ignores_back_to_back_tasks():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Walk", type="exercise", duration_minutes=30, due_time="9:00 AM"))
    pet.add_task(Task(title="Feed", type="feeding", duration_minutes=15, due_time="9:30 AM"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    conflicts = scheduler.get_conflicts("Monday")

    assert conflicts == []


def test_get_conflicts_ignores_completed_tasks():
    pet = Pet(name="Rex", animal_type="dog")
    walk = Task(title="Walk", type="exercise", duration_minutes=30, due_time="9:00 AM", is_completed=True)
    feed = Task(title="Feed", type="feeding", duration_minutes=15, due_time="9:00 AM")
    pet.add_task(walk)
    pet.add_task(feed)

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    conflicts = scheduler.get_conflicts("Monday")

    assert conflicts == []


def test_get_conflicts_flags_overlap_across_midnight():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Late walk", type="exercise", duration_minutes=60, due_time="11:30 PM"))
    pet.add_task(Task(title="Early feed", type="feeding", duration_minutes=30, due_time="12:15 AM"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    conflicts = scheduler.get_conflicts("Monday")

    assert len(conflicts) == 1
    titles = {conflicts[0][0].title, conflicts[0][1].title}
    assert titles == {"Late walk", "Early feed"}


def test_get_conflict_warnings_mentions_pet_name_for_same_pet_conflict():
    pet = Pet(name="Rex", animal_type="dog")
    pet.add_task(Task(title="Walk", type="exercise", duration_minutes=30, due_time="9:00 AM"))
    pet.add_task(Task(title="Brush", type="grooming", duration_minutes=15, due_time="9:00 AM"))

    scheduler = Scheduler()
    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    warnings = scheduler.get_conflict_warnings("Monday")

    assert len(warnings) == 1
    assert "Rex" in warnings[0]


# --- Edge cases: empty / missing data --------------------------------------


def test_pet_with_no_tasks_produces_empty_schedule():
    pet = Pet(name="Ghost", animal_type="cat")
    scheduler = Scheduler()

    scheduler.create_daily_schedule(Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2), pet=pet)

    assert all(day_tasks == [] for day_tasks in scheduler.daily_tasks.values())
    assert scheduler.get_conflicts() == []


def test_owner_with_no_pets_or_tasks_has_no_availability():
    owner = Owner(name="Ann", age=30, gender="F", location="NY", years_owned=2)

    assert owner.get_all_tasks() == []
    assert owner.has_availability() is False


def test_explain_plan_before_schedule_created():
    scheduler = Scheduler()

    assert scheduler.explain_plan() == "No schedule has been created yet."
