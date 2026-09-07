---
name: db-migration-safety
description: Review PostgreSQL, Alembic, pgvector, embedding-dimension/index, LangGraph checkpointer setup, or data migrations before handoff.
---

# Database Migration Safety

Use whenever schema/persistence changes.

Check:
- fresh DB -> head;
- previous revision -> head;
- null/default behavior;
- constraints/foreign keys;
- destructive changes;
- backfill order;
- locks/table rewrites;
- pgvector dimensions and distance/index compatibility;
- embedding model/version lineage;
- LangGraph checkpointer initialization/setup path;
- separation of checkpoint data and canonical domain data.

Never silently drop operational history/provenance.

Rate migration risk LOW / MEDIUM / HIGH.

Destructive or difficult-to-recover changes are HUMAN REVIEW BLOCKERS.
