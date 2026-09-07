# Agent Use Policy

Agents may inspect, edit within scope, run local tests/services, use read-only review subagents, draft HIL/PR docs, and recommend release notes.

Agents may not:
- push;
- open/submit remote PR;
- approve;
- merge;
- check HUMAN-ONLY signoff;
- claim human testing;
- tag releases remotely;
- bypass quality gates;
- weaken deterministic authority;
- introduce hardware control in MVP.

Prefer subagents for read-heavy independent review, not conflicting parallel edits.
