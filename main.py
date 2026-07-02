from pawpal_system import Task, Pet, Owner


def print_tasks(label: str, tasks) -> None:
    print(label)
    print("=" * len(label))
    if not tasks:
        print("(none)")
        print()
        return
    for task in tasks:
        status = "done" if task.is_completed else "pending"
        if task.pet:
            animal = f"{task.pet.animal_type}, {task.pet.breed}" if task.pet.breed else task.pet.animal_type
        else:
            animal = "unassigned"
        print(f"- {task.due_time or '??:??'} | {task.title} [{animal}] ({task.duration_minutes} min, priority={task.priority}, {status})")
    print()


def main() -> None:
    owner = Owner(
        name="Alice",
        age=30,
        gender="F",
        location="NYC",
        years_owned=5,
    )

    dog = Pet("Rex", "dog", breed="Golden Retriever", preferred_time_of_day="morning")
    cat = Pet("Whiskers", "cat", breed="Siamese", preferred_time_of_day="evening")

    # Tasks are deliberately added out of chronological order to exercise sort_by_time().
    groom_dog = Task("Groom Rex", "grooming", 20, due_time="7:00 PM", priority="low")
    walk_dog = Task("Walk Rex", "exercise", 30, due_time="9:30 AM", priority="medium")
    feed_dog = Task("Feed Rex", "feeding", 10, due_time="8:00 AM", priority="high")
    # Same pet, same time as walk_dog -> triggers a same-pet conflict.
    brush_dog = Task("Brush Rex", "grooming", 15, due_time="9:30 AM", priority="low")

    play_cat = Task("Play with Whiskers", "enrichment", 15, due_time="5:00 PM", priority="low")
    feed_cat = Task("Feed Whiskers", "feeding", 5, due_time="6:00 PM", priority="high")
    # Different pet, same time as feed_dog -> triggers a cross-pet conflict.
    litter_cat = Task("Clean Litter Box", "cleaning", 10, due_time="8:00 AM", priority="medium")

    owner.add_pet(dog)
    owner.add_pet(cat)

    dog.add_task(groom_dog)
    dog.add_task(walk_dog)
    dog.add_task(feed_dog)
    dog.add_task(brush_dog)

    cat.add_task(play_cat)
    cat.add_task(feed_cat)
    cat.add_task(litter_cat)

    # Mark one task complete so the status filter has something to show.
    feed_dog.mark_complete()

    scheduler = owner.generate_daily_plan()
    today = scheduler.days_of_week[0]

    print_tasks("Today's Schedule (priority, then time, then duration)", scheduler.daily_tasks[today])

    scheduler.sort_by_time(today)
    print_tasks("Today's Schedule (sorted by time only)", scheduler.daily_tasks[today])

    print_tasks("Rex's Tasks Only", scheduler.filter_tasks(day=today, pet_name="Rex"))

    print_tasks("Completed Tasks", scheduler.filter_tasks(day=today, status="completed"))
    print_tasks("Pending Tasks", scheduler.filter_tasks(day=today, status="pending"))

    print("Conflict Check")
    print("==============")
    for warning in scheduler.get_conflict_warnings(today):
        print(warning)
    print()

    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
