# Ristretto Roadmap
<!-- ristretto-format: 0.16 -->

| Flight | Feature | Title | Tier | Status | Plan | Updated |
|--------|---------|-------|------|--------|------|---------|
| build-modernization | py-version-floor | Bump supported Python range to 3.11–3.14, update tox + CI matrix, py3.13 default | normal | done | plans/py-version-floor.md | 2026-09-08 (commit 222f20b) |
| build-modernization | ruff-migration | Replace flake8+black+isort with ruff; consolidate config into pyproject | normal | done | plans/archived/ruff-migration-build.md | 2026-09-08 (commit 743a0d5) |
| build-modernization | ty-typecheck | Add type annotations to src/; ty blocking in check env | normal | done | plans/archived/ty-typecheck-build.md | 2026-09-08 (commit 614091e) |
| build-modernization | uv-lockfile | Add uv.lock; prune dead extras, dead conditional dep; use [dependency-groups] | normal | done | plans/archived/uv-lockfile-build.md | 2026-09-08 (commit 188abc2) |