from pawpal_system import Task, Pet, Owner


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

    feed_dog = Task("Feed Rex", "feeding", 10, due_time="8:00 AM", priority="high")
    walk_dog = Task("Walk Rex", "exercise", 30, due_time="9:30 AM", priority="medium")
    groom_dog = Task("Groom Rex", "grooming", 20, due_time="7:00 PM", priority="low")

    feed_cat = Task("Feed Whiskers", "feeding", 5, due_time="6:00 PM", priority="high")
    litter_cat = Task("Clean Litter Box", "cleaning", 10, due_time="7:30 AM", priority="medium")
    play_cat = Task("Play with Whiskers", "enrichment", 15, due_time="5:00 PM", priority="low")

    owner.add_pet(dog)
    owner.add_pet(cat)

    dog.add_task(feed_dog)
    dog.add_task(walk_dog)
    dog.add_task(groom_dog)

    cat.add_task(feed_cat)
    cat.add_task(litter_cat)
    cat.add_task(play_cat)

    scheduler = owner.generate_daily_plan()

    today = scheduler.days_of_week[0]
    print("Today's Schedule")
    print("================")
    for task in scheduler.daily_tasks[today]:
        status = "done" if task.is_completed else "pending"
        if task.pet:
            animal = f"{task.pet.animal_type}, {task.pet.breed}" if task.pet.breed else task.pet.animal_type
        else:
            animal = "unassigned"
        print(f"- {task.due_time or '??:??'} | {task.title} [{animal}] ({task.duration_minutes} min, priority={task.priority}, {status})")

    print()
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
