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

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->