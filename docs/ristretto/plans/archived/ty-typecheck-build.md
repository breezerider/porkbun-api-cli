# ty-typecheck — Build Plan

tier: normal

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

## ty toolchain verification

Verified against `ty 0.0.79` (current stable, `uv tool run --from ty ty --version`):

1. `[tool.ty.environment] python-version = "3.11"` accepted (no unknown-field error), catches `invalid-return-type` on real violation → exit 1, `All checks passed!` → exit 0 on clean.
2. `tuple[Any, bool]` return for a `_query_api`-shaped function passes; callers returning `data` (`Any`) satisfy `list[ExistingDnsRecord]` / `str` return types.
3. `payload: Mapping[str, Any] | None` param accepts a `DnsRecord` (TypedDict) argument — `Mapping` from `collections.abc` required (ty reports `A TypedDict is not usually assignable to any dict[..]` if `dict` used).
4. `Operation` with required `new: DnsRecord | None` / `existing: ExistingDnsRecord | None` (no `NotRequired`) passes.
5. `_execute_operations_plan` loop with `if operations is None: continue` + 3 `# ty: narrow` + `assert record is not None` placements (2 on `record = operation["new"]` / `operation["existing"]`, 1 on `operation["existing"]["id"]` access in the update `try` branch) → `All checks passed!`.

**Pin:** `ty==0.0.79` (current stable).

**Correction to the contract's Decisions/memo "Count: 3 asserts":** the criterion 24 text names only the `record = operation["new"]` / `record = operation["existing"]` accesses (2 asserts). Verified at `/tmp/ty-verify` with the actual loop shape: a **3rd assert is required** on `operation["existing"]["id"]` in the `op == "update"` `try` branch — `operation["existing"]` re-accessed there, ty sees `ExistingDnsRecord | None` again, `["id"]` subscript fails (`not-subscriptable`). Without the 3rd assert, `tox -e check` (criterion 17) does not pass. The memos "Count: 3 asserts" line is the authoritative intent; the contract criterion 24 text under-names the placements. The 3rd assert is **bound** (criterion 17 transitively requires it). All three asserts get `# ty: narrow` comments.

## Touchpoints

### 1. `src/porkbun_api_cli/utils.py` — TypedDicts + 4 annotations

**Current state** (no annotations, no TypedDicts, no `from __future__`):

```python
1: import yaml
2:
3:
4: def compare_record_by_content_ttl_prio(target, other):
...
23: def compare_record_by_name_type(domain_name, target, other):
...
39: def operation_allowed_by_mode(operation, mode):
...
64: def load_config(config_file_path):
...
100:     return config
```

**Changes:**

a. `__main__`/module header — add `from __future__ import annotations` as line 1, then TODO + TypedDict block below the `import yaml` (or build the 3 TypedDicts + TODO above the imports — `from __future__` MUST be the first statement).

b. Add imports:
```python
from collections.abc import Mapping
from typing import Any
from typing import NotRequired
from typing import TextIO
from typing import TypedDict
```
(`TextIO` is needed by `cli.py` not `utils.py` — skip it here unless `types.py` split; `Mapping` is needed by `api.py` not `utils.py` — skip here too. Only `Any`, `NotRequired`, `TypedDict` needed in `utils.py`.)

