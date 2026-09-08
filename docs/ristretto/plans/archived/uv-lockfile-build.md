# uv-lockfile — Build Plan

tier: normal

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

## uv toolchain verification

Verified against `uv 0.12.9` (`uv --version` → `uv 0.12.9 (x86_64-unknown-linux-gnu)`, `/usr/bin/uv`):

1. `[dependency-groups] dev = [...]` accepted by `uv lock` — tested with a minimal tmp `pyproject.toml` at `/tmp/opencode/uv-test-pp/pyproject.toml` containing `[dependency-groups] dev = ["ruff==0.16.6", "ty==0.0.79", "pytest", ...]` (15 deps). `uv lock --python 3.13` → `Resolved 56 packages in 274ms`, exit 0.
2. Full real-world copy of `pyproject.toml` (with dead extras deleted, `importlib-metadata` removed, `[dependency-groups] dev` added after `[project.scripts]`) + copied `src/`, `README.rst`, `CHANGELOG.rst`, `MANIFEST.in` → `uv lock --python 3.13` → `Resolved 56 packages in 939ms`, exit 0. Lock contains 56 `[[package]]` entries across the full graph.
3. `uv sync --python 3.13` on that tmp copy → installs 53 packages (runtime + dev + transitive), exit 0. `.venv/bin/python -c "import click, yaml, requests"` → `runtime ok`. `.venv/bin/ruff --version` → `ruff 0.16.6`. `.venv/bin/pytest --version` → `pytest 9.1.1`. `.venv/bin/ty --version` → `ty 0.0.79`. All succeed.
4. `uv lock --check` on the generated lock → `Resolved 56 packages in 0.99ms`, exit 0.
5. `tox -e py313` on the real working tree (unmodified) → `76 passed, 7 subtests passed`, `95.86%` coverage, `py313: OK`, exit 0. tox uses `.tox/py313/` venv, ignores `.venv/`. No drift.
6. `tox -e check` on the real working tree (unmodified) → `check: OK` (ruff + ty + setup check + check-manifest), exit 0.

**No spec gaps found.** The contract's config shape (`[dependency-groups] dev`, no `[tool.uv]`, dead extras deleted, `importlib-metadata` removed) is accepted by uv 0.12.9 and resolves cleanly.

## Touchpoints

### 1. `pyproject.toml` — 3 edits (delete extras, remove importlib-metadata, add dependency-groups)

**Current state — `[project.dependencies]` (lines 35-40):**

```toml
35: dependencies = [
36:     "click",
37:     "pyyaml",
38:     "requests",
39:     'importlib-metadata; python_version<"3.10"',
40: ]
```

**Edit 1 — remove line 39** (`'importlib-metadata; python_version<"3.10"'`). Result:

```toml
dependencies = [
    "click",
    "pyyaml",
    "requests",
]
```

**Current state — `[project.optional-dependencies]` (lines 62-64):**

```toml
62: [project.optional-dependencies]
63: pdf = ["ReportLab>=1.2", "RXP"]
64: rest = ["docutils>=0.3", "pack ==1.1, ==1.3"]
```

This block sits between `[tool.setuptools.dynamic]` (line 59-60) and `[project.scripts]` (lines 66-67). There is one blank line before it (line 61) and one blank line after it (line 65).

**Edit 2 — delete lines 61-65** (the blank line + header + `pdf` + `rest` + trailing blank line). This collapses the gap so `[tool.setuptools.dynamic]` is followed directly by `[project.scripts]`. Result for that region:

```toml
[tool.setuptools.dynamic]
version = {attr = "porkbun_api_cli.__version__"}

[project.scripts]
porkbun-api-cli = "porkbun_api_cli.cli:main"
```

**Edit 3 — add `[dependency-groups]` section.** Place it after `[project.scripts]` (current lines 66-67) and before `[tool.bumpversion]` (current line 69). This is a top-level table (PEP 735), conventionally placed after `[project]` sub-tables, before `[tool.*]` tables. TOML section order is irrelevant to uv, but this placement reads naturally. Result:

