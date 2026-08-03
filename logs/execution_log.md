# Reproducible Execution Evidence

This file replaces demo screenshots with actual captured command output. Every
block below is a verbatim terminal capture from running the exact command
shown, in this repo, with no `ANTHROPIC_API_KEY` configured (the `anthropic`
package isn't even installed in the environment these captures were taken
in — see the "No module named 'anthropic'" line in the log excerpt below).
That's a deliberate choice, not an oversight: it's the worst-case
configuration for this project, and everything below still runs cleanly,
which is the whole point of the offline-fallback design described in the
README and `model_card.md`.

Raw copies of each capture live alongside this file:

| Command | Raw capture |
|---|---|
| `pytest -v` | [`pytest_output.txt`](pytest_output.txt) |
| `python main.py` | [`main_py_output.txt`](main_py_output.txt) |
| `python evaluate_care_agent.py` | [`evaluate_care_agent_output.txt`](evaluate_care_agent_output.txt) |
| `streamlit run app.py --server.headless true` | [`streamlit_startup.txt`](streamlit_startup.txt) |
| `pawpal_agent.log` produced by the `main.py` run above | [`pawpal_agent_sample.txt`](pawpal_agent_sample.txt) |

Everything here is regenerable — running the same commands against the same
code should reproduce the same pass/fail outcomes (the deterministic
offline-fallback scenarios reproduce byte-for-byte; wall-clock timings and
random ports will naturally differ run to run).

---

## 1. Automated test suite — `pytest -v`

Full command: `python -m pytest -v`

```
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.0.3, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Lily Thai\Documents\Codepath Github\project4
plugins: anyio-4.13.0
collecting ... collected 30 items

tests/test_ai_agent.py::test_retrieve_guidelines_prioritizes_dog_topics_for_a_dog PASSED [  3%]
tests/test_ai_agent.py::test_retrieve_guidelines_matches_cat_topics_for_a_cat PASSED [  6%]
tests/test_ai_agent.py::test_retrieve_guidelines_surfaces_medication_doc_when_pet_has_meds PASSED [ 10%]
tests/test_ai_agent.py::test_retrieve_guidelines_returns_empty_for_blank_profile PASSED [ 13%]
tests/test_ai_agent.py::test_validate_draft_accepts_well_formed_draft PASSED [ 16%]
tests/test_ai_agent.py::test_validate_draft_rejects_missing_title PASSED [ 20%]
tests/test_ai_agent.py::test_validate_draft_rejects_out_of_bounds_duration PASSED [ 23%]
tests/test_ai_agent.py::test_validate_draft_defaults_unknown_priority_to_medium PASSED [ 26%]
tests/test_ai_agent.py::test_validate_draft_drops_unparseable_due_time PASSED [ 30%]
tests/test_ai_agent.py::test_resolve_conflicts_nudges_candidate_away_from_existing_task PASSED [ 33%]
tests/test_ai_agent.py::test_resolve_conflicts_leaves_non_conflicting_task_untouched PASSED [ 36%]
tests/test_ai_agent.py::test_plan_care_tasks_offline_fallback_produces_valid_tasks PASSED [ 40%]
tests/test_ai_agent.py::test_plan_care_tasks_avoids_conflicts_with_existing_schedule PASSED [ 43%]
tests/test_pawpal.py::test_mark_complete_marks_task_complete PASSED      [ 46%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 50%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 53%]
tests/test_pawpal.py::test_sort_by_time_handles_mixed_formats_and_missing_time PASSED [ 56%]
tests/test_pawpal.py::test_daily_schedule_sorts_by_priority_before_time PASSED [ 60%]
tests/test_pawpal.py::test_mark_complete_on_daily_task_creates_next_day_task PASSED [ 63%]
tests/test_pawpal.py::test_mark_complete_on_weekly_task_advances_by_one_week PASSED [ 66%]
tests/test_pawpal.py::test_mark_complete_on_one_off_task_does_not_recur PASSED [ 70%]
tests/test_pawpal.py::test_get_conflicts_flags_tasks_at_the_same_time PASSED [ 73%]
tests/test_pawpal.py::test_get_conflicts_flags_overlapping_but_not_identical_times PASSED [ 76%]
tests/test_pawpal.py::test_get_conflicts_ignores_back_to_back_tasks PASSED [ 80%]
tests/test_pawpal.py::test_get_conflicts_ignores_completed_tasks PASSED  [ 83%]
tests/test_pawpal.py::test_get_conflicts_flags_overlap_across_midnight PASSED [ 86%]
tests/test_pawpal.py::test_get_conflict_warnings_mentions_pet_name_for_same_pet_conflict PASSED [ 90%]
tests/test_pawpal.py::test_pet_with_no_tasks_produces_empty_schedule PASSED [ 93%]
tests/test_pawpal.py::test_owner_with_no_pets_or_tasks_has_no_availability PASSED [ 96%]
tests/test_pawpal.py::test_explain_plan_before_schedule_created PASSED   [100%]

============================= 30 passed in 0.13s ==============================
```

