# uv-lockfile — Add uv.lock; prune dead extras, dead conditional dep; use [dependency-groups]

## Spec
- Source: idea (folded from `drop-optional-deps` + original `uv-lockfile`)
- Flight: build-modernization
- Goal: `uv.lock` pins the full dependency graph for reproducible installs across local + CI; `uv sync` produces a working `.venv` with runtime + dev deps; dead `[project.optional-dependencies]` (`pdf`/`rest`) and dead `importlib-metadata` conditional removed; dev deps declared via `[dependency-groups] dev` (not the deprecated `[tool.uv] dev-dependencies`).

## Contract
- Acceptance:
  - [auto] `uv.lock` exists at repo root, tracked in git.
  - [auto] `uv.lock` resolves all runtime deps (`click`, `pyyaml`, `requests`) + dev deps from `[dependency-groups] dev` (`pytest`, `pytest-cov`, `ruff==0.16.6`, `ty==0.0.79`, `types-PyYAML`, `types-requests`, `docutils`, `check-manifest`, `readme-renderer`, `pygments`, `coverage`, `sphinx>=1.3`, `sphinx-rtd-theme`, `sphinx-click`, `tox`) to concrete versions.
  - [auto] `pyproject.toml` contains no `[project.optional-dependencies]` section (both `pdf` and `rest` extras deleted — zero consumers, `rest` was self-contradictory, `pdf` referenced unresolvable `RXP`; see Decisions).
  - [auto] No `ReportLab`, `RXP`, `pack ==1.1`, `pack ==1.3` strings remain in `pyproject.toml`.
  - [auto] `pyproject.toml` `[project.dependencies]` contains no `importlib-metadata` entry (conditional `python_version<"3.10"` is dead under floor 3.11 from py-version-floor).
  - [auto] `pyproject.toml` contains no `[tool.uv]` section (deprecated `dev-dependencies` form not used).
  - [auto] `pyproject.toml` contains `[dependency-groups]` with `dev = [...]` listing the dev deps above.
  - [auto] `uv sync` exits 0 and creates `.venv/` with `click`, `pyyaml`, `requests` importable (`python -c "import click, yaml, requests"` succeeds in the venv).
  - [auto] `uv sync` installs dev deps: `ruff --version`, `pytest --version`, `ty --version` succeed in the venv.
  - [auto] `.gitignore` ignores `.venv/` (verify line present; add if absent).
  - [auto] `tox -e py313` exits 0 after lockfile generation (tox ignores `.venv/`, uses its own `.tox/` — confirms no drift; tests pass unchanged).
  - [auto] `tox -e check` exits 0 after lockfile generation (ruff + ty + setup check + check-manifest pass with merged pyproject).
  - [auto] `uv lock --check` exits 0 (lockfile is up-to-date with pyproject after generation).
