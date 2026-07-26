# Model Card — PawPal+ AI Care Assistant

This model card documents the AI component added to PawPal+ (`CareAgent` in
`ai_agent.py`, paired with the retriever in `care_knowledge.py`). It covers the
system itself, how it was built in collaboration with an AI coding assistant
(Claude Code), and — per the assignment's responsible-AI reflection
requirement — a specific helpful suggestion, a specific flawed suggestion, and
this system's known limitations.

## Model / System Details

- **Underlying LLM:** Claude (`claude-opus-4-8`, Anthropic API), called via the
  `anthropic` Python SDK with a JSON-schema-constrained request
  (`output_config.format`).
- **Task:** given a pet's profile (species, breed, preferred time of day,
  medications) and its existing schedule, retrieve relevant care guidelines
  and draft 1–3 new care tasks grounded in that retrieved text, then adjust
  drafted due times to avoid conflicting with the pet's existing tasks.
- **Retrieval:** exact whole-word keyword scoring over a small, hand-authored
  local knowledge base (`care_knowledge.CARE_GUIDELINES`, ~10 short
  documents) — no embeddings, no external index, no network call for the
  retrieval step itself.
- **Fallback:** if the API key is missing, the call fails, or the model
  refuses, the system falls back to a deterministic draft built from the same
  retrieved guidelines' templates. This is not an edge case to be tolerated —
  it's a first-class code path exercised by its own tests.
- **Guardrails:** every drafted task (from either path) is validated for
  duration bounds, allowed priority/frequency values, and parseable due times
  before it becomes a real `Task` object; invalid fields are dropped and
  logged, never silently accepted.
- **Human-in-the-loop:** drafted tasks are only ever previewed. A person must
  click "Add these tasks" before anything changes the pet's real schedule.

## Intended Use

- A brainstorming/starting-point tool for a pet owner setting up a care
  routine, surfaced alongside the sources it drew from so the suggestion is
  checkable, not a black box.
- A demonstration of a fully-integrated RAG + agentic pipeline (retrieval
  actively shapes generation; the agent self-corrects against real
  application state) for a course assignment.

## Out-of-Scope Use

- **Not veterinary advice.** The knowledge base is a small set of
  general-purpose guidelines written by the developer for this project, not
  reviewed by a veterinary professional, and not tailored to any individual
  pet's actual health history. Medication timing, dosage, or any
  health-related suggestion from this system should always be verified with
  an actual veterinarian.
- Not intended for emergency care decisions, diagnosis, or any use where an
  incorrect suggestion could cause harm to an animal.

## How I Collaborated With AI

This feature was built with Claude Code doing the implementation work
(architecture, code, tests, diagram, docs) while I made the decisions Claude
Code surfaced as explicit trade-offs rather than deciding silently — notably,
which AI-feature category to build (RAG vs. a pure agentic workflow vs. a
reliability/testing system) and whether to require a live API key or design
around an offline fallback from the start. I reviewed each file as it was
written rather than accepting the summary at the end, and asked for the
retrieval scoring and conflict-resolution logic specifically because those
were the parts most likely to be silently wrong in a way that "looks right"
in a quick demo.

### A helpful AI suggestion

When implementing the agentic conflict-resolution step, Claude Code chose to
call the *existing* `Scheduler._windows_overlap()` / `_task_time_windows()`
static methods (already used by the original project's `get_conflicts()`)
instead of writing new overlap-detection code for the AI agent. I hadn't
asked for this explicitly — I only asked for "avoid scheduling the new tasks
on top of existing ones." Reusing the existing method was the right call: it
guarantees the AI agent and the human-facing conflict warnings in the
Streamlit UI can never disagree about what counts as a conflict (including
the trickier midnight-spanning case the original project already handled),
and it avoided a second, slightly-different implementation of the same logic
existing anywhere in the codebase.

### A flawed AI suggestion

The first version of `retrieve_guidelines()` scored a guideline as a match if
any of its keywords appeared as a **substring** of a pet's profile terms in
*either direction* (`keyword in term or term in keyword`). This looked
reasonable in the code and passed a casual read-through, but it was wrong:
for a Golden Retriever, the profile term `"golden"` contains the substring
`"old"` — which is also a keyword for the unrelated senior-pet guideline. The
result was that any Golden Retriever's suggestions were silently influenced
by senior-care guidance regardless of the dog's actual age. I didn't catch
this by reading the code; a test written specifically to assert "a dog's
retrieved guidelines should only be dog-related" failed immediately and
pointed straight at the bug. The fix (`care_knowledge.py`) was to switch to
exact whole-word matching against a term set, which is both more correct and
simpler than the substring version it replaced. The lesson generalizes: an AI
assistant's code can look locally reasonable — clean, readable, seemingly
doing what was asked — while still being subtly wrong in a way that only
shows up under a test built to check the *intent*, not just "does it run."

## Evaluation

- 30 automated tests (`pytest`), 13 of which target this AI layer directly:
  retrieval relevance across species and for a medicated pet, retrieval on a
  blank profile, draft validation (accept/reject/default cases), conflict
  nudging (conflicting and non-conflicting cases), and two end-to-end tests
  of the full offline-fallback pipeline.
- **Not yet evaluated:** the live-LLM response path is not exercised against
  a mocked `anthropic` client, so malformed-JSON handling and the
  `stop_reason == "refusal"` branch are covered structurally (the code exists
  and is simple) but not asserted against a simulated real response.
- Manually verified end-to-end via `python main.py` (logs correctly, produces
  conflict-free suggestions) and `streamlit run app.py` (loads and runs with
  no server-side exceptions).

## System Limitations

- **Unvetted knowledge base.** The care guidelines are illustrative,
  hand-written for this project, and not reviewed by a veterinary
  professional — see *Out-of-Scope Use* above.
- **Keyword retrieval, not semantic retrieval.** Matching is exact whole-word
  overlap; a profile term that's a synonym or a novel phrasing of a keyword
  (e.g. "senior" vs. "elderly") won't retrieve the relevant guideline. The
  substring-matching bug described above was a direct consequence of trying
  to work around this limitation carelessly.
- **Deterministic tie-breaking can drop relevant guidelines.** `top_k=3` with
  alphabetical tie-breaking on equal score means a guideline that's just as
  relevant as three others can be silently excluded — demonstrated in the
  README's third sample interaction, where a medication guideline for a
  senior, medicated dog narrowly loses out to two generic dog guidelines.
- **Structural validation only, not factual validation.** `_validate_draft()`
  checks that a duration is in bounds and a priority/frequency value is
  allowed — it cannot check whether a drafted task is *actually* good advice
  for the specific pet. A schema-valid task can still be substantively wrong.
- **Conflict resolution only shifts time, blindly.** `_resolve_conflicts()`
  nudges a due time forward in 30-minute steps to clear a collision without
  any judgment about whether the new time still makes sense (e.g. it could in
  principle nudge a task into the middle of the night if enough existing
  tasks were packed together); it gives up and logs a warning after a fixed
  number of attempts rather than escalating further.
- **No date-aware scheduling.** Like the original project, the AI layer
  drafts tasks onto a repeating weekly template rather than actual calendar
  dates, so it has no way to account for one-off exceptions (e.g. a lighter
  schedule around a holiday or a vet visit).
- **Single-session, single-user.** There's no persistence beyond a Streamlit
  session and no authentication — not designed for multi-user or production
  deployment as-is.
