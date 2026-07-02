from pawpal_system import Pet, Task


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