```toml
[project.scripts]
porkbun-api-cli = "porkbun_api_cli.cli:main"

[dependency-groups]
dev = [
    'pytest',
    'pytest-cov',
    'ruff==0.16.6',
    'ty==0.0.79',
    'types-PyYAML',
    'types-requests',
    'docutils',
    'check-manifest',
    'readme-renderer',
    'pygments',
    'coverage',
    'sphinx>=1.3',
    'sphinx-rtd-theme',
    'sphinx-click',
    'tox',
]

[tool.bumpversion]
```

**Dev-group list rationale (matches `tox.ini` env deps, no duplication of runtime `click`/`pyyaml`/`requests`):**

| dep | source in tox.ini | pinned? |
|-----|-------------------|---------|
| `pytest` | `[testenv] deps` line 35 | no (tox.ini unpinned) |
| `pytest-cov` | `[testenv] deps` line 36 | no |
| `ruff==0.16.6` | `[testenv:check] deps` line 42 | yes (matches tox.ini pin) |
| `ty==0.0.79` | `[testenv:check] deps` line 43 | yes (matches tox.ini pin) |
| `types-PyYAML` | `[testenv:check] deps` line 44 | no |
| `types-requests` | `[testenv:check] deps` line 45 | no |
| `docutils` | `[testenv:check] deps` line 46 | no |
| `check-manifest` | `[testenv:check] deps` line 47 | no |
| `readme-renderer` | `[testenv:check] deps` line 48 | no |
| `pygments` | `[testenv:check] deps` line 49 | no |
| `coverage` | `[testenv:report] deps` line 68; `[testenv:clean]` uses it | no |
| `sphinx>=1.3` | `docs/requirements.txt` line 1 | floor-pinned (matches docs req) |
| `sphinx-rtd-theme` | `docs/requirements.txt` line 2 | no |
| `sphinx-click` | `docs/requirements.txt` line 3 | no |
| `tox` | needed so `uv sync` → `tox` works from `.venv/` | no |

**No `[tool.uv]` section** — verify absent after edits (criterion 6). Do not add one.

**Quote style:** single quotes for the dev-group strings match the existing `importlib-metadata` line's single-quote style and ruff's `quote-style = "preserve"` (line 123). The existing `[project.dependencies]` uses double quotes — that's fine, TOML allows both; ruff doesn't format TOML files (verified: `ruff format --check --diff pyproject.toml` exits 0, no changes).

### 2. `uv.lock` — new file, generated

Run `uv lock` (or `uv lock --python 3.13`) from the repo root after the 3 pyproject.toml edits. uv resolves the full graph against `requires-python>=3.11`, producing a multi-version lock. Expected: 56 `[[package]]` entries (verified in tmp copy).

The implementer commits `uv.lock` to git. It is the reproducibility artifact.

**Confirm each runtime + dev dep is pinned in the lock** (greps to run after generation):

```bash
# runtime deps — each must have a [[package]] block with name + version
grep -A1 'name = "click"' uv.lock | head -2      # → name = "click"\nversion = "..."
grep -A1 'name = "pyyaml"' uv.lock | head -2     # → name = "pyyaml"\nversion = "..."
grep -A1 'name = "requests"' uv.lock | head -2   # → name = "requests"\nversion = "..."

# dev deps — each must appear as a package OR as a dependency entry
for p in pytest pytest-cov ruff ty types-pyyaml types-requests docutils check-manifest readme-renderer pygments coverage sphinx sphinx-rtd-theme sphinx-click tox; do
  grep -q "name = \"$p\"" uv.lock && echo "$p: found" || echo "$p: MISSING"
done
```

