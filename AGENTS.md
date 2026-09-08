# Repository Guidelines

ProgressAgent is a personal, self-evolving learning system that prepares a job seeker for Agent application development roles. Assets in this repo are as important as code; change them deliberately and keep them truthful.

## Project Structure & Module Organization

- `abilities/` — versioned capability model (JSON + README).
- `jd_library/` — real JD corpus (`approved/`, `candidates/`) and aggregated market profiles.
- `app/src/progress_agent/` — Python CLI: `assess` (self-assessment) and `gap` (baseline gap analysis).
- `app/tests/` — stdlib `unittest` tests for CLI logic.
- `docs/`, `plans/`, `training/` — product design, weekly plans, and day-by-day hands-on exercises.
- `data/` — runtime reports (gitignored).
- `projects/` — user-built practice projects, e.g. `mini-agent/`.

## Build, Test, and Development Commands

No build step; CLI is pure Python 3.12+ standard library.

- Run self-assessment: `cd app && PYTHONPATH=src python3 -m progress_agent assess`
- Run gap analysis: `cd app && PYTHONPATH=src python3 -m progress_agent gap --assessment ../data/reports/<file>.json`
- Run unit tests: `cd app && PYTHONPATH=src python3 -m unittest discover -s tests -v`
- Run a training exercise: `python3 training/day2-error-recovery/agent.py "上海天气怎么样？"`

## Coding Style & Naming Conventions

- Python: type hints on public functions, `dataclasses` for models, UTF-8 throughout, Chinese comments/content are expected.
- Asset filenames carry versions, e.g. `agent-app-developer.v0.1.json`, `market-weights.v0.1.json`.
- JD files use `jd-YYYY-MMDD-NNN` ids and `NNN-公司-职位.md` filenames; every JD has a status (`candidate` / `approved` / `dropped` / `stale`).
- Validate JSON after edits: `python3 -m json.tool <file>`.
- Use `ruff` for formatting/linting when available; keep CLI dependency-free.

## Testing Guidelines

- Framework: stdlib `unittest`; tests live in `app/tests/test_*.py` and describe behavior via `test_...` names.
- Tests must be offline and never require an API key; LLM calls are mocked.
- Cover scoring edges (0–4 validation, weakest-item ordering, urgency math) and model shape (6 dimensions, 31 items).

## Commit & Pull Request Guidelines

- Repo history is minimal; use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `training:`.
- PRs must state what changed, why, and how it was verified (commands + output).
- Capability/JD asset changes require user approval before merge; no automatic merges.

## Agent Workflow Notes

- Coaching mode: provide scaffolds, hints, and review; never hand over finished solutions for learner TODO tasks, and never inflate the learner's real level.
- Read `training/NEXT.md` at the start of every session to know the learner's current task and where to continue.
- After each completed day, append a summary section to that day's README under `training/`, then update `training/README.md` and `training/NEXT.md`.
- Commit the completed day's changes with a Conventional Commit message (e.g. `training: complete day N ...`).
- Use real data (assessment/gap reports) rather than impressions when measuring progress.
