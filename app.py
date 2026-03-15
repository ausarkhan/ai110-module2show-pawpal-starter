# app.py
# Streamlit UI for the PawPal Pet Care Scheduler.
# Run: streamlit run app.py
#
# ---------------------------------------------------------------
# WHY st.session_state IS NEEDED
# ---------------------------------------------------------------
# Streamlit re-runs the ENTIRE script from top to bottom on every
# user interaction (button click, text input, etc.).
#
# THE STATE RESET BUG:
#   If you write  `owner = Owner("Alex", "alex@pawpal.com")`  at
#   the module level without a guard, a brand-new Owner object is
#   created every time the page rerenders — wiping all pets and
#   tasks the user just added.
#
# HOW WE FIX IT:
#   We store the Owner in st.session_state and only create it ONCE
#   using the guard:
#       if "owner" not in st.session_state:
#           st.session_state.owner = Owner(...)
#   On every subsequent rerun, the existing Owner (with all its
#   pets and tasks) is read back from session_state unchanged.
# ---------------------------------------------------------------

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal Scheduler", page_icon="🐾")
st.title("🐾 PawPal — Pet Care Scheduler")

# ---------------------------------------------------------------
# Initialize persistent state (run ONCE per browser session)
# ---------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="My Account", email="user@pawpal.com")

# Convenience alias — still points to the same object in session_state
owner: Owner = st.session_state.owner

# ---------------------------------------------------------------
# SIDEBAR: Add a New Pet
#
# UI action trace:
#   User fills in name/species/age and clicks "Add Pet"
#   -> new Pet object created
#   -> owner.add_pet(new_pet) called on the session_state owner
#   -> owner.pets list grows (persists across reruns)
# ---------------------------------------------------------------
st.sidebar.header("Add a Pet")

pet_name_input    = st.sidebar.text_input("Pet Name", key="new_pet_name")
pet_species_input = st.sidebar.text_input("Species (e.g. Dog, Cat)", key="new_pet_species")
pet_age_input     = st.sidebar.number_input("Age", min_value=0, max_value=50, value=1,
                                            key="new_pet_age")

if st.sidebar.button("Add Pet"):
    if pet_name_input.strip():
        new_pet = Pet(
            name=pet_name_input.strip(),
            species=pet_species_input.strip() or "Unknown",
            age=int(pet_age_input)
        )
        owner.add_pet(new_pet)
        st.sidebar.success(f"'{new_pet.name}' added!")
    else:
        st.sidebar.error("Please enter a pet name.")

# ---------------------------------------------------------------
# MAIN AREA
# ---------------------------------------------------------------
pets = owner.get_pets()

if not pets:
    st.info("No pets registered yet. Use the sidebar to add your first pet.")
else:
    # Let the user choose which pet to work with
    pet_names = [p.name for p in pets]
    selected_name = st.selectbox("Select a pet", pet_names)
    selected_pet: Pet = next(p for p in pets if p.name == selected_name)

    st.divider()

    # -----------------------------------------------------------
    # Schedule a New Task
    # -----------------------------------------------------------
    st.subheader(f"Schedule a task for {selected_pet.name}")

    task_title    = st.text_input("Task Title", key="task_title")
    task_date     = st.date_input("Date",        key="task_date")
    task_time_val = st.time_input("Time",         key="task_time")
    task_type     = st.selectbox("Task Type",
                                 ["feeding", "walk", "vet",
                                  "grooming", "health", "general"],
                                 key="task_type")
    task_recurring  = st.checkbox("Recurring task?", key="task_recurring")
    task_recur_days = 0
    if task_recurring:
        task_recur_days = st.number_input(
            "Repeat every N days", min_value=1, max_value=365, value=1,
            key="recur_days"
        )

    if st.button("Schedule Task"):
        if task_title.strip():
            new_task = Task(
                title=task_title.strip(),
                date=str(task_date),                          # "YYYY-MM-DD"
                time=task_time_val.strftime("%H:%M"),         # "HH:MM"
                task_type=task_type,
                recurring=task_recurring,
                recur_days=int(task_recur_days)
            )
            # This mutates the Pet object that lives inside session_state.owner,
            # so the task persists on the next rerun.
            selected_pet.add_task(new_task)
            st.success(f"Task '{new_task.title}' scheduled for {selected_pet.name}!")
        else:
            st.error("Please enter a task title.")

    st.divider()

    # -----------------------------------------------------------
    # Display Tasks for Selected Pet (sorted by date/time)
    # -----------------------------------------------------------
    st.subheader(f"Tasks for {selected_pet.name}")

    # Build a fresh Scheduler each render — it reads from the
    # session_state owner so it always reflects current data.
    scheduler = Scheduler(owner)
    pet_tasks = scheduler.filter_by_pet(selected_pet.name)

    if not pet_tasks:
        st.write("No tasks scheduled yet.")
    else:
        sorted_pairs = scheduler.sort_tasks_by_date()
        for pet_name, task in sorted_pairs:
            if pet_name != selected_pet.name:
                continue
            status_icon = "✅" if task.completed else "⏳"
            recur_note  = f" | 🔁 every {task.recur_days}d" if task.recurring else ""
            st.write(
                f"{status_icon} **{task.title}** &nbsp;|&nbsp; "
                f"{task.date} {task.time} &nbsp;|&nbsp; "
                f"*{task.task_type}*{recur_note}"
            )

    st.divider()

    # -----------------------------------------------------------
    # Conflict Detection (all pets)
    # -----------------------------------------------------------
    st.subheader("Scheduling Conflicts (all pets)")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        # Deduplicate for display: show each conflicting time-slot once
        seen = set()
        st.warning(f"{len(conflicts) // 2} conflict(s) detected!")
        for pet_name, task in conflicts:
            key = (pet_name, task.date, task.time)
            if key not in seen:
                st.write(f"**[{pet_name}]** @ {task.date} {task.time}")
                seen.add(key)
            st.write(f"&nbsp;&nbsp;&nbsp;• {task.title} ({task.task_type})")
    else:
        st.success("No scheduling conflicts found.")

    st.divider()

    # -----------------------------------------------------------
    # Recurring Tasks summary (all pets)
    # -----------------------------------------------------------
    st.subheader("Recurring Tasks (all pets)")
    recurring = scheduler.get_recurring_tasks()
    if recurring:
        for pet_name, task in recurring:
            st.write(
                f"🔁 **[{pet_name}]** {task.title} — "
                f"every {task.recur_days} day(s) starting {task.date}"
            )
    else:
        st.info("No recurring tasks scheduled.")
