# Memos

Cross-cutting TODOs and deferred decisions surfaced during prep. Not roadmap features yet — pull these into a prep when ready to plan.

## DTO refactor — migrate TypedDicts to dataclasses

- **Origin:** ty-typecheck plan (`docs/ristretto/plans/ty-typecheck.md`), Decisions + inline `# TODO` comment.
- **State:** `ty-typecheck` introduces `DnsRecord`, `ExistingDnsRecord`, `Operation` as `TypedDict`s — a stopgap to get ty passing without rewriting call sites or test fixtures.
- **Why defer:** dataclass migration is a real refactor — changes API input shapes, ~10 dict constructions in `cli.py`, test fixtures (20+ dict literals), and forces decisions on `frozen=`, `slots=`, `kw_only=`, conversion at the `requests.post` boundary. Wrong to bundle with "add annotations."
- **Seam:** the `DnsRecord.name` (subdomain) vs `ExistingDnsRecord.name` (FQDN) semantic split — TypedDict can't enforce it at construction, only field presence. dataclass variants (`ExistingDnsRecord(DnsRecord)` adding `id`, FQDN-validated `name`) express it cleanly.
- **When to pull:** after `ty-typecheck` lands and the typed surface is stable. Likely touches `api.py`, `cli.py`, `utils.py`, and all `tests/test_*.py` fixtures in one feature.

## Assert-based type narrowing — replace with per-op TypedDicts + Literal discriminators

- **Origin:** ty-typecheck plan (`docs/ristretto/plans/ty-typecheck.md`), Decisions (assert policy) + contract (assert criteria).
- **State:** `ty-typecheck` adds `# ty: narrow` + `assert record is not None` in `_execute_operations_plan` to narrow `Operation.new`/`Operation.existing` fields after branch dispatch (`if op == "create": ...`). ty can't narrow a TypedDict field based on a *different* field's value (`operation["operation"]`), so the assert is a runtime guard.
- **Why defer:** the proper fix is splitting `Operation` into `CreateOp` / `UpdateOp` / `DeleteOp` with `operation: Literal["create"]` / `Literal["update"]` / `Literal["delete"]` as a discriminator, enabling ty to narrow the whole TypedDict on the discriminator. That's a structural refactor of the `Operation` type + all its construction sites in `_plan_operations`, bundled with the DTO refactor above.
- **Count:** 3 asserts in `_execute_operations_plan` (~3 lines + comments).
- **When to pull:** same as DTO refactor — the assert narrowing and the TypedDict→dataclass migration are the same seam. Pulling one without the other leaves a hybrid.