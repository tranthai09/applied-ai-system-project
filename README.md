# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Enabling the AI Care Assistant (optional)

The AI Care Assistant (see below) works out of the box with no setup — it falls back to a
deterministic offline draft if no API key is configured. To enable real Claude-generated
suggestions instead:

```bash
cp .env.example .env
# then edit .env and set:
# ANTHROPIC_API_KEY=sk-ant-...
```

That's it — `ai_agent.py` loads `.env` automatically. Run `streamlit run app.py` or
`python main.py` either way; check `pawpal_agent.log` to see whether a run used the live
LLM or the offline fallback, and why.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🤖 AI Care Assistant

PawPal+ includes an AI feature combining **Retrieval-Augmented Generation** with an
**agentic workflow**, fully integrated into the scheduling logic (not a side script):

1. **Retrieve** — `care_knowledge.retrieve_guidelines()` scores a small local knowledge base
   of species/breed/situation-specific care guidelines (exercise, feeding, grooming, litter,
   medication, senior/puppy care, etc.) against the selected pet's profile — animal type,
   breed, preferred time of day, and medications.
2. **Generate, grounded** — `CareAgent.plan_care_tasks()` (`ai_agent.py`) sends those
   retrieved guidelines to Claude (`claude-opus-4-8`) with a JSON-schema-constrained request,
   asking it to draft specific tasks *grounded in the retrieved text* rather than from
   general knowledge.
3. **Agentic self-correction** — each drafted task is checked against the pet's *existing*
   schedule using `Scheduler`'s own conflict-detection logic, and any due-time collision is
   nudged forward in 30-minute steps until it clears (or the agent gives up and surfaces a
   warning) — the same conflict rule the rest of the app already enforces.
4. **Guardrails** — every drafted task is validated (duration bounds, allowed
   priority/frequency values, parseable due times) before it becomes a real `Task` object;
   invalid fields are dropped and logged rather than crashing the app. If no API key is
   configured, the LLM call fails, or the model refuses, the agent transparently falls back
   to a deterministic template-based draft built from the same retrieved guidelines — the
   feature (and the app) keeps working either way.
5. **Logging** — every retrieval, LLM call/failure, validation rejection, and conflict nudge
   is written to `pawpal_agent.log` for a full trace of what the assistant did and why.

In the Streamlit UI, click **"Suggest care tasks for `<pet>`"** to run the pipeline; the
retrieved sources, the agent's explanation, and the drafted tasks appear with an
**"Add these tasks"** button that registers them as real tasks and regenerates the schedule.
`main.py` runs the same pipeline for Rex as part of its CLI demo.

### System diagram

Source: [`diagrams/ai_system_diagram.mmd`](diagrams/ai_system_diagram.mmd) — traces the
pipeline from input (pet/owner profile) through the retriever, the agent (with its
LLM/offline-fallback branch), the validator/guardrail layer, and the agentic conflict
resolver, out to the human-review gate (the "Add these tasks" approval step) and the
automated-testing/logging layer that checks each stage's behavior.

## ✨ Features

