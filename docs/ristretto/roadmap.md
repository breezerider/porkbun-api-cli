# Ristretto Roadmap
<!-- ristretto-format: 0.16 -->

| Flight | Feature | Title | Tier | Status | Plan | Updated |
|--------|---------|-------|------|--------|------|---------|
| build-modernization | py-version-floor | Bump supported Python range to 3.11–3.14, update tox + CI matrix, py3.13 default | normal | done | plans/py-version-floor.md | 2026-09-08 (commit 222f20b) |
| build-modernization | ruff-migration | Replace flake8+black+isort with ruff; consolidate config into pyproject | normal | done | plans/archived/ruff-migration-build.md | 2026-09-08 (commit 743a0d5) |
| build-modernization | ty-typecheck | Add type annotations to src/; ty blocking in check env | normal | done | plans/archived/ty-typecheck-build.md | 2026-09-08 (commit 614091e) |
| build-modernization | uv-lockfile | Add uv.lock; prune dead extras, dead conditional dep; use [dependency-groups] | normal | done | plans/archived/uv-lockfile-build.md | 2026-09-08 (commit 188abc2) |
| dto-ux-rework | dto-migration | TypedDict→frozen dataclass migration + ttl/prio int fix + notes field + from_api boundary | easy (forced) | done | plans/archived/dto-migration-build.md | 2026-09-15 (commit a65afcb; src/api.py,cli.py,utils.py · tests/test_api.py,cli.py,utils.py · docs/ristretto/manual-checks.md,memos.md) |
| dto-ux-rework | plan-entry-redesign | Extend Operation with Literal["match"]; emit match entries from _plan_operations | normal | planned | plans/plan-entry-redesign.md | 2026-09-14 |
| dto-ux-rework | cli-ux-rework | Structured plan output, exit codes, --yes, replace disabled, color, per-domain summary | normal | planned | plans/cli-ux-rework.md | 2026-09-14 |
