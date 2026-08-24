# 0001 — str, Enum over StrEnum

**Date:** 2026-08-24
**Status:** accepted

## Context
Ruff's UP042 flags `class X(str, Enum)` and recommends `enum.StrEnum`,
available since Python 3.11.

## Decision
Keep `str, Enum`. Silence UP042 in `pyproject.toml`.

## Consequences
`f"{Country.RS}"` renders `"Country.RS"` on 3.11+, while concatenation
renders `"RS"`. Any enum value leaving the process — prompts, logs, URLs —
must use `.value` explicitly. Revisit if this causes a real bug.