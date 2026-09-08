# Ristretto Manual Checks

<!-- ristretto-format: 0.16 -->

Human-only checks surfaced during ristretto runs. House rules block
ristretto from making these edits itself; the human applies the change
and ticks the box.

- [x] **py-version-floor** — AGENTS.md L27 stale wording ("Python version mismatch" bullet); replace with: `- **Python version range.** Supported: py3.11–py3.14. \`pyproject.toml\` \`requires-python = ">=3.11"\`, tox envs \`{py311,py312,py313,py314}\` + \`clean/check/docs/report\`, \`clean/check/docs/report\` basepython is py3.13. CI matrix matches. py3.12 not on this machine (\`/usr/bin/python3.12\` absent) — \`skip_missing_interpreters = true\` makes tox skip it locally; CI is the matrix source of truth for 3.12.`; proves: criterion 10 (AGENTS.md wording reflects 3.11–3.14, no stale py3.8/3.13-vs-CI-mismatch wording)