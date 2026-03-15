# pawpal_system.py
# Core classes for the PawPal Pet Care Scheduling System.
#
# Class relationships:
#   Owner  --has many-->  Pet  --has many-->  Task
#   Scheduler receives an Owner and walks Owner->Pet->Task to collect all tasks.


class Task:
    """
    A single care task for a pet.
    Stores what needs to be done, when, and whether it repeats.
    """

    def __init__(self, title, date, time, task_type="general",
                 recurring=False, recur_days=0):
        self.title = title          # short description, e.g. "Morning Walk"
        self.date = date            # "YYYY-MM-DD"
        self.time = time            # "HH:MM"
        self.task_type = task_type  # "feeding", "vet", "walk", "grooming", etc.
        self.completed = False      # starts as not done
        self.recurring = recurring  # True if this task repeats
        self.recur_days = recur_days  # repeat every N days when recurring=True

    def mark_complete(self):
        """Mark this task as done."""
        self.completed = True

    def __repr__(self):
        status = "Done" if self.completed else "Pending"
        recur = f" | every {self.recur_days}d" if self.recurring else ""
        return f"Task('{self.title}', {self.date} {self.time}, [{self.task_type}], {status}{recur})"


class Pet:
    """
    A pet that belongs to an Owner.
    Holds a list of Task objects assigned to this pet.
    """

    def __init__(self, name, species, age):
        self.name = name
        self.species = species
        self.age = age
        self.tasks = []  # list of Task objects for this pet

    def add_task(self, task):
        """Attach a Task to this pet."""
        self.tasks.append(task)

    def get_tasks(self):
        """Return all tasks for this pet."""
        return self.tasks

    def __repr__(self):
        return f"Pet('{self.name}', {self.species}, age={self.age})"


class Owner:
    """
    A pet owner who can register multiple pets.
    Acts as the root of the Owner -> Pet -> Task chain.
    """

    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.pets = []  # list of Pet objects

    def add_pet(self, pet):
        """Register a Pet under this owner."""
        self.pets.append(pet)

    def get_pets(self):
        """Return all pets belonging to this owner."""
        return self.pets

    def __repr__(self):
        return f"Owner('{self.name}', {self.email}, {len(self.pets)} pet(s))"


class Scheduler:
    """
    Manages and analyzes all tasks across an owner's pets.

    The Scheduler does NOT store tasks of its own.
    It reads from the Owner -> Pet -> Task chain and builds a flat
    working list so that sorting, filtering, and conflict detection
    are straightforward.

    Call refresh() after adding new pets or tasks to re-sync.
    """

    def __init__(self, owner):
        self.owner = owner
        # A flat list of (pet_name, task) tuples built from Owner->Pet->Task
        self.task_registry = self._build_registry()

    def _build_registry(self):
        """
        Walk Owner -> pets -> tasks and collect every task into a flat list.
        Each entry is a (pet_name, task) tuple so we always know which pet
        a task belongs to without having to dig into nested lists again.

        This is the core of the Owner -> Pet -> Task -> Scheduler relationship.
        """
        registry = []
        for pet in self.owner.get_pets():
            for task in pet.get_tasks():
                registry.append((pet.name, task))
        return registry

    def refresh(self):
        """Re-build the registry. Call this after adding new pets or tasks."""
        self.task_registry = self._build_registry()

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #

    def get_all_tasks(self):
        """Return all (pet_name, task) pairs in the registry."""
        return self.task_registry

    # ------------------------------------------------------------------ #
    # Sorting
    # ------------------------------------------------------------------ #

    def sort_tasks_by_date(self):
        """
        Return a new list of (pet_name, task) sorted by date then time
        (both are strings in YYYY-MM-DD and HH:MM format, so lexicographic
        sort gives the correct chronological order).
        The original registry is NOT modified.
        """
        return sorted(
            self.task_registry,
            key=lambda pair: (pair[1].date, pair[1].time)
        )

    # ------------------------------------------------------------------ #
    # Filtering
    # ------------------------------------------------------------------ #

    def filter_by_pet(self, pet_name):
        """Return only tasks that belong to the named pet."""
        return [(name, task) for name, task in self.task_registry
                if name == pet_name]

    def filter_by_status(self, completed=False):
        """
        Return tasks filtered by completion status.
        completed=False  -> pending tasks
        completed=True   -> finished tasks
        """
        return [(name, task) for name, task in self.task_registry
                if task.completed == completed]

    def filter_by_type(self, task_type):
        """Return tasks of a specific type, e.g. 'vet', 'feeding'."""
        return [(name, task) for name, task in self.task_registry
                if task.task_type == task_type]

    # ------------------------------------------------------------------ #
    # Conflict Detection
    # ------------------------------------------------------------------ #

    def detect_conflicts(self):
        """
        Detect scheduling conflicts.
        A conflict = two or more tasks for the SAME pet at the same date+time.
        (Two different pets having tasks at the same time is NOT a conflict.)

        Returns a flat list of all (pet_name, task) pairs that are in conflict.
        """
        # Group tasks by (pet_name, date, time)
        groups = {}
        for pet_name, task in self.task_registry:
            key = (pet_name, task.date, task.time)
            if key not in groups:
                groups[key] = []
            groups[key].append((pet_name, task))

        # Collect any group that has more than one task
        conflicts = []
        for key, entries in groups.items():
            if len(entries) > 1:
                conflicts.extend(entries)
        return conflicts

    # ------------------------------------------------------------------ #
    # Recurring Tasks
    # ------------------------------------------------------------------ #

    def get_recurring_tasks(self):
        """Return all tasks that are marked as recurring."""
        return [(name, task) for name, task in self.task_registry
                if task.recurring]