Note: some dev deps (e.g. `pytest`) appear both as a `[[package]]` block (top-level dev-group member) and as a dependency entry in other packages' dependency lists. The `grep -q "name = \"$p\""` check confirms the `[[package]]` block exists for each. All 15 dev deps + 3 runtime deps + the project itself (`porkbun-api-cli`) + transitive deps = 56 total.

### 3. `.gitignore` — verify only (no edit needed)

**Current state (lines 104-106):**

```
104: # Environments
105: .env
106: .venv
```

Line 106 already contains `.venv` (matches `.venv/` directory — `.gitignore` patterns match both files and dirs of that name). **No edit needed.** Criterion 19 is verify-only.

### 4. `tox.ini` — no change needed

tox creates its own venvs under `.tox/` (e.g. `.tox/py313/`, `.tox/check/`); it does not read `uv.lock` or `.venv/`. Verified: `tox -e py313` and `tox -e check` both pass on the unmodified working tree. The lockfile is additive infrastructure; tox is unaffected.

**No edits to `tox.ini`.**

## Tests

Red-first: run each check before editing — it should fail (exit non-zero / wrong count / no match). After editing, it passes.

### Criterion 1: `uv.lock` exists at repo root, tracked in git

**Red-first:** `test ! -e uv.lock` → exit 0 (file absent). After: `test -e uv.lock` → exit 0.

```bash
test -e uv.lock && echo "uv.lock exists" || echo "uv.lock MISSING"
git ls-files uv.lock | grep -q '^uv.lock$' && echo "tracked" || echo "NOT tracked"
```

Expected after: `uv.lock exists` + `tracked`. The implementer must `git add uv.lock` (the lockfile is the reproducibility artifact — untracked lockfile defeats the purpose).

### Criterion 2: `uv.lock` resolves all runtime + dev deps

**Red-first:** `test ! -e uv.lock` → cannot grep (file absent). After generation:

```bash
# runtime deps pinned as [[package]] blocks
grep -A1 'name = "click"' uv.lock | grep -q '^version = '
grep -A1 'name = "pyyaml"' uv.lock | grep -q '^version = '
grep -A1 'name = "requests"' uv.lock | grep -q '^version = '
# all 15 dev deps present as [[package]] blocks
for p in pytest pytest-cov ruff ty types-pyyaml types-requests docutils check-manifest readme-renderer pygments coverage sphinx sphinx-rtd-theme sphinx-click tox; do
  grep -q "name = \"$p\"" uv.lock || { echo "MISSING: $p"; exit 1; }
done
echo "all deps resolved"
```

Expected: `all deps resolved`, exit 0.

### Criterion 3: no `[project.optional-dependencies]` section in pyproject.toml

**Red-first:** `grep -F '[project.optional-dependencies]' pyproject.toml` → match found (exit 0). After deletion: no match (exit 1).

```bash
grep -F '[project.optional-dependencies]' pyproject.toml && echo "FAIL: section still present" || echo "pass: section deleted"
```

Expected after: `pass: section deleted`.

### Criterion 4: no `ReportLab`, `RXP`, `pack ==1.1`, `pack ==1.3` strings in pyproject.toml

**Red-first (before edit):** each grep matches. After: no matches.

```bash
grep -F 'ReportLab' pyproject.toml && echo "FAIL" || echo "pass: no ReportLab"
grep -F 'RXP' pyproject.toml && echo "FAIL" || echo "pass: no RXP"
grep -F 'pack ==1.1' pyproject.toml && echo "FAIL" || echo "pass: no pack ==1.1"
grep -F 'pack ==1.3' pyproject.toml && echo "FAIL" || echo "pass: no pack ==1.3"
```

Expected after: all 4 `pass:` lines.

### Criterion 5: no `importlib-metadata` in `[project.dependencies]`

**Red-first:** `grep -F 'importlib-metadata' pyproject.toml` → match (exit 0). After: no match (exit 1).

```bash
grep -F 'importlib-metadata' pyproject.toml && echo "FAIL: still present" || echo "pass: removed"
```

