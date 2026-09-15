# Ristretto Manual Checks

<!-- ristretto-format: 0.16 -->

Human-only checks surfaced during ristretto runs. House rules block
ristretto from making these edits itself; the human applies the change
and ticks the box.

- [x] **py-version-floor** — AGENTS.md L27 stale wording ("Python version mismatch" bullet); replace with: `- **Python version range.** Supported: py3.11–py3.14. \`pyproject.toml\` \`requires-python = ">=3.11"\`, tox envs \`{py311,py312,py313,py314}\` + \`clean/check/docs/report\`, \`clean/check/docs/report\` basepython is py3.13. CI matrix matches. py3.12 not on this machine (\`/usr/bin/python3.12\` absent) — \`skip_missing_interpreters = true\` makes tox skip it locally; CI is the matrix source of truth for 3.12.`; proves: criterion 10 (AGENTS.md wording reflects 3.11–py3.14, no stale py3.8/3.13-vs-CI-mismatch wording)

- [x] **dto-migration** — `tests/test_utils.py` `test_from_api_matches_real_porkbun_response_shape` (skipped); proves: criterion `from_api` coercion correctness against a real Porkbun API response shape (string vs int for `ttl`/`prio`, presence of `notes` key in `dns/retrieve/{domain}` `records[]`); what was out of reach: a live Porkbun account and stored API credentials are not available in this environment, so the test is left skipped with the check enumerated here; what to do: issue one `POST /api/json/v3/dns/retrieve/{domain}` call against a real Porkbun account using stored API credentials, capture the raw JSON record for an A record and an MX record from the `records[]` array, confirm (a) `ttl`/`prio` are strings or ints, (b) `notes` key is present; if types are strings the `int()` coercion in `from_api` is mandatory (not just a safety net); if ints the coercion is a verified no-op; if `notes` is absent, downgrade the `notes` field decision to "warn-only" and re-plan. **Checked 2026-09-15: live `dns/retrieve/{domain}` against real Porkbun account; CLI dry-run reported current config end-to-end (no `TypeError` from unknown fields, no coercion failure on `ttl`/`prio`); `int()` coercion is a verified no-op for the records observed.**
