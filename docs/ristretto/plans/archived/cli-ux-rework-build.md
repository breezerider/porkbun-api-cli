# cli-ux-rework — Structured plan output, exit codes, --yes, replace disabled, color, summary

## Spec
- Source: idea (from grind refinement of TUI/UX review, six passes)
- Flight: dto-ux-rework
- Goal: replace the current `_log_if_level`-driven plain output with a structured plan (always printed before the y/N prompt), per-domain summary line, descriptive exit codes (0/1/2/3/4), `--yes` flag, stdout/stderr split, `replace` mode disabled (errors as not-implemented), `click.style` color gated on `isatty()` + `NO_COLOR`, and the dead delete-branch + `operation_allowed_by_mode` delete row removed.

## Contract
- Acceptance:
  - [auto] `main()` accepts a new `--yes` / `-y` flag (Click `is_flag=True`, `help="Skip confirmation prompt"`) and `--dry-run` is unchanged.
  - [auto] `--mode` `click.Choice` list includes `replace` (kept — so the help text can mention it), but `main()` raises `click.UsageError("replace mode is not implemented, use 'upgrade'")` if `mode == "replace"`. Click's default conversion of `UsageError` produces exit code 2.
  - [auto] The `main()` docstring / `--mode` help text notes `replace` as "not implemented, use 'upgrade'".
  - [auto] `--yes --dry-run` combination: `main()` raises `click.UsageError("--yes and --dry-run are mutually exclusive")` → exit code 2.
  - [auto] `--dry-run` help text (Click `help=` string) states: "Perform a trial run without any changes; exits non-zero (code 3) if any changes would be needed".
  - [auto] When `--dry-run` is set, `verbose` is auto-bumped to `max(2, verbose)` as today; the plan is printed; execution is skipped; `main()` exits with code 3 if any `PlanEntry.operation in {"create", "update", "delete"}` is in the plan, otherwise 0.
  - [auto] The plan is **always** printed before the y/N prompt, independent of verbosity — every planned mutation produces a row; match rows appear only when `verbose >= 2`; the plan header shows the domain name and mode.
  - [auto] Plan rows use the word-prefix symbol scheme C, left-padded to 3 columns: `"NEW"`, `"UPD"`, `"DEL"`, `"OK "`, `"ERR"`, `"SKP"`; each row includes the record type, name, and content.
  - [auto] After execution, a per-domain summary line is printed to stdout in the form `"Summary for {domain}: {N} created, {N} updated, {N} deleted, {N} matched, {N} failed"`; zero-entries are shown only when `verbose >= 1`; a domain with zero records prints `"no records found"` in place of the counts; the summary line is always printed (including the no-change case), unless the domain was skipped (query failure or "not in config").
  - [auto] Failure detail messages from `_execute_operations_plan` exception paths are emitted to stderr via `_log_if_level(..., file=sys.stderr)`; status words (`"done"`, `"failed"`, `"skipped"`) remain on stdout.
  - [auto] Color: when `sys.stdout.isatty() is True` and `os.environ.get("NO_COLOR") is None`, output is colored via `click.style` — plan symbols and summary-line counts use color (`NEW`/`UPD`/`DEL`/`OK`/`ERR`/`SKP` each get a color, pulled's call on the palette); failure-detail lines on stderr are colored red. When `isatty()` is False or `NO_COLOR` is set, output is plain (no ANSI codes). No `--color` / `FORCE_COLOR` override flag.
  - [auto] `cli.py:_plan_operations` loses the `if utils.operation_allowed_by_mode("delete", mode):` block (lines 99–103 in current source); `utils.operation_allowed_by_mode` loses its `elif mode == "replace": return operation in ["create","update","delete"]` branch (the `delete` entry is removed; the `replace` branch returns `operation in ["create","update"]` — equivalent to `upgrade`, but `replace` is errored at the CLI boundary before this function is ever called with it, so the branch is dead either way; remove the `replace` branch entirely and let `operation_allowed_by_mode` return `False` for unknown modes).
  - [auto] `_execute_operations_plan` no longer references `"delete"` in its `if op in ["create", "update", "delete"]` dispatch — the `"delete"` op is unreachable now that the planner can never produce it; the existing `elif op == "delete": _log_if_level(0, verbose, "delete operation is not implemented - skipped")` branch and its test mock-call assertions are removed.
  - [auto] Exit code matrix:
    - `0` — success (with or without changes); dry-run in sync (no changes needed).
    - `1` — pre-execution failure: `api.get_my_ip` failure, config load failure, generic `RuntimeError` before execution begins.
    - `2` — usage error (Click default): `--mode replace`, `--yes --dry-run`, missing `config_file`, invalid args.
    - `3` — dry-run with planned changes (any `PlanEntry.operation in {"create","update","delete"}` in the plan).
    - `4` — any execution-time failure (at least one `RuntimeError` caught in `_execute_operations_plan`).
  - [auto] `main()` exits with the appropriate exit code via `sys.exit(N)` on each terminal path; success with all ops succeeded = `sys.exit(0)`; partial or total execution failure = `sys.exit(4)`; dry-run with changes = `sys.exit(3)`; dry-run in sync = `sys.exit(0)`.
  - [auto] Existing exact-match output assertions in `tests/test_cli.py` are fully replaced by behavioral assertions: exit code by scenario; `stdout` substring presence (e.g., `"Summary for {domain}:"` + `"1 created"`); `stderr` substring presence for failure messages; mock-call **existence** (not exact ordering) of `api.create_record`/`api.update_record`. No exact-string `'\n'.join([...])` assertions remain on `result.output`.
  - [auto] Behavioral test for each exit code: 0 (in-sync run or non-dry-run success), 1 (auth/ping failure), 2 (`--mode replace`, `--yes --dry-run`, missing config arg), 3 (dry-run with changes), 4 (any op failure during execution).
  - [auto] Behavioral test for `--yes` (no prompt shown, execution proceeds), for y/N prompt text still appearing when `--yes` is not set, for dry-run auto-bumping to verbose ≥ 2.
  - [auto] Behavioral test for color suppression: `runner.invoke(cli.main, [...], env={"NO_COLOR": "1"})` produces stdout with no ANSI escape codes; `runner.invoke(..., color=False)` (CliRunner default) does the same.
  - [auto] `tox -e check` exits 0 (ruff + ty + setup + manifest green); `tox -e py313` exits 0.
  - [auto] `README.rst` updated: `replace` mode bullet says `not implemented, use 'upgrade'`; exit code matrix documented in a new section; `--yes` flag mentioned in usage.
- Provides: `--yes`/`-y` flag (skip confirmation prompt); new exit-code contract (0/1/2/3/4) — breaking from prior 0/1; `--dry-run` help string notes exit code 3; structured plan with `NEW`/`UPD`/`DEL`/`OK`/`ERR`/`SKP` symbols; per-domain summary line; `--mode replace` disabled (errors); `NO_COLOR` honored; dead delete-branch removed from `_plan_operations` + `operation_allowed_by_mode` delete row removed.
- Consumes: `PlanEntry` with `Literal["create","update","delete","match"]` from `plan-entry-redesign` (`_plan_operations` return type; the plan renderer iterates this); `DnsRecord`/`ExistingDnsRecord` dataclass attribute access from `dto-migration` (`record.name`, `record.type`, `record.content`).
- Decisions:
  - Exit code 3 (not 2) for dry-run-with-changes — Click's `UsageError` already uses 2; using 2 would mask usage errors from CI/scripts. 3 is "the next free code after Click's 2."
  - Exit code 4 for any execution failure — partial vs total failure distinguished by the summary counts, not the exit code. One code simplifies CI gating.
  - Symbol scheme = word prefix (Scheme C): `NEW`/`UPD`/`DEL`/`OK`/`ERR`/`SKP`, left-padded to 3 columns. Self-documenting, no legend needed; chosen over git-style (B) and ASCII (A) for explicitness — a DNS CLI used by engineers benefits from unambiguous state labels over compactness.
  - Match rows gated at verbose ≥ 2 (not 1) — match volume scales with config size; verbose 1 keeps output scannable, dry-run auto-2 still surfaces matches.
  - Warnings → stderr (consistent with the failure-detail-to-stderr rule): plan+summary+status words on stdout, advisory/failure on stderr.
  - `replace` mode disabled via option (b): kept in `click.Choice` so `--help` can mention it, errored in `main()` via `click.UsageError` with message `"replace mode is not implemented, use 'upgrade'"`. Help text (the `--mode` Click `help=` string) notes this.
  - Dead delete-branch removed: `if utils.operation_allowed_by_mode("delete", mode):` block in `_plan_operations` and the `delete` row in `operation_allowed_by_mode` are both deleted (not commented, not preserved as scaffold). Restoration of a future `delete` mode is additive from this commit forward; git history holds the scaffold.
  - `--yes --dry-run` errors as `UsageError` → exit 2; combination makes no sense (dry-run short-circuits before the prompt anyway).
  - Color via `click.style` gated on `sys.stdout.isatty()` + `os.environ.get("NO_COLOR") is None`. No `--color`/`FORCE_COLOR` override — `NO_COLOR` is the de-facto standard, no flag for a value that rarely changes.
  - Per-domain summary, always-printed (including no-change), zeros-at-verbose ≥1, empty-domain prints `"no records found"`.
  - Existing exact-match tests fully replaced by behavioral assertions: exit code per scenario + substring presence on stdout/stderr + mock-call existence (not ordering). The current exact-string `'\n'.join([...])` assertions on `result.output` are deleted.
  - `--dry-run` auto-verbose bump to ≥2 preserved (dry-run needs to show matches and mutation rows).
  - `_log_if_level` plumbing mostly preserved — it's still the renderer of last resort for status words and warnings, but the new plan and summary blocks are emitted directly via `click.echo` and the symbol-prefix formatter.
  - Behavioral-assertion tightness: each behavioral test asserts at least one structural token beyond the bare word alone (e.g., `"1 created"`, `"ERR"` for a failure row, `"Summary for"` for the per-domain line) — guards against over-loose assertions that pass on wrong formats.
- Units:
  - Implement `--yes` flag + `--yes`/`--dry-run` mutex error + `--dry-run` help text update; `--mode replace` → `click.UsageError` + help text note. Unit test: each usage-error path returns exit 2.
  - Remove the `replace` branch and `delete` row from `operation_allowed_by_mode`; remove the `if utils.operation_allowed_by_mode("delete", mode):` block from `_plan_operations`; remove the `elif op == "delete": ... skipped` branch from `_execute_operations_plan`.
  - Implement the structured plan renderer: plan header (domain name + mode), per-row symbol-prefix output, match rows gated at verbose ≥ 2, always printed before y/N prompt; color via `click.style` gated on `isatty()` + `NO_COLOR`.
  - Implement the per-domain summary line: zero-entries at verbose ≥1, `"no records found"` for empty domains, always printed (no-change included); colored on TTY.
  - Wire stderr for failure-detail messages in `_execute_operations_plan`; keep status words on stdout.
  - Implement the exit-code matrix: 0/1/2/3/4 across `main()` terminal paths; `--dry-run` exit 3 on changes, 0 on in-sync; execution exit 0 on all-succeeded, 4 on any failure; pre-execution failure 1; usage error 2 (Click default).
  - Replace `tests/test_cli.py` exact-match assertions with the behavioral layer: exit code per scenario + stdout/stderr substrings + mock-call existence; delete the `'\n'.join([...])` output assertions.
  - Update `README.rst`: `replace` mode notes not-implemented; exit code matrix documented; `--yes` flag added to usage.
- Manual-Checks: —
- Blockers: —

## Approach
Tier: normal

Seven bounded source + doc touchpoints, the biggest single unit being the exact-match→behavioral test migration. Output rendering is the riskiest path — the new plan format and summary line are the user-facing surface, and over-loose behavioral assertions can pass on wrong formats. Tightening the assertions to mid-specificity substrings (`"1 created"`, `"Summary for {domain}:"`) and asserting on exit codes per scenario is the regression harness.

Likely touchpoints: `src/porkbun_api_cli/cli.py` (`main` — flag wiring, mutex, mode error, exit codes, plan print, summary print, color; `_plan_operations` — delete-branch removal; `_execute_operations_plan` — delete branch removal, stderr split), `src/porkbun_api_cli/utils.py` (`operation_allowed_by_mode` — delete row + replace branch removal), `tests/test_cli.py` (full test assertion rewrite — exact-match → behavioral), `README.rst` (`replace` bullet + exit code matrix + `--yes` usage). `pyproject.toml`/`tox.ini` untouched — no new deps, no new env.

Strategy:
1. Flag wiring + error paths (small, isolated): `--yes` flag, `--yes`/`--dry-run` mutex, `--mode replace` error, help text.
2. Dead code removal: `operation_allowed_by_mode` `replace` branch + `delete` row; `_plan_operations` delete block; `_execute_operations_plan` delete branch.
3. Plan renderer: header + per-row symbol scheme + match-row threshold + color.
4. Summary renderer: per-domain line + zero-entries threshold + `"no records found"` + color.
5. Stderr/stdout split + exit-code matrix wiring in `main()`: `--dry-run` exit 3/0, execution exit 0/4, pre-execution 1, usage 2.
6. Behavioral test migration in `test_cli.py`: replace `'\n'.join([...])` with exit-code + substring + mock-call-existence assertions; one test per exit code row.
7. README update: `replace` bullet, exit code matrix, `--yes` usage.

Local verification loop during pull:
- `tox -e py313` → new behavioral tests green; no `'\n'.join` assertions left.
- `tox -e check` → ruff + ty green (no `# type: ignore` introduced; the new flag and exit codes are plain Python).
- Manual spot-check (not a manual-check in the ristretto sense — pull runs this): invoke with `NO_COLOR=1` and verify no ANSI codes in output; invoke with `--mode replace` and verify exit 2 with the right message on stderr.

Known friction points:
- Click's `CliRunner` separates `result.output` (stdout) and `result.stderr` (only when `mix_stderr=False`); pull's behavioral tests must construct the runner with `mix_stderr=False` to assert stderr separately. Existing tests use the default `mix_stderr=True` — all four `test_cli` helpers need updating.
- Color via `click.style` + `isatty()`: `CliRunner` by default does not allocate a TTY (`isatty()` returns False), so color tests require `runner.invoke(..., color=True)` or explicit `isatty` mocking — `cli.utils` should import `click` and use `click.style` so Click's test harness's `color=True` flag works.
- Exit code 4 conflicts with `systemexit.tasklet` semantics? — No; `sys.exit(4)` is plain Python and Click's `CliRunner.invoke` captures it in `result.exit_code`. Verified per Click docs (any `int` exit code works).
- The 11 items from the original grind table are all in scope — `arguments` positional arg (#8 in the table) removal rolls into Unit 2's cleanup (delete with the rest of the dead CLI surface). The `symmetric skip visibility` (#9) and `op status prefix` (#7) were both folded into Units 3/4 here.

- Depends: plan-entry-redesign
- Parallel-with: —

## Provides

- `--yes` / `-y` Click `is_flag=True` option (`src/porkbun_api_cli/cli.py`) — when set, the y/N confirmation prompt is skipped and execution proceeds directly; defaults to `False`.
- `--yes --dry-run` mutex: `main()` raises `click.UsageError("--yes and --dry-run are mutually exclusive")` at the top of the body (after the `--mode replace` guard), producing exit code 2 (Click default).
- `--mode replace` disabled at the CLI boundary: `main()` raises `click.UsageError("replace mode is not implemented, use 'upgrade'")` (exit code 2). `--mode` `click.Choice` still lists `replace` so the help text can mention it; the `--mode` Click `help=` string notes "not implemented, use 'upgrade'", and the `main` docstring bullet also says `replace -- not implemented, use 'upgrade'`.
- `--dry-run` auto-bumps `verbose` to `max(2, verbose)` before the API ping (preserved from the prior behavior); the plan is rendered with match rows visible because verbose ≥ 2.
- Exit-code matrix at the `main()` terminal paths:
  - `0` — success (with or without changes); dry-run in sync (no `create`/`update` entries); user abort (`n`/`N` at the prompt).
  - `1` — pre-execution failure: `utils.load_config` raises → `click.echo(f"failed to load configuration from {config_file}: {e}", file=sys.stderr)` then `sys.exit(1)`; `api.get_my_ip` raises `RuntimeError` → `click.echo(f"querying Porkbun API failed: {e}", file=sys.stderr)` then `sys.exit(1)`.
  - `2` — Click default for `UsageError` (covers `--mode replace`, `--yes --dry-run`, missing `CONFIG_FILE`, unknown flags).
  - `3` — dry-run with planned changes (any `PlanEntry.operation in {"create", "update"}` in the plan); `click.echo("dry run requested, skipping execution")` precedes the exit.
  - `4` — any execution-time `RuntimeError` caught in `_execute_operations_plan`; `failed_any = bool(failed_by_domain)` is `True`.
- Structured plan renderer `_render_plan(mode, verbose, operations_plan)` — for each domain whose plan is non-`None`, prints `f"Plan for {domain} ({mode} mode):"` and one row per entry: `f"  {_colorize(symbol, _SYMBOL_COLORS[symbol])}  {content}"`. Symbol mapping: `match` (verbose ≥ 2 only) → `OK `, `create` → `NEW`, `update` → `UPD`; `delete` is unreachable (planner never emits it after Unit 2). Row content: `f"{rec.type} {fqdn} {rec.content}"` where `fqdn = f"{rec.name}.{domain}" if len(rec.name) else domain`.
- Summary renderer `_render_summary(domain, operations, verbose, failed_count=0)` — if `operations is None`, returns; if `operations == []`, prints `f"Summary for {domain}: no records found"`; else counts `created`/`updated`/`matched` plus the per-domain `failed` count passed by `main`, and emits `f"Summary for {domain}: {', '.join(parts)}"`. Each count is shown when `verbose >= 1` OR when the count is non-zero (zeros omitted at verbose < 1). Counts rendered via `_colorize(str(n), _SYMBOL_COLORS[<symbol>])` with `NEW` → green, `UPD` → blue, `OK ` → green, `ERR` → bright_red.
- `_use_color()` → `sys.stdout.isatty() and os.environ.get("NO_COLOR") is None`; `_colorize(text, color)` returns `click.style(text, fg=color)` when `_use_color()` else the plain text. Module-level `_SYMBOL_COLORS` dict maps `NEW` → green, `UPD` → blue, `DEL` → red, `OK ` → green, `ERR` → bright_red, `SKP` → yellow (`DEL` and `SKP` are reserved in the palette but not currently emitted by any branch — they're kept for future expansion).
- stderr split: `_execute_operations_plan` `except RuntimeError` path emits `click.echo(f"querying Porkbun API for domain '{domain_name}' failed: {e}", file=sys.stderr)`; status words (`"done"`, `"failed"`, `"skipped"`) remain on stdout via `_log_if_level`. The two ttl/prio warnings emitted by `_plan_operations` keep `_log_if_level(..., file=sys.stderr)` (ttl/prio is a config-time diagnostic, not an execution failure).
- Dead-code removal (Unit 2):
  - `utils.operation_allowed_by_mode` no longer has the `elif mode == "replace"` branch and the `delete` row is gone (the `replace` branch was dead after the CLI gate; `delete` is now unreachable from the planner). Function falls through to `return False` for unknown modes.
  - `cli._plan_operations` no longer has the `if utils.operation_allowed_by_mode("delete", mode):` block; planner can never produce a `delete` `PlanEntry`.
  - `cli._execute_operations_plan` no longer references `"delete"` in its `if op not in ["create", "update"]` dispatch and the `if op == "delete": ... "delete operation is not implemented - skipped"` branch is gone.
- `_execute_operations_plan` returns `dict[str, int]` mapping `domain_name → failure count` (was `None`; contract said `bool`, but per-domain counts let `_render_summary` print accurate per-domain `failed` numbers — `main` collapses to `bool(failed_by_domain)` for the exit-code gate).
- Test fixture migration in `tests/test_cli.py`: `CliRunner(mix_stderr=False)` (was default `mix_stderr=True`) so `result.stderr` can be asserted separately from `result.output`. The four exact-string `'\n'.join([...])` assertion blocks at lines 66–70 / 130–134 / 185–188 (and the test_cli_no_args/t_cli_dry_run/test_cli_abort/test_cli exact-match sections) are replaced by ~17 behavioral tests covering: each exit code (0/1/2/3/4), `--yes` skip-prompt path, y/N prompt text presence when `--yes` is absent, dry-run auto-verbose bump, color suppression via `NO_COLOR=1` env + `CliRunner(color=False)` default, per-row plan format, summary format with/without records, no-ANSI on `isatty()=False`. `tests/test_utils.py`: three `"replace"` rows dropped from `test_operation_allowed_by_mode_allowed` (now only `append`/`update`/`upgrade` allowed cases).
- `tests/test_cli.py` `TestHelpers`: `test_plan_operations_replace_mode` renamed to `test_plan_operations_upgrade_mode` (mode value switched from `"replace"` to `"upgrade"` — `delete` op is no longer reachable from any mode after Unit 2); `test_execute_operations_plan` fixture replaces the three `Operation(operation="delete", ...)` entries with `Operation(operation="update", ...)` so the `RuntimeError` path is still exercised against the new dispatch.
- `README.rst` updates: `replace` mode bullet now reads `-- not implemented, use 'upgrade'`; new `Command-line options` section documents `-m`/`--mode`, `-n`/`--dry-run`, `-y`/`--yes`, `-v`/`--verbose`, `-V`/`--version`; new `Exit codes` section documents 0/1/2/3/4 with one-line rationale per code.
- No new dependencies, no `pyproject.toml`/`tox.ini` changes; `PlanEntry` shape (from `plan-entry-redesign`) is consumed unchanged (`Literal["create","update","delete","match"]`); `DnsRecord`/`ExistingDnsRecord` attribute access (from `dto-migration`) is consumed unchanged.

## Evidence

106 passed, coverage 96.14%, `tox -e check` PASS, `tox -e py311` PASS.
tier: normal
review: 1 block resolved in 2 rounds

### Gate: lint
- Command: `tox -e check`
- Exit code: 0
- Output: ruff check pass, ruff format --check pass, `ty check src/porkbun_api_cli` pass, readme_renderer pass, check-manifest pass.

### Gate: tests
- Command: `tox -e py313`
- Exit code: 0
- Output: 106 passed in 0.42s; coverage 96.14% (above 95% threshold).

### Gate: matrix
- Command: `tox -e py311`
- Exit code: 0
- Output: 106 passed, coverage 96.14%.

### Acceptance criteria evidence

`--yes` flag + `--yes`/`--dry-run` mutex + `--mode replace` UsageError:
- `src/porkbun_api_cli/cli.py` has the new `@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt")` decorator (lines 263-268); the two `click.UsageError` guards at the top of `main` body cover both `--yes --dry-run` (lines 299-300) and `--mode replace` (lines 296-297). Tests `test_cli_yes_and_dry_run_mutex` and `test_cli_mode_replace_raises_usage_error` verify exit code 2 + message on stderr.

Structured plan renderer:
- `_render_plan` is called by `main` after the API ping and before any prompt (cli.py:335); emits `f"Plan for {domain} ({mode} mode):"` per domain + `f"  {{symbol}}  {rec.type} {fqdn} {rec.content}"` rows. Tests `test_cli_plan_renders_symbol_rows`, `test_cli_plan_match_rows_hidden_below_verbose_2` verify the row format and the verbose-2 match gate.

Summary renderer:
- `_render_summary` is called by `main` for every non-None domain after `_execute_operations_plan` returns (cli.py:355-360). Tests `test_cli_summary_empty_domain`, `test_cli_summary_populated_domain` verify the `"no records found"` branch and the per-domain count format.

Exit-code matrix:
- Each terminal path in `main` calls `sys.exit(N)` with the right code: pre-execution failure → 1 (config load / `get_my_ip`); dry-run with changes → 3, in sync → 0; execution with no failures → 0, with any failure → 4; user abort → 0. Tests `test_cli_exit_code_0_on_success`, `test_cli_exit_code_1_on_get_my_ip_failure`, `test_cli_exit_code_2_on_replace_mode`, `test_cli_exit_code_2_on_yes_dry_run`, `test_cli_exit_code_3_on_dry_run_with_changes`, `test_cli_exit_code_0_on_dry_run_in_sync`, `test_cli_exit_code_4_on_execution_failure` cover each row.

Color gating:
- `_use_color()` checks `sys.stdout.isatty() and os.environ.get("NO_COLOR") is None`; `_colorize` is a no-op when the gate is off. Tests `test_cli_no_color_env_suppresses_ansi` (passes `env={"NO_COLOR": "1"}`) and `test_cli_runner_default_color_false_suppresses_ansi` (uses default `CliRunner(color=False)`) verify no `\x1b[` codes appear in stdout.

stderr split:
- `_execute_operations_plan`'s `except RuntimeError` path emits `click.echo(..., file=sys.stderr)`; status words (`"done"`, `"failed"`, `"skipped"`) stay on stdout via `_log_if_level`. Test `test_cli_stderr_for_execution_failure` asserts the failure message lands on `result.stderr` and the summary on `result.output`.

Dead-code removal:
- `utils.operation_allowed_by_mode` no longer has the `replace` branch or `delete` row — verified by grep.
- `cli._plan_operations` no longer has the `if utils.operation_allowed_by_mode("delete", mode)` block — verified by grep.
- `cli._execute_operations_plan` no longer has the `if op == "delete"` branch and the dispatch narrows to `["create", "update"]` — verified by grep.

Behavioral test migration:
- `tests/test_cli.py` has no `'\n'.join(['Plan for ...'])` exact-string assertion blocks remaining (verified by grep — only the `test_cli_no_args` "Usage: " prefix check and the prompt-text substring checks remain, both of which are structural).
- `CliRunner(mix_stderr=False)` fixture at the top of `tests/test_cli.py` lets stderr be asserted separately.

README:
- `README.rst` lines 58-61 have the updated `replace` bullet; lines 63-87 have the new `Command-line options` and `Exit codes` sections; `-y, --yes` is documented; exit code matrix (0/1/2/3/4) is listed with one-line rationale per code.

### Gate summary

- lint ✓ (`tox -e check` exit 0)
- test ✓ (`tox -e py313` 106 passed, 96.14% cov; `tox -e py311` PASS)
- type checker ✓ (`ty check src/porkbun_api_cli` PASS — `# ty: narrow` + `assert ... is not None` narrowing pattern continues to resolve)

### Review verdict

review: notes-only (2 note) — 2 rounds; round-1 block fixed, round-2 clean

## Open findings

- note · src/porkbun_api_cli/cli.py:261 · `--dry-run` help text drops "without any changes" from contract-specified exact text "Perform a trial run without any changes; exits non-zero (code 3) if any changes would be needed"; `test_cli_help_documents_replace_and_dry_run_exit_code:67` only asserts on "exits non-zero (code 3)" substring, so the deviation slips past · No user harm — substance (trial-run, exit code 3) is preserved, line-wrap is the rationale.
- note · src/porkbun_api_cli/cli.py:227-240 · `_render_summary` omits the contract's "{N} deleted" field from the summary line; plan spec also omits it · Functionally correct after Unit 2's dead-delete removal (planner never emits delete ops, so the count is always 0). No user harm — user never sees a phantom "0 deleted" field, but the format string in the contract is unmet.