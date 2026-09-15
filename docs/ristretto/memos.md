# Memos

Cross-cutting TODOs and deferred decisions surfaced during prep. Not roadmap features yet — pull these into a prep when ready to plan.

## DTO refactor — migrate TypedDicts to dataclasses

- **Origin:** ty-typecheck plan (`docs/ristretto/plans/ty-typecheck.md`), Decisions + inline `# TODO` comment.
- **Resolved by:** `dto-migration` (`docs/ristretto/plans/dto-migration.md`).
- **Decision (2026-09-14):** Replace the three TypedDict stopgaps with `@dataclass(frozen=True)` (`DnsRecord`, `ExistingDnsRecord`, `Operation`) plus three config dataclasses (`Config`, `ApiConfig`, `DomainConfig`). `ttl` and `prio` re-typed from `str` to `int | None` with `int()` coercion in the new `from_api` classmethods. `ExistingDnsRecord` gains `notes: str | None`. `Operation` ships `operation: str`; the `Literal` discriminator extension is scoped to `plan-entry-redesign`.

## Assert-based type narrowing — replace with per-op TypedDicts + Literal discriminators

- **Origin:** ty-typecheck plan (`docs/ristretto/plans/ty-typecheck.md`), Decisions (assert policy) + contract (assert criteria).
- **Resolved by:** `plan-entry-redesign` — `Operation.operation` widened to `Literal["create", "update", "delete", "match"]`; the typed-discriminator split into `CreateOp` / `UpdateOp` / `DeleteOp` was dropped in favor of a single `PlanEntry = Operation` class with `Literal[...]`. Assert narrowing (`# ty: narrow` + `assert ... is not None`) keeps covering the create/update/delete branches since match entries never execute.