## 2. CLI end-to-end demo — `python main.py`

Seeds an owner with two pets, exercises sorting/filtering/conflict detection
on the original scheduler, then runs the AI Care Assistant for Rex:

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

[... sort-by-time / per-pet / completed / pending views omitted here, see main_py_output.txt for the full capture ...]

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

AI Care Assistant (Rex)
=======================
[offline fallback] Used offline template fallback (no LLM available) to draft 3 task(s) for Rex from 3 retrieved guideline(s).
Suggested tasks
===============
- 8:30 AM | Walk [unassigned] (30 min, priority=high, pending)
- 7:00 AM | Feed [unassigned] (10 min, priority=high, pending)
- 6:00 PM | Brush coat [unassigned] (15 min, priority=low, pending)

(See pawpal_agent.log for the full retrieval/generation trace.)
```

Full, untrimmed capture: [`main_py_output.txt`](main_py_output.txt).

The `pawpal_agent.log` that `main.py` produced on this exact run:

```
2026-07-30 21:26:17,251 INFO Anthropic client unavailable, will use offline fallback: No module named 'anthropic'
2026-07-30 21:26:17,252 INFO Retrieved 3 guideline(s) for Rex: ['dog-exercise', 'dog-feeding', 'dog-grooming']
2026-07-30 21:26:17,255 INFO Used offline template fallback (no LLM available) to draft 3 task(s) for Rex from 3 retrieved guideline(s).
```

That first line is real, not staged: this evaluation environment doesn't even
have the `anthropic` package installed, so `CareAgent` caught the
`ImportError`, logged it, and fell back automatically — exactly the failure
mode the design is meant to survive.

## 3. Reliability evaluation harness — `python evaluate_care_agent.py`

```
6 out of 6 reliability checks passed (100%) against the offline-fallback pipeline.
[Pass] Dog, empty schedule - Produces >=1 grounded, in-bounds task from retrieved sources :: 3 task(s), 3 source(s), all within bounds
[Pass] Cat, conflicting existing task - No drafted task collides with the existing 7:00 AM task :: no drafted task collides with the pet's existing 7:00 AM task
[Pass] Senior dog on medication - Retrieves the senior-pet guideline, not just generic dog guidelines :: senior-pet guideline retrieved among: ['Care adjustments for senior pets (senior-pet)', 'Daily exercise for dogs (dog-exercise)', 'Feeding schedule for dogs (dog-feeding)']
[Pass] Unknown species (iguana) - Handles a species outside the knowledge base gracefully (no crash, no fabrication) :: returned an empty, explained result instead of crashing or guessing
[Pass] max_tasks is respected - Requesting max_tasks=1 drafts at most 1 task :: 1 task(s) drafted, within the requested max_tasks=1
[Pass] Offline fallback path actually runs - used_llm is False when the client is unavailable :: used_llm=False, confirming the offline fallback path actually ran

Full report written to eval_results.md
```

This regenerates [`../eval_results.md`](../eval_results.md) at the repo root
every time it's run — that file and this capture should always agree.

## 4. Streamlit UI boots cleanly — `streamlit run app.py`

Run headless (no browser) to capture the server-side boot log as text instead
of a screenshot:

```
python -m streamlit run app.py --server.headless true --server.port 8541
```

```
2026-07-30 21:27:09.734 Uvicorn server started on 0.0.0.0:8541

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8541
  Network URL: http://192.168.1.180:8541
  External URL: http://108.48.176.107:8541
```

A follow-up `curl -s -o /dev/null -w "%{http_code}" http://localhost:8541`
against the running server returned `HTTP 200`, and the server log contained
no traceback or exception output — confirming the full app (including the
new "AI Care Assistant" section) executes top-to-bottom with no server-side
errors. Interactively clicking "Suggest care tasks" / "Add these tasks" in
the browser isn't something a text log can capture; that click-through was
verified manually (see the Sample Interactions and Testing Summary sections
of the README) rather than claimed here.

---

## Honesty note

These captures were all taken with the offline fallback active (no API key,
`anthropic` package not even installed). That's the correct evidence for
"does the guaranteed, guardrail-covered path actually work reproducibly" —
it is **not** evidence that a live Claude response was ever exercised in this
environment. The gap between what's proven here and what would require a
configured `ANTHROPIC_API_KEY` is called out explicitly in the README's
Testing Summary and in `model_card.md`'s Evaluation section — this file
doesn't overstate what it shows.