Expected after: `pass: removed`.

### Criterion 6: no `[tool.uv]` section in pyproject.toml

**Red-first (before edit):** `grep -F '[tool.uv]' pyproject.toml` → no match (already absent — this is a non-regression check). After: still no match.

```bash
grep -F '[tool.uv]' pyproject.toml && echo "FAIL: [tool.uv] present" || echo "pass: no [tool.uv]"
```

Expected: `pass: no [tool.uv]` (both before and after).

### Criterion 7: `[dependency-groups]` with `dev = [...]` present

**Red-first:** `grep -F '[dependency-groups]' pyproject.toml` → no match (exit 1). After: match (exit 0).

```bash
grep -F '[dependency-groups]' pyproject.toml && echo "pass: section present" || echo "FAIL: missing"
# verify dev key + all 15 deps listed
grep -A20 '^\[dependency-groups\]' pyproject.toml | grep -F 'dev = ['
grep -A20 '^\[dependency-groups\]' pyproject.toml | grep -c "'"  # expected: 15 (one per dep string)
# spot-check key pinned deps
grep -A20 '^\[dependency-groups\]' pyproject.toml | grep -F "ruff==0.16.6"
grep -A20 '^\[dependency-groups\]' pyproject.toml | grep -F "ty==0.0.79"
```

Expected after: `pass: section present`, `dev = [` match, count 15, both pins found.

### Criterion 8: `uv sync` exits 0, `.venv/` has runtime deps importable

