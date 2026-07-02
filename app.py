import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    age = st.number_input("Owner age", min_value=0, max_value=120, value=30)
    gender = st.text_input("Owner gender", value="")
with col2:
    location = st.text_input("Location", value="")
    years_owned = st.number_input("Years owning pets", min_value=0, max_value=100, value=1)

# Vault check: only build the Owner once per session, then keep reusing/mutating it.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name=owner_name,
        age=int(age),
        gender=gender,
        location=location,
        years_owned=int(years_owned),
    )
owner = st.session_state.owner
owner.name = owner_name
owner.age = int(age)
owner.gender = gender
owner.location = location
owner.years_owned = int(years_owned)

st.markdown("### Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="")
    new_species = st.selectbox("Species", ["dog", "cat", "other"])
    new_preferred_time = st.selectbox("Preferred time of day", ["any", "morning", "afternoon", "evening"])
    pet_submitted = st.form_submit_button("Add pet")

if pet_submitted and new_pet_name:
    owner.add_pet(Pet(name=new_pet_name, animal_type=new_species, preferred_time_of_day=new_preferred_time))

if not owner.pets:
    st.info("No pets yet. Add one above.")
    st.stop()

pet_names = [p.name for p in owner.pets]
selected_pet_name = st.selectbox("Select a pet to manage tasks for", pet_names)
pet = next(p for p in owner.pets if p.name == selected_pet_name)

st.write("Registered pets:")
st.table(
    [
        {"name": p.name, "species": p.animal_type, "preferred_time_of_day": p.preferred_time_of_day}
        for p in owner.pets
    ]
)

st.markdown("### Tasks")
st.caption("Add a few tasks. These feed directly into the pet's care needs and the scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        type=task_title,
        duration_minutes=int(duration),
        priority=priority,
    )
    pet.add_task(new_task)

if pet.care_needs:
    st.write(f"Current tasks for {pet.name}:")
    st.table(
        [
            {
                "title": task.title,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "completed": task.is_completed,
            }
            for task in pet.care_needs
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    st.session_state.scheduler = owner.generate_daily_plan()

if "scheduler" in st.session_state:
    scheduler: Scheduler = st.session_state.scheduler

    st.success(scheduler.explain_plan())

    st.markdown("#### View options")
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_mode = st.radio("Sort by", ["Priority (default)", "Time only"])
    with col2:
        status_filter = st.selectbox("Status", ["all", "completed", "pending"])
    with col3:
        pet_filter = st.selectbox("Pet", ["all"] + pet_names)

    for day in scheduler.days_of_week:
        if sort_mode == "Time only":
            scheduler.sort_by_time(day)

        day_tasks = scheduler.filter_tasks(
            day=day,
            pet_name=None if pet_filter == "all" else pet_filter,
            status=None if status_filter == "all" else status_filter,
        )
        if not day_tasks:
            continue

        st.write(f"**{day}**")

        conflict_warnings = scheduler.get_conflict_warnings(day)
        if conflict_warnings:
            for warning in conflict_warnings:
                st.warning(f"⚠️ {warning}")
        else:
            st.success("✅ No scheduling conflicts for this day.")

        st.table(
            [
                {
                    "title": t.title,
                    "pet": t.pet.name if t.pet else "unassigned",
                    "due_time": t.due_time or "—",
                    "priority": t.priority,
                    "duration_minutes": t.duration_minutes,
                    "completed": t.is_completed,
                }
                for t in day_tasks
            ]
        )
else:
    st.info("No schedule yet. Click 'Generate schedule' above.")
