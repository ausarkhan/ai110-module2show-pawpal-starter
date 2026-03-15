# main.py
# Demonstrates the full data flow of the PawPal system.
# Run: python main.py

from pawpal_system import Owner, Pet, Task, Scheduler

SEP = "=" * 55

print(SEP)
print("PawPal System — Data Flow Demonstration")
print(SEP)

# ------------------------------------------------------------------ #
# STEP 1: Create an Owner
# ------------------------------------------------------------------ #
owner = Owner(name="Alex Johnson", email="alex@pawpal.com")
print(f"\n[1] Owner created:\n    {owner}")

# ------------------------------------------------------------------ #
# STEP 2: Create Pets and attach them to the Owner
#   Data flow: Owner.add_pet(pet) -> owner.pets list grows
# ------------------------------------------------------------------ #
dog = Pet(name="Buddy", species="Dog", age=3)
cat = Pet(name="Whiskers", species="Cat", age=5)

owner.add_pet(dog)
owner.add_pet(cat)

print(f"\n[2] Pets registered under {owner.name}:")
for pet in owner.get_pets():
    print(f"    {pet}")

# ------------------------------------------------------------------ #
# STEP 3: Create Tasks and attach them to Pets
#   Data flow: Pet.add_task(task) -> pet.tasks list grows
# ------------------------------------------------------------------ #
# Buddy's tasks
task1 = Task(title="Morning Walk",   date="2026-03-16", time="07:00", task_type="walk")
task2 = Task(title="Vet Checkup",    date="2026-03-17", time="10:00", task_type="vet")
task3 = Task(title="Evening Feed",   date="2026-03-16", time="18:00", task_type="feeding",
             recurring=True, recur_days=1)

# Whiskers' tasks
task4 = Task(title="Grooming",       date="2026-03-17", time="09:00", task_type="grooming")
task5 = Task(title="Flea Treatment", date="2026-03-18", time="11:00", task_type="health")

dog.add_task(task1)
dog.add_task(task2)
dog.add_task(task3)
cat.add_task(task4)
cat.add_task(task5)

print(f"\n[3a] Tasks for {dog.name}:")
for t in dog.get_tasks():
    print(f"    {t}")

print(f"\n[3b] Tasks for {cat.name}:")
for t in cat.get_tasks():
    print(f"    {t}")

# ------------------------------------------------------------------ #
# STEP 4: Create the Scheduler
#   The Scheduler walks Owner -> Pet -> Task and builds a flat list.
#   Data flow: Owner -> pets -> tasks -> task_registry (flat list)
# ------------------------------------------------------------------ #
scheduler = Scheduler(owner)

print(f"\n[4] All tasks collected by Scheduler ({len(scheduler.get_all_tasks())} total):")
for pet_name, task in scheduler.get_all_tasks():
    print(f"    [{pet_name}]  {task}")

# ------------------------------------------------------------------ #
# STEP 5: Sorting — sort all tasks by date then time
# ------------------------------------------------------------------ #
print("\n[5] Tasks sorted by date/time:")
for pet_name, task in scheduler.sort_tasks_by_date():
    print(f"    [{pet_name}]  {task}")

# ------------------------------------------------------------------ #
# STEP 6: Filtering
# ------------------------------------------------------------------ #
print(f"\n[6a] Filter — tasks for Buddy only:")
for pet_name, task in scheduler.filter_by_pet("Buddy"):
    print(f"    {task}")

print(f"\n[6b] Filter — pending tasks (not yet completed):")
for pet_name, task in scheduler.filter_by_status(completed=False):
    print(f"    [{pet_name}]  {task}")

# Mark task1 as complete and re-check pending
task1.mark_complete()
scheduler.refresh()
print(f"\n[6c] After marking 'Morning Walk' complete — pending tasks:")
for pet_name, task in scheduler.filter_by_status(completed=False):
    print(f"    [{pet_name}]  {task}")

print(f"\n[6d] Filter — tasks of type 'vet':")
for pet_name, task in scheduler.filter_by_type("vet"):
    print(f"    [{pet_name}]  {task}")

# ------------------------------------------------------------------ #
# STEP 7: Recurring tasks
# ------------------------------------------------------------------ #
print("\n[7] Recurring tasks:")
recurring = scheduler.get_recurring_tasks()
if recurring:
    for pet_name, task in recurring:
        print(f"    [{pet_name}]  {task}")
else:
    print("    (none)")

# ------------------------------------------------------------------ #
# STEP 8: Conflict Detection
#   Add a task for Buddy at the exact same date+time as task1 (07:00)
#   to trigger a conflict.
# ------------------------------------------------------------------ #
conflict_task = Task(
    title="Bath Time",
    date="2026-03-16",
    time="07:00",
    task_type="grooming"
)
dog.add_task(conflict_task)
scheduler.refresh()

print("\n[8] Conflict Detection:")
print("    (Added 'Bath Time' for Buddy at 2026-03-16 07:00 — same as 'Morning Walk')")
conflicts = scheduler.detect_conflicts()
if conflicts:
    print(f"    {len(conflicts) // 2} conflict(s) found:")
    seen = set()
    for pet_name, task in conflicts:
        key = (pet_name, task.date, task.time)
        if key not in seen:
            print(f"      [{pet_name}] @ {task.date} {task.time}:")
            seen.add(key)
        print(f"        - {task.title}")
else:
    print("    No conflicts found.")

# ------------------------------------------------------------------ #
# STEP 9: Method Explanation
#   _build_registry() is the key method that connects all four classes.
# ------------------------------------------------------------------ #
print(f"""
[9] Method deep-dive: Scheduler._build_registry()
    -------------------------------------------------
    This method is called when the Scheduler is first created (or
    when refresh() is called).

    It loops over every pet returned by owner.get_pets(), and for
    each pet it loops over every task returned by pet.get_tasks().
    Each (pet_name, task) pair is appended to a flat list called
    task_registry.

    Why flatten?  The rest of the Scheduler methods (sort, filter,
    conflict detection) only need to iterate ONE list instead of
    nested loops.  This keeps each method simple and readable.

    Chain:  owner ──> pet ──> task ──> (pet_name, task) in registry
""")

print(SEP)
print("End of demonstration.")
print(SEP)
