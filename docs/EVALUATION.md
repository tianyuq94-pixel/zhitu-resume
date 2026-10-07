# Verification notes

Updated: 7 October 2026. This document records engineering checks, not a claim of model accuracy or admissions / recruitment outcomes.

## Automated backend checks

Command: `python -m pytest -q` from `backend` with the development dependencies installed.

The 7 October 2026 run passed **94 tests**. Most AI responses are controlled test doubles, and database-backed tests use an isolated test database. Covered behaviours include:

- Guest identity reuse, user isolation, CSRF and private document access.
- Tool prerequisites, unexpected tool names, task revisions and failure recovery.
- Filtering cosmetic CV edits and preserving unchanged source content.
- PDF / Word exports, parser behaviour and bilingual responses.
- Persona response schema, invalid fact identifiers and contact disclosure only on request.

Relevant sources: `backend/tests/test_agent.py`, `test_meaningful_suggestions.py`, `test_custom_resume.py`, `test_persona.py`, `test_localisation.py` and `test_security.py`.

## Recorded real-model example

`frontend/public/demo/recorded-run.json` was produced by the actual local application and a real model API on 7 October 2026. Its CV describes **Alex Morgan**, Example University and Example Company, all fictional. Only synthetic material was submitted. `alex@example.com` is a demonstration address.

The recorded sequence is job analysis, CV tailoring, interview preparation and finish. Corresponding PDF and editable Word files are in the same directory. Unnecessary local database identifiers were removed from the public record; answer text is preserved.

The example deliberately contains a job requirement, PostgreSQL, without matching CV evidence. The saved response recognises the gap. In this execution no CV rewrite passed the meaningful-change filter, so the export retains the original wording. The UI explains that outcome instead of manufacturing a before / after improvement.

A first capture attempt stopped at a failed preparation step. A subsequent execution completed. This demonstrates why failures and retries need explicit handling; it is not evidence of a quantified reliability rate. The sample timing, if present in the raw record, is one local run and must not be treated as a speed guarantee.

The public example is static and labelled read-only. It does not invoke the model, create a guest session or write to a visitor's CV. The saved output remains English when interface labels are switched to Chinese, preserving the recorded evidence.

## Browser checks

The portfolio review checks fresh-visitor routes, English / Chinese switching, responsive layouts, sample tabs, error and retry handling, local resource links and download signatures. The live toolkit should create a guest session without a login form; if its service is unavailable, the login screen retains a link to the independent recorded example.

Run `node scripts/check_portfolio.cjs` with Playwright installed and a local frontend running. `TEST_BASE` selects the site; `PLAYWRIGHT_MODULE` and `BROWSER_EXECUTABLE` can point to an existing runtime. The suite exercises five public pages in two languages at three viewport widths (30 combinations), keyboard-accessible sample tabs, language persistence, download signatures and fetch retry. Authentication service responses are mocked for repeatable guest-entry / outage checks; the public pages are also asserted to make zero API requests. This is not a load or penetration test.

## What these checks do not establish

- They are not a systematic evaluation across different CVs, languages and occupations.
- No applicant employment outcome, user study or comparison against a baseline has been established.
- String / schema checks do not establish semantic truth, fairness or absence of hallucinations.
- Fact IDs in Persona responses check referenced identifiers, not sentence-by-sentence entailment.
- Exactly-once execution across all tool writes is not guaranteed.

## Proposed next evaluation

Create a versioned set of synthetic CV / role pairs, including sparse CVs and missing evidence. Compare the current workflow with a simpler prompt baseline. Define a review rubric for supported claims, useful changes, role relevance, latency and failure recovery. Report sample size, failures and human judgement alongside results. This is a proposed next step, not work already completed.