c. Add TODO header + 3 TypedDicts (co-locate in `utils.py` — pull's call; avoids a new file for 3 small types, and `cli.py`/`api.py` already import from `.utils` or can import from it):

```python
# TODO: DTOs need a refactor — TypedDicts are a stopgap; dataclass migration is a follow-up feature.


class DnsRecord(TypedDict):
    name: str
    type: str
    content: str
    ttl: NotRequired[str]
    prio: NotRequired[str]


class ExistingDnsRecord(TypedDict):
    name: str
    type: str
    content: str
    ttl: NotRequired[str]
    prio: NotRequired[str]
    id: str


class Operation(TypedDict):
    operation: str
    new: DnsRecord | None
    existing: ExistingDnsRecord | None
```

d. Annotate 4 functions:

```python
def compare_record_by_content_ttl_prio(target: DnsRecord, other: ExistingDnsRecord) -> bool:
def compare_record_by_name_type(domain_name: str, target: DnsRecord, other: ExistingDnsRecord) -> bool:
def operation_allowed_by_mode(operation: str, mode: str) -> bool:
def load_config(config_file_path: str) -> dict[str, Any]:
```

e. `load_config` body line 97: `config["domains"] = []` — ty infers `config` as `dict[str, Any]` from `yaml.safe_load` (returns `Any`); the `if config["domains"] is None:` branch is fine under `Any`. No body edits needed.

### 2. `src/porkbun_api_cli/api.py` — 6 annotations + `Mapping` import

**Current state** (no annotations):

```python
1: import json
2:
3: import requests
4:
5:
6: class PorkbunAPI:
7:     def __init__(self, apikey, secretapikey, endpoint):
...
10:     def _query_api(self, endpoint, payload=None, datafield=None):
...
50:     def list_dns_records(self, domain,):
...
61:     def create_record(self, domain, record):
...
78:     def update_record(self, domain, record_id, new_record):
...
96:     def get_my_ip(self):
```

**Changes:**

a. Add `from __future__ import annotations` as line 1. Add imports after `import requests`:
```python
from collections.abc import Mapping
from typing import Any
```
And import the TypedDicts:
```python
from .utils import DnsRecord
from .utils import ExistingDnsRecord
```
(ruff `force-single-line = true` → one import per line, no multi-line grouping.)

b. Annotate 6 functions:

```python
class PorkbunAPI:
    def __init__(self, apikey: str, secretapikey: str, endpoint: str) -> None:
        ...

    def _query_api(
        self, endpoint: str, payload: Mapping[str, Any] | None = None, datafield: str | None = None
    ) -> tuple[Any, bool]:
        ...

    def list_dns_records(self, domain: str) -> list[ExistingDnsRecord]:
        ...

    def create_record(self, domain: str, record: DnsRecord) -> str:
        ...

    def update_record(self, domain: str, record_id: str, new_record: DnsRecord) -> None:
        ...

    def get_my_ip(self) -> str:
        ...
```

c. Body lines unchanged — `return data` (where `data: Any`) satisfies `list[ExistingDnsRecord]`, `str`, `None` return types under `Any`. `"msg: " + data` works (Any supports `+`). No asserts/casts/ignores needed in `api.py`.

d. `_query_api` line 12: `payload = {}` — ty sees `payload: Mapping[str, Any] | None`, assigning `{}` (a `dict`, which is a `Mapping`) is fine.

### 3. `src/porkbun_api_cli/cli.py` — 6 annotations + None guard + 3 narrow asserts

**Current state** (lines 1–10, no annotations):

```python
1: #!/usr/bin/env python3
2:
3: import sys
4:
5: import click
6:
7: from . import __version__
8: from . import api as PorkbunAPI
9: from . import utils
10:
```

**Changes:**

a. Add `from __future__ import annotations` after the shebang (line 2, before `import sys`). Add imports:
```python
from typing import TextIO

from .utils import DnsRecord
from .utils import ExistingDnsRecord
from .utils import Operation
```
(ruff `force-single-line = true`.)

b. Annotate 6 functions:

```python
def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None:
def _log_if_level(level: int, verbosity: int, message: str, file: TextIO | None = None, nl: bool = True) -> None:
def _collect_existing_dns_records(
    api: PorkbunAPI.PorkbunAPI, domain_names: list[str], verbose: int
) -> dict[str, list[ExistingDnsRecord] | None]:
def _plan_operations(
    mode: str,
    verbose: int,
    existing_domains: dict[str, list[ExistingDnsRecord] | None],
    config_domains: dict[str, list[DnsRecord]],
) -> dict[str, list[Operation] | None]:
def _execute_operations_plan(
    api: PorkbunAPI.PorkbunAPI, verbose: int, operations_plan: dict[str, list[Operation] | None]
) -> None:
def main(config_file: str, mode: str, dry_run: bool, verbose: int, arguments: tuple[str, ...]) -> None:
```

c. `_execute_operations_plan` loop body (current lines 100–130) — 3 structural edits:

**Current:**
```python
100:     for domain_name, operations in operations_plan.items():
101:         _log_if_level(1, verbose, f"- altering domain '{domain_name}'")
102:         for operation in operations:
103:             op = operation["operation"]
104:             if op not in ["create", "update", "delete"]:
105:                 _log_if_level(0, verbose, f"unknown operation '{op}'")
106:                 continue
107:
108:             if op in ["create", "update"]:
109:                 record = operation["new"]
110:                 if len(record["name"]):
111:                     name = f"{record['name']}.{domain_name}"
112:                 else:
113:                     name = domain_name
114:             elif op == "delete":
115:                 record = operation["existing"]
116:                 name = record["name"]
117:             _log_if_level(1, verbose, f"\t{op} {record['type']}-record '{name}' ... ", nl=False)
118:
119:             try:
120:                 if op == "create":
121:                     api.create_record(domain_name, record)
122:                 elif op == "update":
123:                     api.update_record(domain_name, operation["existing"]["id"], record)
124:                 elif op == "delete":
125:                     _log_if_level(0, verbose, f"{op} operation is not implemented - skipped")
```

**After:**
```python
    for domain_name, operations in operations_plan.items():
        if operations is None:
            continue
        _log_if_level(1, verbose, f"- altering domain '{domain_name}'")
        for operation in operations:
            op = operation["operation"]
            if op not in ["create", "update", "delete"]:
                _log_if_level(0, verbose, f"unknown operation '{op}'")
                continue

            if op in ["create", "update"]:
                record = operation["new"]
                # ty: narrow — new is non-None on create/update branch
                assert record is not None
                if len(record["name"]):
                    name = f"{record['name']}.{domain_name}"
                else:
                    name = domain_name
            elif op == "delete":
                record = operation["existing"]
                # ty: narrow — existing is non-None on delete branch
                assert record is not None
                name = record["name"]
            _log_if_level(1, verbose, f"\t{op} {record['type']}-record '{name}' ... ", nl=False)

            try:
                if op == "create":
                    api.create_record(domain_name, record)
                elif op == "update":
                    existing = operation["existing"]
                    # ty: narrow — existing is non-None on update branch (update requires a matched record)
                    assert existing is not None
                    api.update_record(domain_name, existing["id"], record)
                elif op == "delete":
                    _log_if_level(0, verbose, f"{op} operation is not implemented - skipped")
```

**3 `# ty: narrow` + `assert` placements:**
1. After `record = operation["new"]` (create/update branch) — narrows `DnsRecord | None` → `DnsRecord`.
2. After `record = operation["existing"]` (delete branch) — narrows `ExistingDnsRecord | None` → `ExistingDnsRecord`.
3. After `existing = operation["existing"]` (update `try` branch, before `existing["id"]` access) — narrows `ExistingDnsRecord | None` → `ExistingDnsRecord` so `["id"]` subscript is valid.

**None guard placement:** `if operations is None: continue` immediately after `for domain_name, operations in operations_plan.items():`, before the `_log_if_level` call — `operations_plan` values are `list[Operation] | None`; iterating `None` raises at runtime.

d. `main` is a Click-decorated function; the annotation goes on the inner function signature (the decorator stack stays above the `def main(...)` line). `arguments: tuple[str, ...]` matches Click's `nargs=-1` (positional args as a tuple).

e. `_collect_existing_dns_records` line 25: `result = {}` → ty infers `dict[str, list[ExistingDnsRecord] | None]` from the `-> ...` return type; `result[domain_name] = existing_records` where `existing_records` is `list[ExistingDnsRecord] | None` (from the `except`/`else` branches) — fine.

f. `_plan_operations` line 47: `planned_operations = {}` → ty infers `dict[str, list[Operation] | None]` from return type; lines 54/58 assign `None`, line 93 assigns `operations` (a `list[Operation]`) — fine.

### 4. `pyproject.toml` — `[tool.ty.environment]` section

**Current state** (no `[tool.ty]` section exists; file ends at line 144 with `[tool.pytest.ini_options]`):

```toml
132: [tool.pytest.ini_options]
...
144: filterwarnings = ["error"]
```

**Add** (at end of file, after line 144):

```toml

[tool.ty.environment]
python-version = "3.11"
```

**Constraints verified against ty 0.0.79:**
- `python-version` lives under `[tool.ty.environment]`, NOT top-level `[tool.ty]` (rejected as unknown field: `expected one of environment, src, rules, terminal, analysis, overrides`).
- No `ignore_missing_imports` key anywhere under `[tool.ty]`.

### 5. `tox.ini` — `[testenv:check]`

**Current state** (lines 40–53):

```ini
40: [testenv:check]
41: deps =
42:     ruff==0.16.6
43:     docutils
44:     check-manifest
45:     readme-renderer
46:     pygments
47: skip_install = true
48: commands =
49:     ruff check .
50:     ruff format --check --diff .
51:     python setup.py check --strict --metadata --restructuredtext
52:     check-manifest .
```

**Replace with:**

```ini
[testenv:check]
deps =
    ruff==0.16.6
    ty==0.0.79
    types-PyYAML
    types-requests
    docutils
    check-manifest
    readme-renderer
    pygments
usedevelop = true
commands =
    ruff check .
    ruff format --check --diff .
    ty check src/porkbun_api_cli
    python setup.py check --strict --metadata --restructuredtext
    check-manifest .
```

**Key changes:**
- `skip_install = true` → `usedevelop = true` (editable install resolves `click`/`pyyaml`/`requests` runtime deps without duplicating them in `deps`).
- `deps` adds `ty==0.0.79`, `types-PyYAML`, `types-requests` (stub dev-deps for ty to check `import yaml`/`import requests` signatures).
- `commands` adds `ty check src/porkbun_api_cli` after `ruff format --check --diff .`, before `python setup.py check`. ty exits non-zero → `check` fails.

## Tests

Red-first: run each check before editing — it should fail (wrong count / exit 1). After editing, it passes.

### Criterion 1: `api.py` 6 functions annotated

**Red-first:** `grep -c '^    def __init__(self, apikey: str' src/porkbun_api_cli/api.py` → 0.

```bash
grep -c 'def __init__(self, apikey: str, secretapikey: str, endpoint: str) -> None' src/porkbun_api_cli/api.py
grep -c 'def _query_api(' src/porkbun_api_cli/api.py
grep -c '-> tuple\[Any, bool\]' src/porkbun_api_cli/api.py
grep -c 'def list_dns_records(self, domain: str) -> list\[ExistingDnsRecord\]' src/porkbun_api_cli/api.py
grep -c 'def create_record(self, domain: str, record: DnsRecord) -> str' src/porkbun_api_cli/api.py
grep -c 'def update_record(self, domain: str, record_id: str, new_record: DnsRecord) -> None' src/porkbun_api_cli/api.py
grep -c 'def get_my_ip(self) -> str' src/porkbun_api_cli/api.py
# each: 1
```

### Criterion 2: `utils.py` 4 functions annotated

**Red-first:** `grep -c 'def compare_record_by_content_ttl_prio(target: DnsRecord' src/porkbun_api_cli/utils.py` → 0.

```bash
grep -c 'def compare_record_by_content_ttl_prio(target: DnsRecord, other: ExistingDnsRecord) -> bool' src/porkbun_api_cli/utils.py
grep -c 'def compare_record_by_name_type(domain_name: str, target: DnsRecord, other: ExistingDnsRecord) -> bool' src/porkbun_api_cli/utils.py
grep -c 'def operation_allowed_by_mode(operation: str, mode: str) -> bool' src/porkbun_api_cli/utils.py
grep -c 'def load_config(config_file_path: str) -> dict\[str, Any\]' src/porkbun_api_cli/utils.py
# each: 1
```

### Criterion 3: `cli.py` 6 functions annotated

**Red-first:** `grep -c 'def _print_version(ctx: click.Context' src/porkbun_api_cli/cli.py` → 0.

```bash
grep -c 'def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None' src/porkbun_api_cli/cli.py
grep -c 'def _log_if_level(level: int, verbosity: int, message: str, file: TextIO | None = None, nl: bool = True) -> None' src/porkbun_api_cli/cli.py
grep -c 'def _collect_existing_dns_records(api: PorkbunAPI.PorkbunAPI, domain_names: list\[str\], verbose: int) -> dict\[str, list\[ExistingDnsRecord\] | None\]' src/porkbun_api_cli/cli.py
grep -c 'def _plan_operations(mode: str, verbose: int, existing_domains: dict\[str, list\[ExistingDnsRecord\] | None\], config_domains: dict\[str, list\[DnsRecord\]\]) -> dict\[str, list\[Operation\] | None\]' src/porkbun_api_cli/cli.py
grep -c 'def _execute_operations_plan(api: PorkbunAPI.PorkbunAPI, verbose: int, operations_plan: dict\[str, list\[Operation\] | None\]) -> None' src/porkbun_api_cli/cli.py
grep -c 'def main(config_file: str, mode: str, dry_run: bool, verbose: int, arguments: tuple\[str, \.\.\.\]) -> None' src/porkbun_api_cli/cli.py
# each: 1
```

### Criterion 4: TypedDicts defined with required `Operation.new`/`existing`

**Red-first:** `grep -c 'class DnsRecord(TypedDict)' src/porkbun_api_cli/utils.py` → 0.

```bash
grep -c 'class DnsRecord(TypedDict)' src/porkbun_api_cli/utils.py
grep -c 'class ExistingDnsRecord(TypedDict)' src/porkbun_api_cli/utils.py
grep -c 'class Operation(TypedDict)' src/porkbun_api_cli/utils.py
grep -c '    new: DnsRecord | None' src/porkbun_api_cli/utils.py
grep -c '    existing: ExistingDnsRecord | None' src/porkbun_api_cli/utils.py
# each: 1
grep -c 'NotRequired\[.*new.*\]\|NotRequired\[.*existing.*\]' src/porkbun_api_cli/utils.py
# expected: 0  (new/existing are required, not NotRequired)
grep -c '    ttl: NotRequired\[str\]' src/porkbun_api_cli/utils.py
grep -c '    prio: NotRequired\[str\]' src/porkbun_api_cli/utils.py
# each: 2  (once in DnsRecord, once in ExistingDnsRecord)
```

### Criterion 5: TODO comment at top of TypedDict module

**Red-first:** `grep -c 'TODO: DTOs need a refactor' src/porkbun_api_cli/utils.py` → 0.

```bash
grep -F '# TODO: DTOs need a refactor — TypedDicts are a stopgap; dataclass migration is a follow-up feature.' src/porkbun_api_cli/utils.py
# expected: match found
```

### Criterion 6: `[tool.ty.environment]` in pyproject, no `ignore_missing_imports`

**Red-first:** `grep -c 'tool.ty.environment' pyproject.toml` → 0.

```bash
grep -F '[tool.ty.environment]' pyproject.toml
grep -F 'python-version = "3.11"' pyproject.toml
# each: match found
grep -c 'ignore_missing_imports' pyproject.toml
# expected: 0
```

### Criterion 7: `[testenv:check]` `usedevelop = true`

**Red-first:** `grep -A20 '^\[testenv:check\]' tox.ini | grep -c 'skip_install = true'` → 1 (current). After: 0.

```bash
grep -A20 '^\[testenv:check\]' tox.ini | grep -F 'usedevelop = true'
grep -A20 '^\[testenv:check\]' tox.ini | grep -c 'skip_install = true'
# first: match found; second: 0
```

### Criterion 8: `check` deps include `ty` (pinned), `types-PyYAML`, `types-requests`

**Red-first:** `grep -c 'ty==' tox.ini` → 0.

```bash
grep -F 'ty==0.0.79' tox.ini
grep -F 'types-PyYAML' tox.ini
grep -F 'types-requests' tox.ini
# each: match found
```

### Criterion 9: `ty check src/porkbun_api_cli` in `check` commands after ruff

**Red-first:** `grep -F 'ty check src/porkbun_api_cli' tox.ini` → no match.

```bash
grep -F 'ty check src/porkbun_api_cli' tox.ini
# expected: match found
# ordering check: ty line must appear after ruff format line
grep -n -F 'ty check src/porkbun_api_cli' tox.ini | cut -d: -f1  # line N
grep -n -F 'ruff format --check --diff .' tox.ini | cut -d: -f1  # line M
# assert N > M
```

### Criterion 10: `tox -e check` exits 0

**Red-first:** Before annotations land, `ty check src/porkbun_api_cli` would fail (no `[tool.ty]` config + unannotated functions → no errors actually, but `usedevelop` flip + missing `types-PyYAML`/`types-requests` deps before install = env misconfigured). After all edits:

```bash
tox -e check
# expected: exit 0
```

Drives: `pyproject.toml` (`[tool.ty.environment]`), `tox.ini` (`[testenv:check]`), all 3 src modules (annotations + narrows).

### Criterion 11: `tox -e py313` exits 0

**Red-first:** Run after annotations are in but before final `ruff format` — should still pass (annotations don't change runtime; TypedDicts are structural, compatible with existing dict fixtures). If it fails, an annotation has a syntax/scope error.

```bash
tox -e py313
# expected: exit 0
```

Drives: all 3 src modules — runtime behavior unchanged. Tests: `tests/test_api.py` (20 tests), `tests/test_utils.py` (8 tests), `tests/test_cli.py` (6 tests + 6 `TestHelpers` tests), doctests in `utils.py` (4 docstrings with `:param` blocks — NOT executable doctests, `--doctest-modules` only runs `>>>` blocks, none here).

### Criterion 12: No `# type: ignore` in src

**Red-first:** `grep -c '# type: ignore' src/porkbun_api_cli/*.py` → 0 (already 0 — this is a non-regression check).

```bash
grep -rc '# type: ignore' src/porkbun_api_cli/ | grep -v ':0$' || echo "clean"
# expected: clean
```

### Criterion 13: No `typing.cast` in src

**Red-first:** `grep -c 'typing.cast\|from typing import.*cast\|cast(' src/porkbun_api_cli/*.py` → 0.

```bash
grep -rc 'typing\.cast\|from typing import.*cast\|cast(' src/porkbun_api_cli/ | grep -v ':0$' || echo "clean"
# expected: clean
```

### Criterion 14: `# ty: narrow` asserts present (3 in `_execute_operations_plan`)

**Red-first:** `grep -c '# ty: narrow' src/porkbun_api_cli/cli.py` → 0.

```bash
grep -c '# ty: narrow' src/porkbun_api_cli/cli.py
# expected: 3
grep -F '# ty: narrow — new is non-None on create/update branch' src/porkbun_api_cli/cli.py
grep -F '# ty: narrow — existing is non-None on delete branch' src/porkbun_api_cli/cli.py
grep -F '# ty: narrow — existing is non-None on update branch (update requires a matched record)' src/porkbun_api_cli/cli.py
# each: match found
```

### Criterion 15: `assert record is not None` narrowing (3 instances)

**Red-first:** `grep -c 'assert record is not None\|assert existing is not None' src/porkbun_api_cli/cli.py` → 0.

```bash
grep -c 'assert record is not None' src/porkbun_api_cli/cli.py
# expected: 2
grep -c 'assert existing is not None' src/porkbun_api_cli/cli.py
# expected: 1
```

### Criterion 16: `if operations is None: continue` guard

**Red-first:** `grep -c 'if operations is None: continue' src/porkbun_api_cli/cli.py` → 0.

```bash
grep -F 'if operations is None: continue' src/porkbun_api_cli/cli.py
# expected: match found
# placement: immediately after `for domain_name, operations in operations_plan.items():`
grep -n -A1 'for domain_name, operations in operations_plan.items():' src/porkbun_api_cli/cli.py | grep 'if operations is None: continue'
# expected: match found
```

### Criterion 17, 18, 19, 20, 21, 22, 23, 24, 25 → covered by criterion 10 (`tox -e check`) + criterion 11 (`tox -e py313`) + criteria 12–16 (greps)

- Criterion 17 (`tox -e check` exits 0) → test 10.
- Criterion 18 (`tox -e py313` exits 0) → test 11.
- Criterion 19 (no `# type: ignore`) → test 12.
- Criterion 20 (no `typing.cast`) → test 13.
- Criterion 21 (assert + `# ty: narrow`) → test 14.
- Criterion 22 (`_query_api` return `tuple[Any, bool]`) → test 1 (`-> tuple\[Any, bool\]` grep).
- Criterion 23 (`if operations is None: continue`) → test 16.
- Criterion 24 (`assert record is not None` after `operation["new"]`/`["existing"]`) → test 15.
- Criterion 25 (TODO comment) → test 5.

## Implementation order

1. **`src/porkbun_api_cli/utils.py`**: Add `from __future__ import annotations`, imports (`Any`, `NotRequired`, `TypedDict`), TODO header, 3 TypedDicts (`DnsRecord`, `ExistingDnsRecord`, `Operation`), 4 function annotations. Run `tox -e py311` → tests green (TypedDicts structural, no runtime change). Run `uvx --from ty ty check src/porkbun_api_cli/utils.py --python /usr/bin/python3.13` → should pass (no callers yet, just definitions).

2. **`src/porkbun_api_cli/api.py`**: Add `from __future__ import annotations`, imports (`Mapping` from `collections.abc`, `Any` from `typing`, `DnsRecord`/`ExistingDnsRecord` from `.utils`), 6 function annotations. Run `uvx --from ty ty check src/porkbun_api_cli/api.py --python /usr/bin/python3.13` → should pass (`tuple[Any, bool]` + `Mapping` shapes verified). Run `tox -e py311` → tests green.

3. **`src/porkbun_api_cli/cli.py`**: Add `from __future__ import annotations`, imports (`TextIO` from `typing`, `DnsRecord`/`ExistingDnsRecord`/`Operation` from `.utils`), 6 function annotations, `if operations is None: continue` guard in `_execute_operations_plan`, 3 `# ty: narrow` + `assert` placements. Run `uvx --from ty ty check src/porkbun_api_cli/cli.py --python /usr/bin/python3.13` → should pass (verified: all 3 narrows land, `operation["existing"]["id"]` narrowed via intermediate `existing` var). Run `tox -e py311` → tests green (asserts are no-ops when invariants hold; TypedDicts structural).

4. **`pyproject.toml`**: Add `[tool.ty.environment]` + `python-version = "3.11"` at end of file.

5. **`tox.ini`**: Rewrite `[testenv:check]` — flip `skip_install = true` → `usedevelop = true`, add `ty==0.0.79` + `types-PyYAML` + `types-requests` to `deps`, add `ty check src/porkbun_api_cli` to `commands` after `ruff format --check --diff .`.

6. **Run `tox -e check`** → exit 0 (ruff + ty + setup + manifest). If ty fails: re-run `uvx --from ty ty check src/porkbun_api_cli --python /usr/bin/python3.13` for the specific error, fix annotations (NOT by adding `# type: ignore`/`cast` — by fixing the type or adding a `# ty: narrow` assert).

7. **Run `tox -e py313`** → exit 0 (final runtime confirmation). Gate command per `.ristretto.json`: `test = "tox -e py311"`, but contract criterion 18 binds `py313` — run both.

### AGENTS.md consultation points

- AGENTS.md L12: "Lint only: `tox -e check` (flake8 + black --check + isort --check-only + manifest + rst check)" — **stale** (ruff-migration already replaced this; this feature adds ty). Implementer does NOT update AGENTS.md (not bound by contract); follow-up feature or the closer may note it.
- AGENTS.md L23: "`pytest.ini` sets `filterwarnings = error`" — **stale** (moved to `pyproject.toml`). Not bound by this contract.
- AGENTS.md L28: "Pinned linters. `check` env pins exact versions: `flake8==7.0.0`, `black==24.3.0`, `isort==5.13.2`" — **stale** since ruff-migration; further stale after this feature adds `ty==0.0.79`. Not bound.
- AGENTS.md L44: "Tests use unittest-style asserts (see flake8 PT009 ignores)" — **stale** (PT ignores removed in ruff-migration). Not bound.
- The contract does not bind an AGENTS.md update for this feature. The implementer should NOT touch AGENTS.md.

### Local verification loop

Run after each annotation unit (steps 1–3):

```bash
uvx --from ty ty check src/porkbun_api_cli --python /usr/bin/python3.13
```

Should converge to `All checks passed!` as units land. Final gate: `tox -e check` (which runs `ty check src/porkbun_api_cli` with the same interpreter via the `check` env's py3.13 basepython).

## Manual checks

None. Contract `Manual-Checks: —`.

## Evidence

tier: normal

### Gate: lint
- Command: `tox -e check`
- Exit code: 0
- Output:
  ```
  check: commands[4]> check-manifest .
  lists of files in version control and sdist match
    check: OK (6.84=setup[1.70]+cmd[0.01,0.01,0.08,0.36,4.68] seconds)
    congratulations :) (7.03 seconds)
  ```

### Gate: test
- Command: `tox -e py311`
- Exit code: 0
- Output:
  ```
  Required test coverage of 95.0% reached. Total coverage: 95.86%
  ==================== 76 passed, 7 subtests passed in 0.74s ====================
    py311: OK (4.16=setup[3.09]+cmd[1.08] seconds)
    congratulations :) (4.32 seconds)
  ```
- Command: `tox -e py313`
- Exit code: 0
- Output:
  ```
  Required test coverage of 95.0% reached. Total coverage: 95.86%
  ==================== 76 passed, 7 subtests passed in 0.84s ====================
    py313: OK (5.11=setup[3.86]+cmd[1.26] seconds)
    congratulations :) (6.42 seconds)
  ```

### Acceptance criteria
- [x] [1] api.py 6 annotated — `grep -n 'def __init__(self, apikey: str, secretapikey: str, endpoint: str) -> None'` → line 14; `def _query_api(` → line 17, `-> tuple[Any, bool]` → line 19; `def list_dns_records(self, domain: str) -> list[ExistingDnsRecord]` → line 59; `def create_record(self, domain: str, record: DnsRecord) -> str` → line 70; `def update_record(self, domain: str, record_id: str, new_record: DnsRecord) -> None` → line 87; `def get_my_ip(self) -> str` → line 105. All 6 match.
- [x] [2] utils.py 4 annotated — `grep -n` each: `def compare_record_by_content_ttl_prio(target: DnsRecord, other: ExistingDnsRecord) -> bool` → line 35; `def compare_record_by_name_type(domain_name: str, target: DnsRecord, other: ExistingDnsRecord) -> bool` → line 54; `def operation_allowed_by_mode(operation: str, mode: str) -> bool` → line 70; `def load_config(config_file_path: str) -> dict[str, Any]` → line 95. All 4 match.
- [x] [3] cli.py 6 annotated — `def _print_version(ctx: click.Context, param: click.Parameter, value: bool) -> None` → line 17; `def _log_if_level(level: int, verbosity: int, message: str, file: TextIO | None = None, nl: bool = True) -> None` → line 24; `def _collect_existing_dns_records(...) -> dict[str, list[ExistingDnsRecord] | None]` → line 29; `def _plan_operations(...) -> dict[str, list[Operation] | None]` → line 50; `def _execute_operations_plan(...) -> None` → line 110; `def main(config_file: str, mode: str, dry_run: bool, verbose: int, arguments: tuple[str, ...]) -> None` → line 181. All 6 match.
- [x] [4] TypedDicts defined, Operation.new/existing required — `class DnsRecord(TypedDict)` → utils.py:12; `class ExistingDnsRecord(TypedDict)` → utils.py:20; `class Operation(TypedDict)` → utils.py:29. `new: DnsRecord | None` → line 31; `existing: ExistingDnsRecord | None` → line 32. `grep -c 'NotRequired[.*new.*]\|NotRequired[.*existing.*]'` = 0 (required, not NotRequired). `ttl: NotRequired[str]` count = 2 (DnsRecord + ExistingDnsRecord); `prio: NotRequired[str]` count = 2.
- [x] [5] TODO comment present — `grep -F '# TODO: DTOs need a refactor — TypedDicts are a stopgap; dataclass migration is a follow-up feature.' src/porkbun_api_cli/utils.py` → match at line 9.
- [x] [6] `[tool.ty.environment]` python-version="3.11", no ignore_missing_imports — `grep -F '[tool.ty.environment]' pyproject.toml` → match; `grep -F 'python-version = "3.11"' pyproject.toml` → match; `grep -c 'ignore_missing_imports' pyproject.toml` = 0.
- [x] [7] usedevelop = true, skip_install absent — `grep -A25 '^\[testenv:check\]' tox.ini | grep -F 'usedevelop = true'` → match; `grep -A25 '^\[testenv:check\]' tox.ini | grep -c 'skip_install = true'` = 0.
- [x] [8] ty==0.0.79 + types-PyYAML + types-requests in deps — `grep -F 'ty==0.0.79' tox.ini` → line 43; `grep -F 'types-PyYAML' tox.ini` → line 44; `grep -F 'types-requests' tox.ini` → line 45. All match.
- [x] [9] ty check src/porkbun_api_cli in commands after ruff — `grep -F 'ty check src/porkbun_api_cli' tox.ini` → line 54. Ordering: `ruff format --check --diff .` → line 53; `ty check src/porkbun_api_cli` → line 54. 54 > 53 ✓.
- [x] [10] tox -e check exits 0 — gate confirmed above (ruff + ty + setup check + check-manifest, 7.03 seconds).
- [x] [11] tox -e py313 exits 0 — gate confirmed above (76 passed, 7 subtests passed, 95.86% coverage, 6.42 seconds).
- [x] [12] no # type: ignore in src — `grep -rc '# type: ignore' src/porkbun_api_cli/ | grep -v ':0$'` → "clean" (no matches).
- [x] [13] no typing.cast in src — `grep -rc 'typing\.cast\|from typing import.*cast\|cast(' src/porkbun_api_cli/ | grep -v ':0$'` → "clean" (no matches).
- [x] [14] 3 # ty: narrow comments — `grep -c '# ty: narrow' src/porkbun_api_cli/cli.py` = 3. Placements: line 126 (`# ty: narrow — new is non-None on create/update branch`), line 134 (`# ty: narrow — existing is non-None on delete branch`), line 144 (`# ty: narrow — existing is non-None on update branch (update requires a matched record)`).
- [x] [15] 2 assert record + 1 assert existing — `grep -c 'assert record is not None' src/porkbun_api_cli/cli.py` = 2 (lines 127, 135); `grep -c 'assert existing is not None' src/porkbun_api_cli/cli.py` = 1 (line 145).
- [x] [16] if operations is None: continue guard — `grep -n 'if operations is None' src/porkbun_api_cli/cli.py` → line 115; `grep -n -A1 'for domain_name, operations in operations_plan.items():' src/porkbun_api_cli/cli.py` shows the guard on the immediately following line (116: `continue`). Placement confirmed: first statement inside the for-loop body, before `_log_if_level`.

### Plan correction: cli.py:73 local annotation

The implementer added a local annotation `operations: list[Operation] = []` at cli.py:73 (inside `_plan_operations`), not specified in the contract Units. This was required for ty to pass: without it, ty infers the empty-dict literal `{}` as `dict[str, list[Operation] | None]` from the return type, but the `operations` list built up via `.append()` loses the `list[Operation]` element type — ty cannot infer the TypedDict element from append calls alone. The explicit local annotation closes the literal-dict→TypedDict inference gap. Not scope creep; a ty-passing requirement discovered during implementation.

### Review verdict

review: notes-only (2 note, 0 lean) (1 round)

## Open findings

Copied verbatim from the reviewer verdict:

- note · src/porkbun_api_cli/utils.py:49-50 · pyright flags NotRequired `ttl`/`prio` access in compare_record_by_content_ttl_prio (guarded by `"ttl" not in target` but pyright doesn't narrow on it); ty 0.0.79 passes, and ty is the binding gate — user cannot be harmed because the enforced gate passes and the guarded access is correct.
- note · src/porkbun_api_cli/cli.py:115 · `if operations is None: continue` guard is a behavior change on a changed path with no direct test coverage (test_execute_operations_plan passes only list values, never None) — user cannot be harmed because the guard only skips domains whose query failed, where the pre-change code crashed with TypeError.