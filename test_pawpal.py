# test_pawpal.py
# pytest test suite for the PawPal core system.
# Run: pytest test_pawpal.py -v

from pawpal_system import Owner, Pet, Task, Scheduler


# ------------------------------------------------------------------ #
# Owner tests
# ------------------------------------------------------------------ #

def test_owner_add_and_get_pets():
    """Owner.add_pet() stores pets; Owner.get_pets() returns them."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    cat = Pet("Luna", "Cat", 4)

    owner.add_pet(dog)
    owner.add_pet(cat)

    pets = owner.get_pets()
    assert len(pets) == 2
    assert pets[0].name == "Rex"
    assert pets[1].name == "Luna"


def test_owner_starts_with_no_pets():
    """A newly created Owner has an empty pet list."""
    owner = Owner("Sam", "sam@example.com")
    assert owner.get_pets() == []


# ------------------------------------------------------------------ #
# Pet tests
# ------------------------------------------------------------------ #

def test_pet_add_and_get_tasks():
    """Pet.add_task() stores tasks; Pet.get_tasks() returns them."""
    pet = Pet("Rex", "Dog", 2)
    task = Task("Morning Walk", "2026-03-16", "07:00", "walk")

    pet.add_task(task)
    tasks = pet.get_tasks()

    assert len(tasks) == 1
    assert tasks[0].title == "Morning Walk"


# ------------------------------------------------------------------ #
# Task tests
# ------------------------------------------------------------------ #

def test_task_defaults():
    """A Task starts as not completed and non-recurring."""
    task = Task("Vet Visit", "2026-03-17", "10:00", "vet")
    assert task.completed is False
    assert task.recurring is False
    assert task.recur_days == 0


def test_task_mark_complete():
    """Task.mark_complete() changes completed from False to True."""
    task = Task("Vet Visit", "2026-03-17", "10:00", "vet")
    task.mark_complete()
    assert task.completed is True


# ------------------------------------------------------------------ #
# Scheduler tests
# ------------------------------------------------------------------ #

def test_scheduler_builds_registry():
    """Scheduler collects all tasks from all pets into one flat list."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    dog.add_task(Task("Walk", "2026-03-16", "08:00", "walk"))
    dog.add_task(Task("Feed", "2026-03-16", "12:00", "feeding"))
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    assert len(scheduler.get_all_tasks()) == 2


def test_scheduler_sort_by_date():
    """sort_tasks_by_date() returns tasks in chronological order."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    # Add intentionally out of order
    dog.add_task(Task("Evening Walk", "2026-03-16", "18:00", "walk"))
    dog.add_task(Task("Morning Walk", "2026-03-16", "07:00", "walk"))
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_tasks_by_date()

    assert sorted_tasks[0][1].title == "Morning Walk"
    assert sorted_tasks[1][1].title == "Evening Walk"


def test_scheduler_filter_by_pet():
    """filter_by_pet() returns only tasks for the specified pet."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    cat = Pet("Luna", "Cat", 3)
    dog.add_task(Task("Walk", "2026-03-16", "08:00", "walk"))
    cat.add_task(Task("Feed", "2026-03-16", "09:00", "feeding"))
    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)
    rex_tasks = scheduler.filter_by_pet("Rex")

    assert len(rex_tasks) == 1
    assert rex_tasks[0][1].title == "Walk"


def test_scheduler_filter_by_status():
    """filter_by_status() correctly separates pending and completed tasks."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    t1 = Task("Walk", "2026-03-16", "08:00", "walk")
    t2 = Task("Feed", "2026-03-16", "12:00", "feeding")
    t1.mark_complete()
    dog.add_task(t1)
    dog.add_task(t2)
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    pending   = scheduler.filter_by_status(completed=False)
    completed = scheduler.filter_by_status(completed=True)

    assert len(pending)   == 1
    assert len(completed) == 1
    assert pending[0][1].title   == "Feed"
    assert completed[0][1].title == "Walk"


def test_scheduler_detects_conflict():
    """
    Two tasks for the SAME pet at the same date+time is a conflict.
    Both conflicting tasks should appear in the returned list.
    """
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    dog.add_task(Task("Walk", "2026-03-16", "08:00", "walk"))
    dog.add_task(Task("Bath", "2026-03-16", "08:00", "grooming"))  # conflict!
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    # Both tasks should be returned
    assert len(conflicts) == 2
    conflict_titles = {task.title for _, task in conflicts}
    assert "Walk" in conflict_titles
    assert "Bath" in conflict_titles


def test_scheduler_no_conflict_different_pets():
    """
    Two DIFFERENT pets can have tasks at the same date+time — no conflict.

    FAILING SCENARIO EXPLANATION:
    If detect_conflicts() used only (date, time) as the conflict key
    (forgetting pet_name), this test would FAIL because the two tasks
    would look like a conflict even though they belong to different pets.
    Our implementation uses (pet_name, date, time) as the key, so this
    test correctly passes.
    """
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    cat = Pet("Luna", "Cat", 3)
    dog.add_task(Task("Walk", "2026-03-16", "08:00", "walk"))
    cat.add_task(Task("Feed", "2026-03-16", "08:00", "feeding"))  # same time, different pet
    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts()

    assert conflicts == []  # different pets — not a conflict


def test_scheduler_recurring_tasks():
    """get_recurring_tasks() returns only recurring tasks."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    t_recurring = Task("Daily Feed", "2026-03-16", "08:00", "feeding",
                       recurring=True, recur_days=1)
    t_one_off   = Task("Vet Visit",  "2026-03-17", "10:00", "vet")
    dog.add_task(t_recurring)
    dog.add_task(t_one_off)
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    recurring = scheduler.get_recurring_tasks()

    assert len(recurring) == 1
    assert recurring[0][1].title == "Daily Feed"


def test_scheduler_refresh_picks_up_new_tasks():
    """After calling refresh(), the Scheduler sees tasks added after creation."""
    owner = Owner("Sam", "sam@example.com")
    dog = Pet("Rex", "Dog", 2)
    dog.add_task(Task("Walk", "2026-03-16", "08:00", "walk"))
    owner.add_pet(dog)

    scheduler = Scheduler(owner)
    assert len(scheduler.get_all_tasks()) == 1

    # Add a task AFTER Scheduler was created
    dog.add_task(Task("Feed", "2026-03-16", "12:00", "feeding"))
    scheduler.refresh()

    assert len(scheduler.get_all_tasks()) == 2