- **Priority + time + duration sorting** — `Scheduler.create_daily_schedule()` orders each day's tasks by priority (high → medium → low) first, then by due time, then by duration, so the most important care needs surface at the top of the plan.
- **Sort by time only** — `Scheduler.sort_by_time(day)` re-sorts a day chronologically by due time alone, ignoring priority, for a strict timeline view.
- **Filtering** — `Scheduler.filter_tasks()` narrows a schedule by day, pet (instance or name), and completion status, applied cumulatively (AND) so views like "Rex's pending tasks on Monday" are one call.
- **Conflict detection** — `Scheduler.get_conflicts()` does a pairwise scan of each day's due-time windows (accounting for task duration and midnight-spanning tasks) to flag overlaps, whether it's the same pet double-booked or two different pets needing the owner at once.
- **Conflict warnings** — `Scheduler.get_conflict_warnings()` turns detected conflicts into human-readable messages (e.g. "'Walk Rex' (9:30 AM) overlaps with 'Brush Rex' (9:30 AM) - both scheduled for Rex."), surfaced in the Streamlit UI as `st.warning`/`st.success` banners.
- **Daily & weekly recurrence** — `Task.mark_complete()` calls `Task.next_occurrence()` to automatically spawn the next instance of a task, advancing `due_date` by one day for `"daily"` tasks or one week for `"weekly"` tasks, so completing a task keeps it on the schedule going forward.
- **Frequency-to-day mapping** — `Scheduler._days_for_task()` resolves a task's `frequency` field (daily, weekly, a specific weekday, or a comma-separated list of weekdays) into the set of weekday buckets it should appear in.
- **Owner preference matching** — `Task.matches_owner_preference()` checks a task's preferred time of day against the pet's `preferred_time_of_day` (or general owner context when unassigned to a pet).
- **Plan explanation** — `Scheduler.explain_plan()` summarizes the sorting rule used, per-day task/completion counts, and a rollup of any detected conflicts, in plain text.
- **Completion tracking** — `Scheduler.get_completed_tasks()` / `get_incomplete_tasks()` and `Scheduler.track_task_duration()` report status and total scheduled minutes across every day a recurring task appears.

## 📐 Class Diagram

![PawPal+ UML class diagram](diagrams/uml_final.png)

Source: [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd)

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

```
Today's Schedule
================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 7:30 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Tasks are sorted by priority, then due time, then duration.
Monday: 6 task(s), 0 completed, 6 pending.
Tuesday: 6 task(s), 0 completed, 6 pending.
Wednesday: 6 task(s), 0 completed, 6 pending.
Thursday: 6 task(s), 0 completed, 6 pending.
Friday: 6 task(s), 0 completed, 6 pending.
Saturday: 6 task(s), 0 completed, 6 pending.
Sunday: 6 task(s), 0 completed, 6 pending.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov

# Bash command
python -m pytest


The tests in `tests/test_pawpal.py` cover the core scheduling behaviors:

- **Sorting** — tasks are ordered chronologically by due time (handling mixed time formats and missing times), with priority taking precedence over time.
- **Recurrence** — completing a daily task spawns a new occurrence due the next day, completing a weekly task spawns one due the next week, and one-off tasks don't recur.
- **Conflict detection** — overlapping due times (including identical times and overlaps spanning midnight) are flagged, back-to-back tasks are not, and completed tasks are excluded from conflict checks.
- **Edge cases** — a pet with no tasks, an owner with no pets/tasks, and generating an explanation before any schedule exists.


```

Confidence Level: 5 stars


Sample test output:

Today's Schedule (priority, then time, then duration)
=====================================================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 8:00 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Today's Schedule (sorted by time only)
======================================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 8:00 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Rex's Tasks Only
================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Completed Tasks
===============
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)

Pending Tasks
=============
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 8:00 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Conflict Check
==============
Warning: 'Feed Rex' (8:00 AM) overlaps with 'Clean Litter Box' (8:00 AM) - the owner can't be in two places at once.
Warning: 'Walk Rex' (9:30 AM) overlaps with 'Brush Rex' (9:30 AM) - both scheduled for Rex.

Tasks are sorted by priority, then due time, then duration.
Monday: 8 task(s), 1 completed, 7 pending.
Tuesday: 8 task(s), 1 completed, 7 pending.
Wednesday: 8 task(s), 1 completed, 7 pending.
Thursday: 8 task(s), 1 completed, 7 pending.
Friday: 8 task(s), 1 completed, 7 pending.
Saturday: 8 task(s), 1 completed, 7 pending.
Sunday: 8 task(s), 1 completed, 7 pending.
Warning: 14 scheduling conflict(s) detected.

