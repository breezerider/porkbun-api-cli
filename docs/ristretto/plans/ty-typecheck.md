# ty-typecheck — Add type annotations to src/; ty blocking in check env

## Spec
- Source: idea
- Flight: build-modernization
- Goal: every `src/porkbun_api_cli/*.py` function carries param + return annotations; ty runs in `check` and exits non-zero on violation; no `# type: ignore`, no `cast`, no `ignore_missing_imports`.

## Contract
- Acceptance:
  - [auto] `src/porkbun_api_cli/api.py`: `__init__`, `_query_api`, `list_dns_records`, `create_record`, `update_record`, `get_my_ip` all annotated (params + returns).
  - [auto] `src/porkbun_api_cli/utils.py`: `compare_record_by_content_ttl_prio`, `compare_record_by_name_type`, `operation_allowed_by_mode`, `load_config` all annotated (params + returns).
  - [auto] `src/porkbun_api_cli/cli.py`: `_print_version`, `_log_if_level`, `_collect_existing_dns_records`, `_plan_operations`, `_execute_operations_plan`, `main` all annotated (params + returns).
  - [auto] A module (`types.py` or co-located in `utils.py` — pull's call) defines `DnsRecord` and `ExistingDnsRecord` as `TypedDict`s with `name: str`, `type: str`, `content: str`, `ttl: NotRequired[str]`, `prio: NotRequired[str]`; `ExistingDnsRecord` adds `id: str` and `name` is the FQDN (not subdomain). `Operation` as `TypedDict` with `operation: str`, `new: DnsRecord | None`, `existing: ExistingDnsRecord | None` — **both fields required (not `NotRequired`)**; the plan builder in `_plan_operations` always sets both, they are nullable not absent.
  - [auto] `pyproject.toml` contains `[tool.ty.environment]` with `python-version = "3.11"` (NOT top-level `[tool.ty] python-version` — ty 0.0.79 rejects that as unknown field) and **no `ignore_missing_imports`** key anywhere under `[tool.ty]`.
  - [auto] `[testenv:check]` in `tox.ini` uses `usedevelop = true` (replaces `skip_install = true`); `deps` includes `ty` (version-pinned), `types-PyYAML`, `types-requests` (stub dev-deps); `click` ships `py.typed` (no stub). Runtime deps `click`/`pyyaml`/`requests` resolve via the editable install, not duplicated in `deps`.
  - [auto] `[testenv:check]` `commands` includes `ty check src/porkbun_api_cli` as a blocking step (exits non-zero → `check` fails), positioned after `ruff check` + `ruff format --check`.
  - [auto] `tox -e check` exits 0 (ruff + ty + setup check + check-manifest all green).
  - [auto] `tox -e py313` exits 0 (annotations don't break runtime; tests pass unchanged).
  - [auto] No `# type: ignore` comments added to `src/porkbun_api_cli/*.py`.
  - [auto] No `typing.cast` calls added to `src/porkbun_api_cli/*.py`.
  - [auto] `assert` statements added to `src/porkbun_api_cli/*.py` for type narrowing are permitted, each preceded by a `# ty: narrow` comment naming the invariant (e.g. `# ty: narrow — new is non-None on create/update branch`).
  - [auto] `_query_api` return type is `tuple[Any, bool]` (NOT `tuple[str | None, bool]` — JSON response from Porkbun API is untyped at the boundary; callers' return types enforce the expected shape).
  - [auto] `_execute_operations_plan` loop body guarded: `if operations is None: continue` as the first line inside `for domain_name, operations in operations_plan.items():` (dict values are `list[Operation] | None`, None = query failure).
  - [auto] `_execute_operations_plan` narrows `record` via `assert record is not None` after each `record = operation["new"]` / `record = operation["existing"]` access, each `assert` preceded by `# ty: narrow` comment.
  - [auto] A `TODO` comment at the top of the module holding `DnsRecord`/`ExistingDnsRecord`/`Operation` reads: `# TODO: DTOs need a refactor — TypedDicts are a stopgap; dataclass migration is a follow-up feature.`
- Provides: `DnsRecord`, `ExistingDnsRecord`, `Operation` TypedDicts (from this feature's `src/`); annotated signatures on every `src/` function; ty as blocking gate in `check`; stub deps `types-PyYAML` + `types-requests` in `check`; `usedevelop = true` in `check` env (runtime deps resolvable).
- Consumes: ruff `check` env shape from ruff-migration (the `deps` + `commands` list this feature extends); Python floor 3.11 from py-version-floor (enables `NotRequired`, `X | None` syntax).
- Decisions:
  - Annotation depth → TypedDict aliases only, no dataclass migration. `DnsRecord` (subdomain `name`), `ExistingDnsRecord` (FQDN `name`, has `id`). Stopgap measure; follow-up refactor feature deferred (see memo `docs/ristretto/memos.md`).
  - TODO recorded inline: `# TODO: DTOs need a refactor — TypedDicts are a stopgap; dataclass migration is a follow-up feature.`
  - ty gate → blocking in `check` (not a separate `tox -e ty` env). Full-annotate this round means ty passes day one; making it enforce.
  - stub deps → add `types-PyYAML`, `types-requests` to `check` deps. `click` ships `py.typed` (no stub). No `ignore_missing_imports` — ty enforces real dependency signatures.
  - `check` env install → `usedevelop = true` (replaces `skip_install = true`). Without the package + runtime deps installed, ty raises `unresolved-import` on `import click`/`requests`/`yaml` once `cli.py` annotates Click types. `usedevelop` makes the package importable and resolves runtime deps without duplicating them in `deps`.
  - ty config location → `[tool.ty.environment] python-version = "3.11"` in `pyproject.toml`. Top-level `[tool.ty] python-version` is rejected by ty 0.0.79 as unknown field (verified: `expected one of environment, src, rules, terminal, analysis, overrides`).
  - `_query_api` return → `tuple[Any, bool]`. Original plan proposed `tuple[str | None, bool]`; verified this produces 7 ty errors across `api.py` callers (`invalid-return-type` when `data: str | None` returned where `list[ExistingDnsRecord]` or `str` expected; `unsupported-operator` on `"msg: " + data` where `data` is `str | None`). JSON response from Porkbun API is untyped at the boundary — `Any` is the honest type; callers' return types (`list[ExistingDnsRecord]`, `str`) enforce the expected shape. Avoids `assert`/`cast`/`# type: ignore` at the API boundary.
  - `Operation.new` / `Operation.existing` → **required fields** (`new: DnsRecord | None`, `existing: ExistingDnsRecord | None`), NOT `NotRequired`. Original plan used `NotRequired`; verified this produces 5 `not-subscriptable` + 2 `invalid-argument-type` errors in `_execute_operations_plan` because ty can't distinguish "field absent" (NotRequired) from "field present but None" — both look like `None` on access. The builder in `_plan_operations` always sets both fields (`{"operation": "update", "new": record, "existing": entry}`), so they are required-but-nullable, not absent-when-unused.
  - `assert` for type narrowing → **permitted**, each preceded by `# ty: narrow` comment naming the invariant. Distinguished from `# type: ignore` (silencing) and `cast` (unchecked suppression): `assert` is a runtime check that fails loudly if the invariant is wrong. Used in `_execute_operations_plan` to narrow `operation["new"]`/`operation["existing"]` after branch dispatch (`if op == "create": ...`) — ty cannot narrow a TypedDict field based on a *different* field's value (`operation["operation"]`), so `assert record is not None` is the runtime guard. See memo `docs/ristretto/memos.md` for the follow-up to replace these with per-op TypedDicts + `Literal` discriminators.
  - `for operation in operations` loop → guarded with `if operations is None: continue`. `operations_plan` values are `list[Operation] | None` (None = query failure per `_collect_existing_dns_records`); iterating `None` raises `TypeError` at runtime and `not-iterable` in ty. Matches the existing None-means-failure pattern.
  - `DnsRecord.name` vs `ExistingDnsRecord.name` semantic split → subdomain vs FQDN. TypedDict can't enforce the distinction at construction, only field presence/types; documented in TODO + memo. `compare_record_by_name_type` builds FQDN from subdomain + domain — annotation captures `target: DnsRecord`, `other: ExistingDnsRecord`, return `bool`.
  - `load_config` return → `dict[str, Any]` (config is nested YAML; a strict `TypedConfig` is a bigger refactor, deferred alongside DTO TODO). `apikey: str`, `secretapikey: str`, `endpoint: str` access patterns stay `Any`-typed at the boundary; `**config["api"]` unpacking in `main` is `Any`-permissive.
  - `main` (Click entrypoint) → annotated `(config_file: str, mode: str, dry_run: bool, verbose: int, arguments: tuple[str, ...]) -> None`. Click decorators stay; annotation is on the inner function signature.
  - `from __future__ import annotations` → added to all three src modules (and `types.py` if separate). Makes `X | None` and `dict[...]` lazy-evaluated as strings, avoiding runtime `TypeError` on 3.11 if `__annotations__` is inspected at import time. Cheap insurance, no behavior change.
- Units:
  - Define `DnsRecord`, `ExistingDnsRecord`, `Operation` TypedDicts (in `utils.py` or new `types.py` — pull decides) + TODO comment header. Fields per Decisions: `Operation.new`/`existing` required (no `NotRequired`).
  - Annotate `utils.py` (4 funcs): `compare_record_by_content_ttl_prio(target: DnsRecord, other: ExistingDnsRecord) -> bool`, `compare_record_by_name_type(domain_name: str, target: DnsRecord, other: ExistingDnsRecord) -> bool`, `operation_allowed_by_mode(operation: str, mode: str) -> bool`, `load_config(config_file_path: str) -> dict[str, Any]`.
  - Annotate `api.py` (6 funcs/methods): `__init__(self, apikey: str, secretapikey: str, endpoint: str) -> None`, `_query_api(self, endpoint: str, payload: Mapping[str, Any] | None = None, datafield: str | None = None) -> tuple[Any, bool]` (note: `Mapping` not `dict` — TypedDict not assignable to `dict` in ty; `Mapping` accepts it), `list_dns_records(self, domain: str) -> list[ExistingDnsRecord]`, `create_record(self, domain: str, record: DnsRecord) -> str`, `update_record(self, domain: str, record_id: str, new_record: DnsRecord) -> None`, `get_my_ip(self) -> str`.
  - Annotate `cli.py` (6 funcs): `_print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None`, `_log_if_level(level: int, verbosity: int, message: str, file: TextIO | None = None, nl: bool = True) -> None`, `_collect_existing_dns_records(api: PorkbunAPI.PorkbunAPI, domain_names: list[str], verbose: int) -> dict[str, list[ExistingDnsRecord] | None]`, `_plan_operations(mode: str, verbose: int, existing_domains: dict[str, list[ExistingDnsRecord] | None], config_domains: dict[str, list[DnsRecord]]) -> dict[str, list[Operation] | None]`, `_execute_operations_plan(api: PorkbunAPI.PorkbunAPI, verbose: int, operations_plan: dict[str, list[Operation] | None]) -> None`, `main(config_file: str, mode: str, dry_run: bool, verbose: int, arguments: tuple[str, ...]) -> None`. Add `if operations is None: continue` guard + `# ty: narrow` asserts in `_execute_operations_plan`.
  - Add `[tool.ty.environment] python-version = "3.11"` to `pyproject.toml`; flip `[testenv:check]` to `usedevelop = true`, add `ty==<pin>`, `types-PyYAML`, `types-requests` to `deps`; add `ty check src/porkbun_api_cli` to `commands` after ruff steps.
- Manual-Checks: —
- Blockers: —

## Approach
Tier: normal

Three src modules, 14 functions, ~200 LOC. TypedDicts first (one unit, defines the vocabulary), then annotate module-by-module (three units), then wire ty (one unit). Each unit is a red→green cycle: add types → run `uvx --from ty ty check src/porkbun_api_cli --python /usr/bin/python3.13` until that module passes → next. Final gate: `tox -e check` green (ty wired in).

Likely touchpoints: `src/porkbun_api_cli/utils.py` (TypedDicts + 4 annotations) or new `src/porkbun_api_cli/types.py`, `src/porkbun_api_cli/api.py` (6 annotations, `Mapping` import), `src/porkbun_api_cli/cli.py` (6 annotations, Click types, None guard, assert narrows), `pyproject.toml` (`[tool.ty.environment]`), `tox.ini` (`[testenv:check]` `usedevelop` + deps + commands). Tests untouched — TypedDicts are structurally compatible with the existing dict fixtures, so `test_*.py` stays valid.

Strategy:
1. TypedDicts + TODO in `utils.py` (co-locate — avoids a new file for 3 small types) or `types.py` (pull decides; `types.py` is cleaner if `utils.py` gets crowded). `Operation.new`/`existing` required (no `NotRequired`). Import `from typing import TypedDict, NotRequired, Any` and `from __future__ import annotations` at top of every annotated module.
2. `utils.py` annotations: straightforward, `DnsRecord`/`ExistingDnsRecord` params, `bool`/`dict` returns.
3. `api.py` annotations: `_query_api` return is `tuple[Any, bool]` (JSON boundary untyped); `payload` param is `Mapping[str, Any] | None` (NOT `dict[str, Any] | None` — TypedDict not assignable to `dict` in ty, verified: `A TypedDict is not usually assignable to any dict[..]`); `list_dns_records` returns `list[ExistingDnsRecord]`; `create_record` returns `str`. Callers do `return data` (Any assignable to any return type) and `"msg: " + data` (Any supports `+`) — no asserts needed in `api.py`.
4. `cli.py` annotations: Click types (`click.Context`, `click.Parameter`) for `_print_version`; `PorkbunAPI` imported from `api` (already aliased as `PorkbunAPI` module in current code — keep alias); `main` is the decorated entrypoint, annotate the inner signature. `_log_if_level` uses `TextIO` from `typing` for `file`. `_execute_operations_plan` gets two structural fixes: (a) `if operations is None: continue` as first line of the domain loop (dict values are `list | None`); (b) `# ty: narrow` + `assert record is not None` after each `record = operation["new"]` / `record = operation["existing"]` access — ty can't narrow TypedDict fields across branches, assert is the runtime guard.
5. ty config + gate: `[tool.ty.environment] python-version = "3.11"` (NOT top-level); `check` env flips to `usedevelop = true` (runtime deps resolvable via editable install), adds `ty==<pin>` + `types-PyYAML` + `types-requests` to `deps`, adds `ty check src/porkbun_api_cli` to `commands` after ruff steps.

`from __future__ import annotations` at the top of all three src modules (+ `types.py` if separate): makes `X | None` and `dict[...]` lazy-evaluated as strings, avoiding any runtime `TypeError` on 3.11 if `__annotations__` is inspected at import time. Cheap insurance, no behavior change.

Local verification loop during pull (run after each unit):
- `uvx --from ty ty check src/porkbun_api_cli --python /usr/bin/python3.13` → should converge to 0 errors as units land.
- `tox -e py313` after each unit → tests stay green (annotations don't change runtime; TypedDicts compatible with dict fixtures).
- Final: `tox -e check` → ruff + ty + setup + manifest all green.

Known friction points (verified against ty 0.0.79 in this repo):
- `_execute_operations_plan` loop: `operations_plan.items()` yields `list[Operation] | None`; the `if operations is None: continue` guard is mandatory, not optional.
- `Operation.new`/`existing` access: ty sees `DnsRecord | None` (or `ExistingDnsRecord | None`) and can't narrow on `if op == "create"` (different field). `assert record is not None` with `# ty: narrow` comment is the fix. 3 asserts in this function.
- `check` env without runtime deps: `skip_install = true` + annotated `import click` → `unresolved-import`. `usedevelop = true` is the fix; adding deps to `deps` list duplicates them unnecessarily.
- `_query_api` return `tuple[str | None, bool]`: produces 7 errors across callers. `tuple[Any, bool]` is the fix — JSON is untyped at the boundary, `Any` is honest, callers' return types enforce shape.

- Depends: ruff-migration (#2 — this feature extends its `check` env `deps` + `commands`; also `usedevelop = true` flips the env that ruff-migration finalized), py-version-floor (#1 — `NotRequired` + `X | None` syntax require 3.11+ floor).
- Parallel-with: uv-lockfile (#4 — orthogonal; lockfile doesn't affect annotations or ty).

status: planned