# Documentation Policy

Behavior changes require documentation changes.

Use:
- README for durable setup/run;
- docs/architecture or engineering runtime docs for current design;
- one terse reusable lesson in the PR body and commit message;
- MVP_RUNBOOK for operations;
- PR body for change-specific evidence/HIL/rollback.

Prefer exact commands, explicit assumptions, diagrams, failure behavior, and rationale.

Do not:
- claim absent features;
- hide synthetic/non-production assumptions;
- use docs to excuse failing tests;
- persist CrewAI-era terminology in v4 architecture.