- Provides: `uv.lock` (reproducible dep graph); `[dependency-groups] dev` in pyproject; `.venv/` workflow via `uv sync`; `pyproject.toml` with no `[project.optional-dependencies]` section, no `importlib-metadata`, no `[tool.uv]`.
- Consumes: Python floor 3.11 from py-version-floor (lockfile resolves against floor; `importlib-metadata` conditional becomes dead); ruff + ty deps from ruff-migration + ty-typecheck (dev-group list reflects what `check` + `docs` envs need).
- Decisions:
  - Delete both `pdf` and `rest` extras entirely (folded from `drop-optional-deps`). Evidence: (a) zero consumers — no `import reportlab`, no `import pack`, no `pip install .[pdf]`/`.[rest]`, no CI/tox/docs reference (grep-verified); (b) `rest` is self-contradictory (`pack ==1.1, ==1.3` demands two incompatible versions — unsatisfiable by any resolver, never could have installed); (c) `pdf` references `RXP`, absent from PyPI; (d) repo is alpha on test.pypi.org, zero evidence of PDF/REST output features; (e) upstream cookiecutter-pylibrary template (the repo's origin) ships only a commented `# rst = ["docutils>=0.11"]` hint — the author's uncommented `pdf`/`rest` mutation was never wired to anything (verified via git history + template comparison).
  - Do not preserve a commented extras example. The template's commented `# rst = ["docutils>=0.11"]` is not part of this repo's contract; adding it back is speculative scaffolding. If a future feature needs an extra, it declares one then.
  - Remove `importlib-metadata; python_version<"3.10"` from `[project.dependencies]` (originally in py-version-floor's scope per its plan's Units, but that feature landed without removing it — confirmed present at pyproject.toml:39 post-pull). Conditional is unreachable under `requires-python>=3.11`. This feature owns the removal because it affects the lockfile's dep graph.
  - dev-deps location → `[dependency-groups] dev` in `pyproject.toml` (PEP 735, uv-native). NOT `[tool.uv] dev-dependencies` — that form is legacy in uv 0.12.9 (`--upgrade-group dev` still satisfies it for back-compat, but uv docs route new projects to `[dependency-groups]`; verified: `uv lock` + `uv sync` both work with `[dependency-groups] dev` on uv 0.12.9).
  - dev-group membership → enumerates what `tox -e check`, `tox -e py313`, `tox -e docs`, `tox -e report` need (pulled from tox.ini deps lines): runtime test deps (`pytest`, `pytest-cov`), check deps (`ruff==0.16.6`, `ty==0.0.79`, `types-PyYAML`, `types-requests`, `docutils`, `check-manifest`, `readme-renderer`, `pygments`), coverage (`coverage`), docs (`sphinx>=1.3`, `sphinx-rtd-theme`, `sphinx-click`), + `tox` itself (so `uv sync` then `tox` works from the venv). Pinned versions match tox.ini where tox pins them (`ruff==0.16.6`, `ty==0.0.79`); rest unpinned (tox.ini doesn't pin them).
  - `.venv/` → ignored by `.gitignore` (verify, add if absent). Standard Python `.gitignore` usually has it — check, don't assume.
  - CI integration → **out of scope.** CI continues using `ci/requirements.txt` + `tox`. Migrating CI to `uv sync` is a separate feature (if ever wanted); this feature's contract is the lockfile + local workflow.
  - `uv.lock` python version → locked against 3.13 (local default) with `requires-python>=3.11` ensuring compatibility across 3.11–3.14. uv generates a multi-version lock by default.
  - `uv sync --extra rest` criterion from original plan → removed. That criterion referenced the `rest` extra this feature deletes. It was a stale reference to the dead extra; no replacement needed.
  - Do not duplicate runtime deps (`click`/`pyyaml`/`requests`) in the dev group. `uv sync` installs `[project.dependencies]` + `[dependency-groups] dev` automatically; runtime deps come from `[project.dependencies]`, dev deps from the group. Duplicating them in `dev` would be noise.
- Units:
  - Delete `[project.optional-dependencies]` section (lines 62-64: header + `pdf` + `rest`) from `pyproject.toml`.
  - Remove `importlib-metadata; python_version<"3.10"` line from `[project.dependencies]` in `pyproject.toml`.
  - Add `[dependency-groups]` with `dev = [...]` (listing the dev deps above) to `pyproject.toml`. Do NOT add `[tool.uv]`.
  - Verify `.gitignore` has `.venv/`; add if absent.
  - Run `uv lock` to generate `uv.lock`; commit it.
  - Run `uv sync` to confirm `.venv/` builds, runtime deps import, dev tools runnable; run `tox -e py313` + `tox -e check` to confirm no drift.
- Manual-Checks: —
- Blockers: —

## Approach
Tier: normal

Plumbing + dead-config cleanup. uv 0.12.9 already installed. Four edits to `pyproject.toml` (delete optional-deps section, delete importlib-metadata line, add `[dependency-groups]`, nothing else), one `.gitignore` verify, one generated file (`uv.lock`), one verification round (`uv sync` + tox).

Likely touchpoints: `pyproject.toml` (3 edits), `uv.lock` (new, generated), `.gitignore` (verify/add `.venv/`).

Strategy:
1. Delete `[project.optional-dependencies]` section (3 lines: header + `pdf` + `rest`). Run `tox -e check` — ruff format may collapse surrounding blank lines; let it.
2. Remove `importlib-metadata; python_version<"3.10"` from `[project.dependencies]` (one line).
3. Add `[dependency-groups] dev = [...]` with the dev deps listed in Decisions. Place it after `[project.scripts]` or near `[tool.*]` sections — TOML section order doesn't matter to uv, follow ruff format preference. Do NOT add `[tool.uv]`.
4. Verify `.gitignore` contains `.venv/`; add the line if missing.
5. `uv lock` generates `uv.lock` against `requires-python>=3.11`, multi-version resolution (uv default). Commit the lockfile — it's the reproducibility artifact.
6. `uv sync` creates `.venv/` from the lock. Verify: `python -c "import click, yaml, requests"` (runtime), `ruff --version` + `pytest --version` + `ty --version` (dev tools). Then `tox -e py313` + `tox -e check` (tox ignores `.venv/`, uses its own `.tox/` — confirms the lockfile is consistent with what tox resolves, no drift).

Verified against uv 0.12.9 in a scratch project: `[dependency-groups] dev` with 15 deps → `uv lock` resolved 56 packages, `uv sync` installed runtime + dev deps, all dev tools runnable. No `[tool.uv]` needed.

- Depends: py-version-floor (done — floor 3.11 makes `importlib-metadata` dead), ruff-migration (done — `ruff==0.16.6` pin carried into dev-group), ty-typecheck (done — `ty==0.0.79` pin + `types-PyYAML`/`types-requests` carried into dev-group). All three landed; this feature is the last in the flight.
- Parallel-with: —

status: planned