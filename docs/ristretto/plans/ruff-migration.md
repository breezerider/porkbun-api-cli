# ruff-migration — Replace flake8+black+isort with ruff; consolidate config into pyproject

## Spec
- Source: idea
- Flight: build-modernization
- Goal: ruff is the only code-quality tool; all lint/format config lives in `pyproject.toml`; `pytest.ini` folds into `[tool.pytest.ini_options]`.

## Contract
- Acceptance:
  - [auto] `[tool.black]` and `[tool.isort]` sections absent from `pyproject.toml`.
  - [auto] `[flake8]` section absent from `tox.ini`.
  - [auto] `pytest.ini` absent; `pyproject.toml` contains `[tool.pytest.ini_options]` with `filterwarnings = ["error"]`, `--doctest-modules`, `--doctest-glob=*.rst`, `--import-mode=importlib`, `testpaths = ["tests"]`, `--strict-markers`, `-ra`, `--tb=short`, `norecursedirs = [...]`.
  - [auto] `pyproject.toml` contains `[tool.ruff]` with `line-length = 120`, `target-version = "py311"`.
  - [auto] `pyproject.toml` contains `[tool.ruff.lint]` with `select = ["E","F","I","B"]` and `ignore = ["E203","E501","E701"]` (not `extend-ignore` — deprecated in ruff).
  - [auto] `pyproject.toml` contains `[tool.ruff.format]` with `quote-style = "preserve"` and `preview = true`.
  - [auto] `pyproject.toml` contains `[tool.ruff.lint.isort]` with `force-single-line = true` (not `force-single-line-imports` — that key does not exist in ruff; the correct key is `force-single-line`).
  - [auto] `pyproject.toml` `[tool.ruff.lint.per-file-ignores]` contains `{"__init__.py" = ["F401"]}` and **no** `PT009`/`PT027` entries.
  - [auto] `tests/test_api.py` and `tests/test_cli.py` contain no `noqa: PT` comments and no `# noqa: PT009`/`PT027` lines; flake8-pytest-style ignores fully removed.
  - [auto] `[testenv:check]` `deps` pins `ruff` (versioned, not floating) and contains no `flake8*`, `black`, `isort`, `flake8-bugbear`, `flake8-pytest-style`.
  - [auto] `[testenv:check]` `commands` runs `ruff check .` then `ruff format --check --diff .` then `python setup.py check --strict --metadata --restructuredtext` then `check-manifest .`.
  - [auto] `ruff format .` has been applied to all files (blank-line-after-class, `click.Choice([...])` collapse, `'\n'.join([...])` collapse — ruff/black diverge on these 4 files); `ruff format --check --diff .` exits 0 afterward.
  - [auto] `tox -e check` exits 0.
  - [auto] `tox -e py313` exits 0 (doctests, warnings-as-errors still pass after pytest config move).
  - [auto] No `flake8`/`black`/`isort` pin versions remain in `tox.ini`.
  - [auto] `src/porkbun_api_cli/cli.py:178` `# noqa: E501, B950` comment replaced with `# noqa: E501` (B950 has no ruff equivalent; E501 remains ignored but explicit noqa kept for line-length safety if ignore is later removed).
- Provides: ruff as sole lint+format tool; `[tool.ruff.*]` config in pyproject; `[tool.pytest.ini_options]` in pyproject; `check` env runs `ruff check` + `ruff format --check`.
- Consumes: Python version floor 3.11 from py-version-floor (for `target-version = "py311"`).
- Decisions:
  - Drop PT (flake8-pytest-style) entirely → no `PT` in ruff `select`; per-file ignores for PT removed. Tests use unittest-style asserts by convention, no enforcement. Rationale: rules were pinned but 100% defeated by per-file ignores; enabling ruff's native PT only reproduces the dead state — rules on, all asserters ignored. Re-enable `PT` in a later feature if tests migrate to function-style.
  - `B950` → no ruff equivalent (confirmed: ruff 0.16.6 rejects `B950` as unknown selector). Select whole `B` family instead for bugbear coverage; `B950` was flake8-bugbear's "line too long with margin" proxy, ruff handles line-length via `E501` (ignored here, matching current behavior). `cli.py:178` noqa retargeted to `E501` only.
  - `quote-style = "preserve"` → equals `black skip-string-normalization = true`; single quotes stay valid.
  - `preview = true` → carries `black --preview` behavior forward (ruff format preview parity).
  - `force-single-line = true` → carries `isort force_single_line = true` quirk forward. Key is `force-single-line`, not `force-single-line-imports` (the latter does not exist in ruff and causes config-parse failure).
  - Bugbear coverage → select whole `B` family (ruff-implemented subset); `B950` not available, handled via `E501` ignore.
  - Keep `E203, E501, E701` in `ignore` (ruff deprecates `extend-ignore`; `ignore` is the supported key).
  - Keep `F401` per-file ignore on `__init__.py` → `__version__`-only module re-exports nothing but setuptools reads it; rule fires false-positive otherwise.
  - pytest.ini → `[tool.pytest.ini_options]` → single source of truth (modern-python skill rule). Same keys, same behavior; `pytest.ini` deleted.
  - ruff pinned version in `check` deps → not floating (was `flake8==7.0.0`, `black==24.3.0`, `isort==5.13.2`; pick current stable, e.g. `ruff==0.x.x` at pull time).
