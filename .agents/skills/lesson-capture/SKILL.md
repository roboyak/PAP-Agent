---
name: lesson-capture
description: Update the reusable docs/lessons entry for the current incremental PAP PR so future agentic automation projects can reuse the pattern.
---

# Lesson Capture

Create/update `docs/lessons/<NN>-<slug>.md`.

Structure:

1. Lesson — one-sentence principle.
2. Problem — reliability/architecture issue.
3. Decision — chosen approach and why.
4. Architecture — interfaces/data flow; Mermaid when useful.
5. Implementation — high-level key files/contracts.
6. Verification — automated + HIL + failure path.
7. Failure Modes — remaining risks and containment.
8. Reusable Pattern — how another project can reuse it.
9. Next Increment — intentionally deferred work.

Do not claim behavior not implemented.
