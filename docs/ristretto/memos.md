# Memos

Cross-cutting TODOs and deferred decisions surfaced during prep. Not roadmap features yet — pull these into a prep when ready to plan.

## DTO refactor — migrate TypedDicts to dataclasses

- **Origin:** ty-typecheck plan (`docs/ristretto/plans/ty-typecheck.md`), Decisions + inline `# TODO` comment.
- **Resolved by:** `dto-migration` (`docs/ristretto/plans/dto-migration.md`).
- **Decision (2026-09-14):** Replace the three TypedDict stopgaps with `@dataclass(frozen=True)` (`DnsRecord`, `ExistingDnsRecord`, `Operation`) plus three config dataclasses (`Config`, `ApiConfig`, `DomainConfig`). `ttl` and `prio` re-typed from `str` to `int | None` with `int()` coercion in the new `from_api` classmethods. `ExistingDnsRecord` gains `notes: str | None`. `Operation` ships `operation: str`; the `Literal` discriminator extension is scoped to `plan-entry-redesign`.

## Assert-based type narrowing — replace with per-op TypedDicts + Literal discriminators

- **Origin:** ty-typecheck plan (`docs/ristretto/plans/ty-typecheck.md`), Decisions (assert policy) + contract (assert criteria).
- **Partly resolved by:** `dto-migration` — the asserts (`# ty: narrow` + `assert ... is not None`) still narrow dataclass fields cleanly with `ty==0.0.79`, no further changes needed for runtime correctness.
- **Carry-forward (scope: `plan-entry-redesign`):** the structural `Operation` → `CreateOp` / `UpdateOp` / `DeleteOp` split with `Literal` discriminators is no longer *needed* for ty to narrow on dataclass attribute access — the `assert` pattern still works — so the discriminator refactor is now a `plan-entry-redesign` nicety rather than a correctness fix.