```
# Paste your pytest output here
============================================================================================================ test session starts ============================================================================================================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\Lily Thai\Documents\Codepath Github\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 17 items                                                                                                                                                                                                                           

tests\test_pawpal.py .................                                                                                                                                                                                                 [100%]

============================================================================================================ 17 passed in 0.06s =============================================================================================================
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

### UI features

The Streamlit app (`app.py`) is organized top to bottom into:

- **Owner & Pet** — enter the owner's name, age, gender, location, and years owned; add one or more pets (name, species, preferred time of day) via a form. Registered pets are listed in a table, and a dropdown selects which pet's tasks you're managing.
- **Tasks** — add a task for the selected pet (title, duration in minutes, priority). The pet's current tasks are listed in a table showing duration, priority, and completion status.
- **Build Schedule** — click "Generate schedule" to call `Owner.generate_daily_plan()`, which builds a full week of daily buckets. Once generated, you can:
  - Toggle **Sort by**: "Priority (default)" vs. "Time only" (`Scheduler.sort_by_time()`).
  - Filter by **Status** (all / completed / pending) and by **Pet**, both backed by `Scheduler.filter_tasks()`.
  - See each day's plan as a table (title, pet, due time, priority, duration), with conflict banners above it.

### Example workflow

1. Enter owner info (e.g. "Jordan") and add a pet, "Rex" (dog, preferred time: morning).
2. Select Rex, then add tasks: "Morning walk" (20 min, high priority), and a second task at the same time to see conflict detection in action.
3. Click "Generate schedule" — the app builds a week of daily task buckets sorted by priority, then due time, then duration.
4. View today's (or any weekday's) schedule in the table; switch the "Sort by" toggle to "Time only" to see the same tasks reordered chronologically instead of by priority.
5. Filter down to just Rex's pending tasks using the Pet and Status dropdowns.

### Key Scheduler behaviors shown

- **Priority + time + duration sorting** — the default schedule view orders high-priority tasks first, then by due time, then by duration.
- **Sort by time only** — the "Time only" toggle re-sorts a day strictly chronologically, ignoring priority.
- **Filtering** — the Status and Pet dropdowns narrow the displayed tasks cumulatively (e.g. "Rex's pending tasks").
- **Conflict warnings** — when two tasks' due-time windows overlap (same pet or different pets needing the owner at once), an `st.warning` banner names both tasks and explains why; days with no overlaps get an `st.success` confirmation instead.

### Sample CLI output (`python main.py`)

`main.py` seeds an owner with two pets (Rex the dog, Whiskers the cat) and several tasks — including one already completed and two intentional overlaps (same-pet and cross-pet) — then exercises sorting, filtering, and conflict detection directly against the `Scheduler`:

```
Today's Schedule (priority, then time, then duration)
=====================================================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 8:00 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Today's Schedule (sorted by time only)
======================================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 8:00 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Rex's Tasks Only
================
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Completed Tasks
===============
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, done)

Pending Tasks
=============
- 8:00 AM | Feed Rex [dog, Golden Retriever] (10 min, priority=high, pending)
- 8:00 AM | Clean Litter Box [cat, Siamese] (10 min, priority=medium, pending)
- 9:30 AM | Walk Rex [dog, Golden Retriever] (30 min, priority=medium, pending)
- 9:30 AM | Brush Rex [dog, Golden Retriever] (15 min, priority=low, pending)
- 5:00 PM | Play with Whiskers [cat, Siamese] (15 min, priority=low, pending)
- 6:00 PM | Feed Whiskers [cat, Siamese] (5 min, priority=high, pending)
- 7:00 PM | Groom Rex [dog, Golden Retriever] (20 min, priority=low, pending)

Conflict Check
==============
Warning: 'Feed Rex' (8:00 AM) overlaps with 'Clean Litter Box' (8:00 AM) - the owner can't be in two places at once.
Warning: 'Walk Rex' (9:30 AM) overlaps with 'Brush Rex' (9:30 AM) - both scheduled for Rex.

Tasks are sorted by priority, then due time, then duration.
Monday: 8 task(s), 1 completed, 7 pending.
Tuesday: 8 task(s), 1 completed, 7 pending.
Wednesday: 8 task(s), 1 completed, 7 pending.
Thursday: 8 task(s), 1 completed, 7 pending.
Friday: 8 task(s), 1 completed, 7 pending.
Saturday: 8 task(s), 1 completed, 7 pending.
Sunday: 8 task(s), 1 completed, 7 pending.
Warning: 14 scheduling conflict(s) detected.
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->