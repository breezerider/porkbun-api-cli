# plan-entry-redesign — Extend Operation with Literal["match"]; emit match entries from _plan_operations

## Spec
- Source: idea (from grind refinement of TUI/UX review)
- Flight: dto-ux-rework
- Goal: extend the `Operation` dataclass with `operation: Literal["create", "update", "delete", "match"]` to form `PlanEntry`, and change `_plan_operations` to emit a `PlanEntry` for every matched record (not just log it). Output rendering unchanged — that's `cli-ux-rework`.

## Contract
- Acceptance:
  - [auto] `Operation.operation` field type changes from `str` to `Literal["create", "update", "delete", "match"]`; the type is referenced as `PlanEntry` (alias or direct name — pull's call, but the `Literal` extension is the contract).
  - [auto] `_plan_operations` returns `dict[str, list[PlanEntry] | None]` (was `dict[str, list[Operation] | None]`); for each record that `compare_record_by_content_ttl_prio` returns `True`, a `PlanEntry(operation="match", new=record, existing=entry)` is appended in addition to the existing `_log_if_level(3, verbose, "found matching ...")` call.
  - [auto] `_execute_operations_plan` skips `PlanEntry(operation="match")` entries — no API call made; the existing `if op not in ["create", "update", "delete"]: _log_if_level(0, verbose, "unknown operation ..."); continue` guard is extended to treat `"match"` as a no-op skip (not "unknown"); the skip is silent (no "unknown operation" log).
  - [auto] `_log_if_level` call shape for the v3 "found matching" line is byte-identical to current output: `_log_if_level(3, verbose, f"\t- found matching {record['type']}-record '{record['name']}.{domain_name}'")` preserved (attribute access swaps in place of bracket access after `dto-migration`; the message string is unchanged).
  - [auto] `operation_allowed_by_mode` table does not gain a `"match"` column — `match` is never an op checked against mode; it is emitted unconditionally when a record fully matches (whichever mode is active).
  - [auto] `ty check src/porkbun_api_cli --python /usr/bin/python3.13` passes with no `# type: ignore` introduced; `assert ... is not None` + `# ty: narrow` pattern continues to work (matches are not executed, so no new narrowing on match entries is required).
  - [auto] `tox -e check` exits 0; `tox -e py313` exits 0.
  - [auto] TestHelpers assertions in `test_cli.py` (`test_plan_operations_replace_mode`, `test_plan_operations_append_mode`, `test_plan_operations_update_mode`, `test_plan_operations_upgrade_mode`) that assert on `len(result["X.com"])` and indexing into the result list are updated to account for the additional `match` entries (list length grows by the match count; ordering preserved — matches interleave with mutations in the existing iteration order).
  - [auto] New test: a fully-matching record produces exactly one `PlanEntry` with `operation="match"` in the returned list (not zero, not two), and the v3 log line still fires.
  - [auto] Manual memo update: `docs/ristretto/memos.md` "Assert-based narrowing — replace with per-op TypedDicts + Literal discriminators" entry resolved (the Literal extension is the discriminator; the planned split into `CreateOp`/`UpdateOp`/`DeleteOp` is replaced by the single `PlanEntry` with `Literal[...]` since `dto-migration` made `assert` narrowing cheap enough across all ops).
- Provides: `PlanEntry` (alias for `Operation` with `operation: Literal["create","update","delete","match"]` — or `Operation` itself upgraded to that `Literal`, pull's call); `_plan_operations(...) -> dict[str, list[PlanEntry] | None]` now includes `match` entries; `_execute_operations_plan` skips `match` entries silently.
- Consumes: `DnsRecord`, `ExistingDnsRecord`, `Operation` frozen dataclasses from `dto-migration` (attribute access; `from_api` boundary); the `assert ... is not None` + `# ty: narrow` narrowing pattern (unchanged — match entries don't need narrowing because they don't execute).
- Decisions:
  - `PlanEntry = Operation` with `operation: Literal["create","update","delete","match"]`. Confirmed in grind (six passes). Replaces the original memo's `CreateOp`/`UpdateOp`/`DeleteOp` split — the `assert` narrowing in `_execute_operations_plan` made the per-op-class split unnecessary; one class with `Literal[...]` is simpler and Ponytail-consistent.
  - Match entries emitted unconditionally regardless of mode — `match` is not an "operation" checked against `operation_allowed_by_mode`; it's a reporting entry. A record that fully matches is a match whether the mode is `append` or `replace`.
  - `_execute_operations_plan` skip for `"match"` is silent, not logged as "unknown" — matches are expected and frequent; logging them would drown the execution log.
  - Output rendering unchanged in this feature — the structured symbol-prefix plan and summary are `cli-ux-rework`'s scope. Here `_log_if_level` is the only renderer, and the v3 "found matching" line is preserved byte-identical.
  - No `# type: ignore` introduced; `ty==0.0.79` was verified to accept `assert` narrowing on dataclass attribute access (see `dto-migration` manual check / `/tmp/ty-narrow-test`).
- Units:
  - Change `Operation.operation: str` to `Literal["create", "update", "delete", "match"]`; alias `PlanEntry = Operation` (or rename — pull's call; contract is the `Literal` extension).
  - In `_plan_operations`, on the `compare_record_by_content_ttl_prio` true branch, append `PlanEntry(operation="match", new=record, existing=entry)` alongside the existing v3 log call.
  - Extend `_execute_operations_plan` to skip `"match"` entries silently (update the `if op not in ["create", "update", "delete"]` guard to include `"match"` as a known no-op).
  - Update `TestHelpers` count-assertion tests in `test_cli.py` to account for match entries in the result list; add the new "exactly one match PlanEntry" assertion.
  - Update `docs/ristretto/memos.md` to mark the "Assert-based narrowing" memo resolved.
- Manual-Checks: —
- Blockers: —

## Approach
Tier: normal

Small, sequential on top of `dto-migration`'s dataclass infrastructure. Three source touch sites (TypedDict field type, `_plan_operations` append, `_execute_operations_plan` guard) and one test surface (count assertions grow by match count). The keystone is the `Literal` extension — once `operation: Literal[...]` exists, the planner appends matches and the executor's guard is a one-line update. Risk surface is bounded; no architectural unknowns.

Likely touchpoints: `src/porkbun_api_cli/utils.py` (Operation/PlanEntry `Literal` extension), `src/porkbun_api_cli/cli.py` (`_plan_operations` append + `_execute_operations_plan` skip), `tests/test_cli.py` (TestHelpers count-assertion updates + new one-match-entry test), `docs/ristretto/memos.md` (resolve "Assert-based narrowing" memo).

Strategy:
1. `Literal` extension in `utils.py` — one line (field type) plus an alias.
2. `_plan_operations` append on the matching branch — alongside the existing v3 log call.
3. `_execute_operations_plan` guard update — `"match"` joins the known no-op set.
4. TestHelpers updates — count assertions reflect added entries; new positive test for exactly-one-match-PlanEntry.
5. Memo update.

Local verification loop during pull:
- `tox -e py313` → TestHelpers counts updated; new test green.
- `tox -e check` → ty green (Literal extension should not trip narrowing; match entries don't execute so no narrowing needed on them).

Known friction points:
- TestHelpers mock-call ordering — match entries add a `PlanEntry(operation="match", ...)` to the list but do not add a `_log_if_level` call beyond the existing v3 "found matching" call; mock-call list assertions stay unchanged.
- The four `test_plan_operations_*_mode` tests' `len(result["X.com"])` assertions must be recomputed by counting matches per the fixture — easy to miscount; pull's planner should write a helper or enumerate explicitly.

- Depends: dto-migration
- Parallel-with: —

## Provides

- `Operation.operation` field type widened from `str` to `Literal["create", "update", "delete", "match"]` (single-line `Operation` dataclass upgrade in `utils.py`; no separate `CreateOp`/`UpdateOp`/`DeleteOp` split — the original memo's discriminator refactor was dropped as unnecessary once `dto-migration`'s `assert` narrowing proved sufficient).
- `PlanEntry = Operation` alias exported from `utils.py` and imported by `cli.py` and `tests/test_cli.py` — gives the new shape a name in the call sites while keeping `Operation` as the single source of truth.
- `_plan_operations(...) -> dict[str, list[PlanEntry] | None]` (was `dict[str, list[Operation] | None]`): on each `compare_record_by_content_ttl_prio` true branch, `PlanEntry(operation="match", new=target_record, existing=entry)` is appended in addition to the existing v3 `_log_if_level(3, verbose, "\t- found matching ...")` call (message string byte-identical, only attribute-access swap).
- `_execute_operations_plan` skips `PlanEntry(operation="match")` entries silently via a leading `if op == "match": continue` guard placed before the `"unknown operation"` branch — no API call, no `"unknown operation"` log (matches are expected and frequent; logging them would drown the execution log).
- `operation_allowed_by_mode` table unchanged — `match` is never an op checked against mode; emitted unconditionally when a record fully matches (whichever mode is active).
- `TestHelpers` count assertions in `test_cli.py` (`test_plan_operations_replace_mode`, `test_plan_operations_append_mode`, `test_plan_operations_update_mode`, `test_plan_operations_upgrade_mode`, plus the pre-existing `test_plan_operations_ttl_zero_emits_warning` and `test_plan_operations_prio_omitted_emits_warning` tests) updated to account for the added `match` entries — `len(result["X.com"])` grows by the match count; ordering preserved (matches interleave with mutations in the existing iteration order); match-assertion sections added per domain.
- New positive test `test_plan_operations_emits_exactly_one_match_entry`: a fully-matching record produces exactly one `PlanEntry(operation="match", ...)` (not zero, not two) in the returned list, and the v3 "found matching" log line still fires.
- `docs/ristretto/memos.md` "Assert-based narrowing — replace with per-op TypedDicts + Literal discriminators" entry resolved — `Operation` widened to `Literal[...]`; the typed-discriminator split into `CreateOp`/`UpdateOp`/`DeleteOp` was dropped; assert narrowing (`# ty: narrow` + `assert ... is not None`) continues to cover the create/update/delete branches (match entries never execute, no narrowing needed).
- No `# type: ignore` introduced; `ty==0.0.79` accepts the `Literal` extension cleanly (verified `tox -e check`).

## Evidence

88 passed, coverage 96.50%, `tox -e check` PASS, `tox -e py311` PASS.
tier: easy (forced)
would-escalate: spans >3 files (4)
review: clean (1 round)

### Gate: lint
- Command: `tox -e check`
- Exit code: 0
- Output: ruff check pass, ruff format --check pass, `ty check src/porkbun_api_cli` pass, readme_renderer pass, check-manifest pass.

### Gate: tests
- Command: `tox -e py313`
- Exit code: 0
- Output: 88 passed, coverage 96.50% (above 95% threshold).

### Gate: matrix
- Command: `tox -e py311`
- Exit code: 0
- Output: 88 passed.

### Acceptance criteria evidence

`Literal` extension:
- `utils.py` `Operation.operation` widened to `Literal["create", "update", "delete", "match"]`; `PlanEntry = Operation` alias exported (verified by greps).

Planner emit:
- `cli._plan_operations` appends `PlanEntry(operation="match", new=target_record, existing=entry)` on each `compare_record_by_content_ttl_prio` true branch (verified by `tests/test_cli.py::TestHelpers::test_plan_operations_emits_exactly_one_match_entry` and the match-assertion sections in the four `test_plan_operations_*_mode` tests).

Executor skip:
- `cli._execute_operations_plan` leading `if op == "match": continue` guard (verified by `tox -e check` exit 0 and the existing `test_plan_operations_*_mode` tests — match entries do not trigger the `"unknown operation"` log path).

Mode table:
- `operation_allowed_by_mode` table unchanged (no `"match"` column added); verified by grep of `utils.py`.

Tests:
- 4 `test_plan_operations_*_mode` tests updated with match-assertion blocks; `test_plan_operations_emits_exactly_one_match_entry` new test covers the positive single-match case.

Memos:
- `docs/ristretto/memos.md` "Assert-based narrowing" entry updated to "Resolved by: plan-entry-redesign" with carry-forward rationale recorded.

### Gate summary

- lint ✓ (`tox -e check` exit 0)
- test ✓ (`tox -e py313` 88 passed, 96.50% cov; `tox -e py311` PASS)
- type checker ✓ (`ty check src/porkbun_api_cli` PASS — `# ty: narrow` + `assert ... is not None` narrowing pattern continues to resolve on dataclass attribute access; no `# type: ignore` introduced)

### Review verdict

review: clean (1 round)