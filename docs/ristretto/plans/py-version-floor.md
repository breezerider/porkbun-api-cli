# py-version-floor — Bump supported Python range to 3.11–3.14

## Spec
- Source: idea
- Flight: build-modernization
- Goal: `requires-python` and all test/CI surfaces target only non-EOL Pythons (3.11–3.14), py3.13 as local default.

## Contract
- Acceptance:
  - [auto] `requires-python` in `pyproject.toml` equals `>=3.11`.
  - [auto] `tox.ini` `envlist` includes exactly `{py311,py312,py313,py314}` (plus `clean,check,docs,report`); no `py38`/`py39`/`py310` remain.
  - [auto] Every `basepython` mapping in `[testenv]` resolves py311→python3.11, py312→python3.12, py313→python3.13, py314→python3.14, and `clean,check,docs,report`→python3.13 (or env override).
  - [auto] `.github/workflows/github-actions.yml` matrix covers py311, py312, py313, py314 across ubuntu/windows/macos × x64/arm64 (12 test cells + check + docs); no py38/39/10 rows remain.
  - [auto] `cibw_build` keys and the cibw job step are removed (all entries were `cibw_build: false` — dead config).
  - [auto] `check` and `docs` CI jobs use python 3.13 (was 3.11).
  - [auto] `tox -e py313` exits 0; `tox -e py314` exits 0.
  - [auto] `python3.11 -m tox -e py311` exits 0 (python3.11 binary present at `/usr/bin/python3.11`).
  - [auto] `black`/`ruff`/`isort` `target-version` equals `py311` (which survives this feature; ruff/isort/black config is #2's contract, but any `target-version` field touched here aligns to py311).
  - [auto] `docs/ristretto/roadmap.md` and `AGENTS.md` "Python version mismatch" note reflect 3.11–3.14 (no stale py3.8/3.10/3.13-vs-CI-mismatch wording).
- Provides: Python version floor 3.11; tox env set {py311,py312,py313,py314}; py3.13 as `clean/check/docs/report` basepython; CI matrix py311–py314.
- Consumes: —
- Decisions:
  - Floor version → 3.11 (non-EOL, LTS-distros, skill 3.12+ is tooling-capability not floor mandate).
  - py313 → local default (only fully-functional interpreter for check/docs/report; CI matrix still tests 3.11/3.12).
  - cibw dead config → delete (no entry had `cibw_build: true`; `cibuildwheel` step unreachable).
  - `check`/`docs`/`coverage` jobs python → 3.13 (align with local default; was 3.11).
- Units:
  - Bump `requires-python` in `pyproject.toml` to `>=3.11`; update `target-version` in `[tool.black]` to `py311`.
  - Rewrite `tox.ini` envlist to `{py311,py312,py313,py314}` + basepython mappings.
  - Rewrite `.github/workflows/github-actions.yml` matrix to py311–py314 × 3 OS, drop cibw keys + step, bump check/docs jobs to 3.13.
  - Update `AGENTS.md` gotchas: replace "Python version mismatch" bullet with accurate 3.11–3.14 statement.
- Manual-Checks: —
- Blockers: —

## Approach
Tier: normal

Four-file mechanical migration, no behavior change. `requires-python` is the keystone — CI matrix and tox envlist must match it exactly or the claim is false. cibw removal is cleanup of already-dead config (every entry set `cibw_build: false`), not a feature loss.

Likely touchpoints: `pyproject.toml`, `tox.ini`, `.github/workflows/github-actions.yml`, `AGENTS.md`.

Strategy:
1. `requires-python` → `>=3.11`; `[tool.black] target-version = ['py311']`.
2. tox envlist: `clean,check,docs,{py311,py312,py313,py314},report`. Add `py312` basepython mapping alongside existing py311/py313/py314. `skip_missing_interpreters = true` already set — py312 env skips locally (no `/usr/bin/python3.12`), passes in CI.
3. CI matrix: replace 12 py38–py311 entries with py311–py314 × {ubuntu, windows, macos} × x64/arm64. Drop `cibw_build`, `cibw_arch`, `python_arch` for non-cibw rows and the `cibw build and test` + `check wheel` + `upload wheel` steps. Bump `check`/`docs`/`coverage` job python to `3.13`.
4. AGENTS.md: delete "Python version mismatch" bullet (mismatch resolved); add one-line accurate statement.

Local verification: `tox -e py311,py313,py314` all green; py312 skipped. CI matrix is source of truth for 3.12 (not locally installed).

- Depends: —
- Parallel-with: ruff-migration, ty-typecheck, uv-lockfile (all orthogonal to version range; #2/#3/#4 read this feature's `Provides:` for `target-version` but don't gate on it being merged first).

status: planned