# plan-dedup — Remove duplicate plan rendering; fix ghost header in _render_plan

## Spec
- Source: shot (TUI design review of cli-ux-rework branch)
- Flight: —
- Goal: the cli-ux-rework build added `_render_plan` as the canonical plan view but left the old `_log_if_level`-driven per-record lines in `_plan_operations`; at verbose ≥ 2 (which `--dry-run` auto-bumps to) the user reads the plan twice in two formats. Remove the dead per-record log lines from `_plan_operations` so the planner is pure and `_render_plan` owns the per-row view. Also fix the ghost-header bug in `_render_plan`: `f"Plan for {domain} ({mode} mode):"` prints even when every row is a `match` hidden below verbose ≥ 2, leaving a header with no body.

## Contract
- Acceptance:
  - [auto] `_plan_operations` emits no `_log_if_level` call for per-record `\t- create`, `\t- update`, or `\t- found matching` lines; the `\n\tPROCESSING EXISTING RECORDS\n` section header is removed. The two skip-reason lines (query failure, not-in-config) and the two ttl/prio stderr warnings remain.
  - [auto] `_render_plan` prints the `f"Plan for {domain} ({mode} mode):"` header only when at least one row will render (i.e., at least one `create`/`update` entry, or at least one `match` entry at verbose ≥ 2). A domain whose plan is all-matches at verbose < 2 prints no header.
  - [auto] `tox -e py313` exits 0; `tox -e check` exits 0.
  - [auto] At `--dry-run` with a mixed plan (create + match + update), stdout shows exactly one plan block (`Plan for …` header + symbol rows), not two (`PROCESSING` block + `Plan for …` block).
- Provides: `_plan_operations` is a pure planner (no per-row rendering, no `processed` dead state); `_render_plan` owns the entire per-row view and gates its header on whether any row renders (collect-then-emit pattern).
- Consumes: `PlanEntry` with `Literal["create","update","delete","match"]` (unchanged); `_log_if_level` (still used for skip-reasons + ttl/prio warnings); `_render_plan` (signature unchanged).
- Decisions:
  - Skip-reason lines stay in `_plan_operations` because they are domain-level decisions (query failed / not in config), not per-record plan rows — `_render_plan` skips `None` plans entirely and never surfaces these.
  - ttl/prio stderr warnings stay in `_plan_operations` because they are config-time diagnostics, not plan rows.
  - Ghost-header fix: iterate once to collect renderable rows, then emit header + rows only if the list is non-empty. Avoids a two-pass `any()` scan + re-iterate.
  - The `processed` list (-tracking which existing records were matched) is retained — it was there for the now-removed delete block but is harmless dead state; removing it is a separate cleanup, not this shot's scope. (Actually: `processed` is now fully dead — nothing reads it after the delete block was removed in cli-ux-rework. Removing it is in scope as adjacent dead code from the same rework.)

## Approach
Tier: easy

Two touchpoints in `src/porkbun_api_cli/cli.py`:
1. `_plan_operations` (lines 71–140): delete the `\n\tPROCESSING EXISTING RECORDS\n` header log (line 79), the three per-record `\t- …` log calls (lines 120–124, 127–131, 135), and the now-dead `processed` list (lines 95, 103). Keep skip-reason logs (86, 90) and ttl/prio stderr warnings (107–119).
2. `_render_plan` (lines 184–213): restructure to collect renderable rows first, emit header + rows only if non-empty.

Test touchpoint: `tests/test_cli.py::TestHelpers` — seven tests assert `_log_if_level.mock_calls` including the removed lines. Update expected_calls to drop the `\t- …` and header calls, keeping skip-reason and ttl/prio warning calls. The five mode tests (`_replace_mode`/`_upgrade_mode`, `_append_mode`, `_update_mode`, `_upgrade_mode`, `_emits_exactly_one_match_entry`, `_ttl_zero_emits_warning`, `_prio_omitted_emits_warning`) each lose 1–3 expected calls.

No new deps, no pyproject/tox changes.
## Evidence

115 passed, coverage 97.43%, `tox -e check` PASS, `tox -e py311` PASS.
tier: easy
review: clean (1 round)

### Gate: lint
- Command: `tox -e check`
- Exit code: 0
- Output: ruff check pass, ruff format --check pass, ty check pass, readme_renderer pass, check-manifest pass.

### Gate: test
- Command: `tox -e py311` (full suite via gate.js verify)
- Exit code: 0
- Output: 115 passed, coverage 97.43% (above 95% threshold).

### Acceptance criteria evidence

Criterion 1 — no per-record `_log_if_level` in `_plan_operations`:
- 7 tests assert `_log_if_level.mock_calls` with only skip-reason + ttl/prio warning calls (no `\t- …` or `\n\tPROCESSING EXISTING RECORDS\n`): `test_plan_operations_replace_mode`, `_append_mode`, `_update_mode`, `_upgrade_mode`, `_emits_exactly_one_match_entry`, `_ttl_zero_emits_warning`, `_prio_omitted_emits_warning`. Red→green.

Criterion 2 — ghost header suppressed:
- `test_cli_plan_match_rows_hidden_below_verbose_2` asserts `"Plan for example.com" not in result.output` at verbose=1 with all-match plan. Red→green.
- `test_cli_plan_header_shown_when_create_exists_even_at_verbose_0` asserts header present when a create row renders at verbose=0.

Criterion 3 — gates green:
- `gate.js verify` exit 0 (lint ✓ + test ✓).

Criterion 4 — one plan block at --dry-run:
- `test_cli_exit_code_3_on_dry_run_with_changes` asserts `"Plan for example.com"` in output; `PROCESSING` block removed from source (no `\t- …` lines remain in `_plan_operations`). `test_cli_exit_code_0_on_dry_run_in_sync` verifies all-match dry-run renders header at verbose≥2 (auto-bumped).

### Gate summary

- lint ✓ (`tox -e check` exit 0)
- test ✓ (`tox -e py311` 115 passed, 97.43% cov)
- type checker ✓ (`ty check src/porkbun_api_cli` PASS)

### Review verdict

review: clean (1 round)