**Red-first:** No `uv.lock` → `uv sync` fails (no lockfile to sync from, or resolves fresh but `.venv/` doesn't exist yet). After lockfile generation:

```bash
uv sync --python 3.13
# expected: exit 0, "Installed N packages"
.venv/bin/python -c "import click, yaml, requests; print('runtime ok')"
# expected: runtime ok
```

Expected: `uv sync` exit 0, `runtime ok` printed.

### Criterion 9: `uv sync` installs dev deps (ruff, pytest, ty runnable)

```bash
.venv/bin/ruff --version
# expected: ruff 0.16.6
.venv/bin/pytest --version
# expected: pytest 9.1.1 (or compatible)
.venv/bin/ty --version
# expected: ty 0.0.79
```

Expected: all 3 print version strings, exit 0.

### Criterion 10: `.gitignore` ignores `.venv/`

**Red-first:** Already present (line 106). This is verify-only — no red state.

```bash
grep -F '.venv' .gitignore
# expected: match at line 106
```

Expected: match found.

### Criterion 11: `tox -e py313` exits 0

tox uses `.tox/py313/` venv, ignores `.venv/`. Run after lockfile generation to confirm no drift.

```bash
tox -e py313
# expected: exit 0, "76 passed, 7 subtests passed", py313: OK
```

Expected: exit 0.

### Criterion 12: `tox -e check` exits 0

```bash
tox -e check
# expected: exit 0, check: OK (ruff check + ruff format --check + ty check + setup check + check-manifest)
```

Expected: exit 0.

### Criterion 13: `uv lock --check` exits 0

**Red-first:** No `uv.lock` → `uv lock --check` fails (lockfile absent or stale). After generation:

```bash
uv lock --check
# expected: exit 0 (lockfile up-to-date with pyproject.toml)
```

Expected: exit 0.

## Implementation order

Smallest sequence that satisfies the contract end-to-end:

1. **Edit `pyproject.toml` — remove `importlib-metadata` line (line 39).** Delete the line `'importlib-metadata; python_version<"3.10"',` from `[project.dependencies]`. The `dependencies` array becomes 3 entries: `click`, `pyyaml`, `requests`.

2. **Edit `pyproject.toml` — delete `[project.optional-dependencies]` block (lines 61-65).** Remove the blank line (61) + header (62) + `pdf` (63) + `rest` (64) + blank line (65). The region between `[tool.setuptools.dynamic]` and `[project.scripts]` collapses to a single blank line separator.

3. **Edit `pyproject.toml` — add `[dependency-groups]` section.** Insert after `[project.scripts]` block (after line 67 `porkbun-api-cli = "porkbun_api_cli.cli:main"`) and before `[tool.bumpversion]` (line 69). Add a blank line, the `[dependency-groups]` header, `dev = [...]` array with the 15 deps listed above, and a trailing blank line. Use single-quoted strings for the dep entries (matches ruff `quote-style = "preserve"`).

4. **Verify `.gitignore` line 106** — `.venv` already present. No edit.

5. **Run `uv lock`** from repo root:
   ```bash
   uv lock
   ```
   Generates `uv.lock` at repo root. Expected: `Resolved 56 packages`, exit 0. (No `--python` flag needed — uv reads `requires-python>=3.11` and uses the local default interpreter; `--python 3.13` is optional.)

6. **Run `uv sync`** to build `.venv/`:
   ```bash
   uv sync
   ```
   Expected: installs 53 packages, exit 0.

7. **Verify runtime + dev deps in `.venv/`:**
   ```bash
   .venv/bin/python -c "import click, yaml, requests"
   .venv/bin/ruff --version
   .venv/bin/pytest --version
   .venv/bin/ty --version
   ```

8. **Run `uv lock --check`** — confirms lockfile is up-to-date:
   ```bash
   uv lock --check
   ```

9. **Run `tox -e py313`** — confirms no drift (tox ignores `.venv/`, uses `.tox/`):
   ```bash
   tox -e py313
   ```

10. **Run `tox -e check`** — ruff + ty + setup + manifest green with merged pyproject:
    ```bash
    tox -e check
    ```

11. **`git add uv.lock pyproject.toml`** — stage the lockfile + config changes. The lockfile must be tracked (criterion 1).

### AGENTS.md consultation points

- AGENTS.md does not bind any update for this feature. The implementer should NOT touch AGENTS.md.
- AGENTS.md L12 ("flake8 + black --check + isort --check-only") is stale (ruff-migration replaced it; ty-typecheck added ty). Not bound here.
- AGENTS.md L23 ("`pytest.ini` sets `filterwarnings = error`") is stale (config moved to `pyproject.toml [tool.pytest.ini_options]` in ruff-migration). Not bound here.
- AGENTS.md L28 ("Pinned linters: `flake8==7.0.0`, `black==24.3.0`, `isort==5.13.2`") is stale since ruff-migration. Not bound here.
- AGENTS.md is not a touchpoint for this feature. If the closer wants to note AGENTS.md staleness, that's a follow-up — not this feature's scope.

## Manual checks

None. Contract `Manual-Checks: —`. All 13 acceptance criteria are `[auto]` and proven by the test commands above (file-content greps, `uv lock`/`uv sync`/`uv lock --check` exit codes, `tox -e py313`/`tox -e check` exit codes).

No entry appended to `docs/ristretto/manual-checks.md`.

## Evidence

tier: normal

### Gate: lint
- Command: `tox -e check`
- Exit code: 0
- Output:
  ```
  check: commands[0]> ruff check .
  All checks passed!
  check: commands[1]> ruff format --check --diff .
  12 files already formatted
  check: commands[2]> ty check src/porkbun_api_cli
  All checks passed!
  check: commands[3]> python setup.py check --strict --metadata --restructuredtext
  running check
  check: commands[4]> check-manifest .
  lists of files in version control and sdist match
    check: OK (7.05=setup[2.05]+cmd[0.01,0.01,0.08,0.35,4.54] seconds)
    congratulations :) (8.50 seconds)
  ```

### Gate: test
- Command: `tox -e py313`
- Exit code: 0
- Output:
  ```
  platform linux -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
  collected 76 items

  tests/test_api.py ... 19 passed
  tests/test_cli.py ... 16 passed
  tests/test_utils.py ... 41 passed

  coverage report (TOTAL row):
  TOTAL   488   16   188   12   95.86%
  Required test coverage of 95.0% reached. Total coverage: 95.86%
  ==================== 76 passed, 7 subtests passed in 0.82s =====================
    py313: OK (5.27=setup[4.02]+cmd[1.25] seconds)
    congratulations :) (5.45 seconds)
  ```

### Acceptance criteria

- [x] [1] uv.lock exists + tracked — `test -e uv.lock` → `uv.lock exists`; `git ls-files uv.lock | grep -q '^uv.lock$'` → `tracked`. File tracked in commit `188abc2`.
- [x] [2] uv.lock resolves all runtime + dev deps — `grep -c '\[\[package\]\]' uv.lock` → `56`. Runtime deps resolved: `click 8.5.0` (`[[package]]` block with version), `pyyaml`, `requests` (both appear as dependency entries in the graph and as `[[package]]` blocks). All 15 dev deps confirmed via `grep -q "name = \"$p\""` for each (`pytest`, `pytest-cov`, `ruff`, `ty`, `types-pyyaml`, `types-requests`, `docutils`, `check-manifest`, `readme-renderer`, `pygments`, `coverage`, `sphinx`, `sphinx-rtd-theme`, `sphinx-click`, `tox`) → all `found`.
- [x] [3] no `[project.optional-dependencies]` — `grep -F '[project.optional-dependencies]' pyproject.toml` → no match → `pass: section deleted`.
- [x] [4] no ReportLab/RXP/pack strings — 4 greps (`grep -F 'ReportLab'`, `'RXP'`, `'pack ==1.1'`, `'pack ==1.3'` on pyproject.toml) → all 4 `pass:` no match.
- [x] [5] no importlib-metadata — `grep -F 'importlib-metadata' pyproject.toml` → no match → `pass: removed`.
- [x] [6] no `[tool.uv]` — `grep -F '[tool.uv]' pyproject.toml` → no match → `pass: no [tool.uv]`.
- [x] [7] `[dependency-groups] dev` present — `grep -F '[dependency-groups]' pyproject.toml` → `pass: section present`. Section body confirmed: `dev = [` with 15 single-quoted entries including `'ruff==0.16.6'` and `'ty==0.0.79'` (pins match tox.ini).
- [x] [8] `uv sync` exits 0, runtime importable — `uv sync` → `Resolved 56 packages in 1ms` / `Checked 53 packages in 0.93ms`, exit 0. `.venv/bin/python -c "import click, yaml, requests; print('runtime ok')"` → `runtime ok`, exit 0.
- [x] [9] dev tools runnable — `.venv/bin/ruff --version` → `ruff 0.16.6`; `.venv/bin/pytest --version` → `pytest 9.1.1`; `.venv/bin/ty --version` → `ty 0.0.79`. All exit 0.
- [x] [10] `.gitignore` has `.venv` — `grep -F '.venv' .gitignore` → match at line 106 (`.venv`). Pre-existing; no edit needed.
- [x] [11] `tox -e py313` exits 0 — see Gate: test above. `py313: OK`, 76 passed, 7 subtests, 95.86% coverage.
- [x] [12] `tox -e check` exits 0 — see Gate: lint above. `check: OK` (ruff check + ruff format --check + ty check + setup check + check-manifest all pass).
- [x] [13] `uv lock --check` exits 0 — `uv lock --check` → `Resolved 56 packages in 1ms`, exit 0.

### Gate summary

- lint ✓ (`tox -e check` exit 0)
- test ✓ (`tox -e py313` 76 passed, 7 subtests, 95.86% cov)

### Review verdict

review: notes-only (0 note, 1 lean) (1 round)

## Open findings

- lean · AGENTS.md · L12/L23/L28 stale (flake8/black/isort replaced by ruff, pytest.ini moved to pyproject) · plan itself flags as out-of-scope follow-up; contract doesn't bind it.