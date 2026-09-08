---
name: modern-python
description: Use when setting up modern Python tooling with uv, ruff, ty, and pytest for Python 3.12+ projects.
---

# Modern Python

## When to Use This Skill
- Setting up a new Python project with modern tooling
- Migrating from pip/poetry to uv for package management
- Configuring ruff for linting and formatting
- Setting up ty for type checking

## Workflow
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Init project: `uv init` — creates `pyproject.toml`
3. Add dependencies: `uv add <package>`
4. Install ruff: `uv add --dev ruff`
5. Configure ruff in `pyproject.toml`: set line-length, target-version, and rules
6. Lint: `uv run ruff check .` and format: `uv run ruff format .`
7. Install ty: `uv add --dev ty`
8. Type check: `uv run ty check`
9. Test: `uv run pytest`

## Rules
- Use uv instead of pip, pip-tools, poetry, or conda for dependency management
- Use ruff instead of flake8, isort, black, or pyupgrade
- Use ty instead of mypy for type checking
- Keep `pyproject.toml` as the single source of truth for project config
- Run linters and type checks in CI, not just locally
