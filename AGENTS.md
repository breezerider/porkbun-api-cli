# AGENTS.md

Compact guide for OpenCode sessions working in this repo. Verified against current codebase.

## What this is

Python CLI (`porkbun-api-cli`) managing Porkbun DNS records from a YAML config. Click-based. Supports modes: `append`, `replace`, `update`, `upgrade`. Single package, src layout.

## Commands

- **All checks:** `tox` (runs clean, check, docs, {py311,py312,py313,py314}, report)
- **Lint only:** `tox -e check` (ruff check + ruff format --check + ty check + manifest + rst check)
- **Tests only:** `tox -e py313` (or py311/py312/py314; py313 is local default for clean/check/docs/report)
- **Single test:** `tox -e py313 -- pytest -k test_myfeature`
- **Parallel:** `tox -p auto`
- **Docs:** `tox -e docs` (sphinx-build into `dist/docs`)
- **Coverage report:** `tox -e report` (needs prior test run; `fail_under = 95`)
- **Type check only:** `uvx --from ty ty check src/porkbun_api_cli --python /usr/bin/python3.13` (or `tox -e check` runs it as a gate)
- **Reproducible env:** `uv sync` (creates `.venv/` from `uv.lock`; runtime + `[dependency-groups] dev` deps)

Do not run bare `pytest` expecting parity — `tox` sets PYTHONPATH, coverage flags, and env. Use tox envs.

## Gotchas

- **Warnings are errors.** `pyproject.toml [tool.pytest.ini_options]` sets `filterwarnings = ["error"]`. A deprecation warning fails the suite.
- **Doctests run.** `--doctest-modules` and `--doctest-glob=*.rst` are on (in `[tool.pytest.ini_options]`). Docstring examples and `.rst` snippets are executed as tests. Changing a docstring example breaks CI.
- **`delete` op is not implemented.** `cli.py` logs "not implemented - skipped" for staged deletes. `replace` mode plans deletes but never executes them. Don't assume replace actually removes records.
- **Interactive prompt.** Non-dry-run execution prompts `y/N` via `click.getchar()`. Tests must use `--dry-run` or stdin faking; see `tests/test_cli.py`.
- **Python versions 3.11–3.14 supported.** `requires-python>=3.11`. tox envlist `{py311,py312,py313,py314}`; py3.13 is the local default for `clean/check/docs/report`. CI matrix matches (py311–py314 × ubuntu/windows/macos). py3.12 not installed locally — `skip_missing_interpreters` skips that env; CI covers it.
- **Pinned tools.** `check` env pins `ruff==0.16.6` + `ty==0.0.79` (in `tox.ini` deps + `[dependency-groups] dev`). Unpinned installs may flag differently. ruff format `--preview` is on.
- **ruff isort quirk.** `[tool.ruff.lint.isort] force-single-line = true` — one import per line, no multi-line grouping. Replaces the old `[tool.isort]` config.
- **Type annotations enforced.** `check` env runs `ty check src/porkbun_api_cli` (blocking). `src/porkbun_api_cli/*.py` are fully annotated (TypedDicts in `utils.py`: `DnsRecord`, `ExistingDnsRecord`, `Operation`; `from __future__ import annotations` in all three src modules). `# type: ignore` and `typing.cast` are forbidden; `assert` + `# ty: narrow` comment is the permitted narrowing pattern. See `docs/ristretto/memos.md` for the deferred DTO refactor.
- **`uv.lock` is source of truth for deps.** `uv sync` creates `.venv/` from `uv.lock`; `[dependency-groups] dev` in `pyproject.toml` lists dev deps. `[project.optional-dependencies]` was deleted (dead template stubs); no extras declared. `importlib-metadata` conditional removed (dead under floor 3.11).

## Style (enforced by `check`)

- ruff: `line-length = 120`, `target-version = "py311"`, `quote-style = "preserve"` (single quotes fine), `preview = true` (format)
- ruff lint: `select = ["E","F","I","B"]`, `ignore = ["E203","E501","E701"]` (not `extend-ignore` — deprecated in ruff). `B950` has no ruff equivalent; whole `B` family selected instead. `cli.py:178` has `# noqa: E501` (retargeted from the old `# noqa: E501, B950`).
- ruff per-file-ignores: `{"__init__.py" = ["F401"]}` only. No `PT009`/`PT027` entries (flake8-pytest-style dropped — tests use unittest-style asserts, no enforcement).
- ty: `[tool.ty.environment] python-version = "3.11"` (NOT top-level `[tool.ty] python-version` — ty 0.0.79 rejects that as unknown field). `check` env uses `usedevelop = true` (not `skip_install = true`) so runtime deps resolve for ty.
- Run formatter before committing: `ruff format .` then `ruff check .` (check-only in CI will fail on diff).

## Layout

- `src/porkbun_api_cli/` — the package
  - `cli.py` — Click entrypoint, `main`; planning + execution loop
  - `api.py` — `PorkbunAPI` class, thin wrapper over Porkbun HTTP API (POSTs JSON)
  - `utils.py` — config loader (YAML), record comparators, mode→operation permission table, TypedDicts (`DnsRecord`, `ExistingDnsRecord`, `Operation`)
  - `__init__.py` — only `__version__` (consumed by setuptools via `tool.setuptools.dynamic`)
- `tests/` — `test_api.py`, `test_cli.py`, `test_utils.py`, `config.yml` fixture. Tests use unittest-style asserts (no PT enforcement).
- `ci/` — bootstrap script + requirements for CI runners
- `docs/` — Sphinx sources; built by `tox -e docs`
- `uv.lock` — reproducible dep graph (source of truth for `uv sync`)

Console script: `porkbun-api-cli` → `porkbun_api_cli.cli:main` (declared in `pyproject.toml [project.scripts]`).

## Config format (YAML input)

```yaml
api:
  endpoint: https://...
  apikey: ...
  secretapikey: ...
domains:
  - name: example.com
    records:
      - {name: "", type: A, content: 1.2.3.4}
```

`load_config` in `utils.py` is the validator — required keys: `api`, `api.apikey`, `api.secretapikey`. `domains` optional (defaults to []).

## Release

- Versioning via `tool.bumpversion` in `pyproject.toml`. Bump updates `src/porkbun_api_cli/__init__.py`, `CHANGELOG.rst`, `README.rst`, commits, and signs tag `v{version}`.
- Tag push (`refs/tags/v*`) triggers `upload_pypi` job → publishes to **test.pypi.org** (not real PyPI; uses `PIPY_TEST_TOKEN` secret). Do not assume releases hit production PyPI.