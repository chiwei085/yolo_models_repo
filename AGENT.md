# AGENT.md — Repo Conventions (for Codex/agents)

This repository prioritizes reproducible tooling, clean Python, and explicit conventions.
Follow these rules when adding or modifying code.

## Python tooling: Ruff-first workflow
- Use **Ruff** as the single source of truth for:
  - linting
  - import sorting
  - formatting
- Do **not** add Black/isort/flake8 separately unless explicitly requested.

**Commands (preferred):**
- `uv run ruff check .`
- `uv run ruff format .`
- When reasonable, apply fixes:
  - `uv run ruff check . --fix`

**Policy:**
- Keep the codebase consistently formatted by Ruff.
- Keep imports sorted by Ruff (no manual isort config).

## Type hints: modern, Python 3.12+ style
- Target **Python 3.12**.
- Use **modern typing style**, avoid legacy patterns:
  - Prefer built-in generics: `list[str]`, `dict[str, int]` (not `List[str]`, `Dict[...]`)
  - Prefer `X | Y` (PEP 604 unions) instead of `Optional[X]` or `Union[X, Y]` where applicable
  - Default: do not add `from __future__ import annotations`
  - Only use it when real forward references require it
  - Prefer `Path` from `pathlib` over raw strings for filesystem paths
- Use `typing` only when needed (e.g. `TypedDict`, `Protocol`, `Literal`, `TypeAlias`, `Self`).
- Keep annotations **useful** and **readable**:
  - annotate public functions, CLI entrypoints, and return types
  - don’t over-annotate trivial locals if it hurts readability
- If the code would benefit from structure, use:
  - `@dataclass(slots=True)` for small data containers
  - `TypedDict` for JSON-like dict shapes

## Git commit message style: bracketed subsystem prefix
Use a Linux-kernel-like style with an explicit subsystem in brackets.

**Format:**
- `[subsystem] imperative summary`
- Summary line:
  - imperative mood (“add”, “fix”, “refactor”, “remove”, “document”)
  - <= 72 characters (best effort)
  - no trailing period

**Examples:**
- `[tools] add YOLOv8 ONNX export CLI`
- `[export] fix opset selection for OpenCV DNN compatibility`
- `[docs] document uv + ruff workflow`
- `[ci] tighten ruff rules and fail on lint`

**Body (optional but recommended for non-trivial changes):**
- Explain *why* the change is needed, not just *what* changed.
- Wrap at ~72 columns.
- If relevant, include reproduction steps or before/after behavior.

## General implementation expectations
- Prefer small, composable functions over monolithic scripts.
- Be explicit about paths: resolve repo root relative to the file location.
- Fail fast with clear error messages and non-zero exit codes in CLI tools.
- Avoid hidden global state; avoid magic environment assumptions.
- Keep dependencies minimal and justified in `pyproject.toml`.
