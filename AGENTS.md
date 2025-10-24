# Repository Guidelines

## Project Structure & Module Organization
- `main.py` boots the Telethon user and bot clients, wires schedulers, and can spawn the FastAPI-based RSS server under `rss/`.
- Message handling spans `handlers/`, `filters/`, and `managers/`, with shared helpers in `utils/` and enumerations in `enums/`.
- Data access lives in `models/` (SQLAlchemy) and runtime `db/` artifacts, while scheduling logic sits in `scheduler/`; AI providers stay in `ai/`.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` — establish a Python 3.11 environment consistent with the Docker image.
- `pip install -r requirements.txt` — install Telethon, FastAPI, and provider dependencies.
- `python main.py` — run the forwarder locally with `.env` secrets; logs stream to stdout and `./logs/`.
- `docker compose run -it telegram-forwarder` handles the initial login, followed by `docker compose up -d` for detached operation.
- `docker compose down && docker compose pull && docker compose up -d` refreshes a deployment without rebuilding.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation, concise module docstrings, and type hints matching current async signatures.
- Prefer snake_case for functions and variables, PascalCase for classes, and keep Telethon client instances suffixed `_client`.
- Log through `utils.log_config.setup_logging()` defaults; prefer structured `logger` calls over `print`.
- Sort imports and keep sections (<stdlib>, third-party, local) distinct to match existing modules.

## Testing Guidelines
- No automated suite ships today; add lightweight `pytest` cases under `tests/` when possible, or extend nearby integration helpers.
- Before opening a PR, run `python main.py`, trigger message forwarding, verify scheduled summaries, and hit RSS endpoints when enabled.
- Watch `./logs/` and `./db/` for regressions; clear stale scratch files in `./temp/` between manual runs.

## Commit & Pull Request Guidelines
- Match the existing Conventional Commit style (`fix(scheduler): ...`, `feat: ...`), keeping scopes aligned with top-level packages.
- Provide succinct PR descriptions with motivation, approach, and rollout notes; include config diffs or screenshots when behavior changes.
- Link issues and call out schema or config migrations (e.g., updates in `models/` or `config/`); bump `version.py` for user-facing changes.
- Document test evidence or state why automation is skipped, and highlight secrets or webhook updates reviewers must prepare.