- Units:
  - Add `[tool.ruff]`, `[tool.ruff.lint]` (`select = ["E","F","I","B"]`, `ignore = ["E203","E501","E701"]`), `[tool.ruff.format]`, `[tool.ruff.lint.isort]` (`force-single-line = true`), `[tool.ruff.lint.per-file-ignores]` (only `{"__init__.py" = ["F401"]}` — no PT entries) to `pyproject.toml`; delete `[tool.black]`, `[tool.isort]`.
  - Move pytest config: `pytest.ini` → `pyproject.toml [tool.pytest.ini_options]`; delete `pytest.ini`.
  - Rewrite `[testenv:check]` in `tox.ini`: deps = `ruff==<pin>`, `docutils`, `check-manifest`, `readme-renderer`, `pygments`; commands = `ruff check .`, `ruff format --check --diff .`, `python setup.py check ...`, `check-manifest .`. Delete `[flake8]` section.
  - Scrub `tests/test_api.py` and `tests/test_cli.py` of any `PT009`/`PT027` noqa comments (none found inline — per-file-ignores removal in config handles it). Replace `cli.py:178` `# noqa: E501, B950` with `# noqa: E501`.
  - Run `ruff format .` to apply ruff formatting (4 files diverge from black: blank-line-after-class in `api.py`/`test_api.py`/`test_cli.py`, `click.Choice([...])` collapse + `'\n'.join([...])` collapse in `cli.py`/`test_cli.py`). After this, `ruff format --check .` passes.
- Manual-Checks: —
- Blockers: —

## Approach
Tier: normal

Mechanical config consolidation. ruff is a drop-in for flake8 (pyflakes + pycodestyle + bugbear) + isort + black formatter; all current settings map 1:1 to ruff keys. The only semantic loss is PT, which was already inert. pytest.ini → pyproject is a pure move (pytest reads `[tool.pytest.ini_options]` with same precedence).

Likely touchpoints: `pyproject.toml`, `tox.ini`, `pytest.ini` (delete), `tests/test_api.py`, `tests/test_cli.py` (only if inline noqa comments exist — grep found none in src except `cli.py:178` which stays).

Strategy:
1. Build `[tool.ruff.*]` mirroring current flake8+black+isort config (keys listed in Decisions). Add `target-version = "py311"` (from py-version-floor's `Provides:`).
2. Move pytest.ini contents to `[tool.pytest.ini_options]`, preserving `addopts` as a list. Delete `pytest.ini`.
3. Rewrite `[testenv:check]`: ruff replaces flake8+black+isort (one tool, two commands: `check` + `format --check`). Keep `setup.py check` (rst validation) + `check-manifest`. Update `MANIFEST.in` if `pytest.ini` removal affects it — it does (`include pytest.ini` line present) — drop that line.
4. Grep `tests/` for inline `# noqa: PT...` comments; remove any. Per-file-ignores config removal handles the blanket case. Replace `cli.py:178` `# noqa: E501, B950` with `# noqa: E501`.
5. **Apply `ruff format .`** — ruff and black diverge on 4 files (blank-line-after-class, `click.Choice([...])` collapse, `'\n'.join([...])` collapse). These must be reformatted by ruff before `ruff format --check --diff .` passes in `check`. This is a required step, not optional; skipping it makes criterion "tox -e check exits 0" unsatisfiable.

Local verification: `tox -e check` green (ruff clean on current code — it already passes flake8+black+isort), `tox -e py313` green (pytest config moved, behavior identical).

- Depends: py-version-floor (reads `target-version` from its `Provides:`; merging order: #1 first so py311 is decided, but #2 can be planned in parallel since the value is known).
- Parallel-with: ty-typecheck (#3 reads this feature's `check` env shape but lands separately), uv-lockfile.

status: planned