---
name: langgraph-workflow-safety
description: Review LangGraph state, nodes, edges, subgraphs, checkpointing, retries, interrupts, termination, or Tree-of-Thought workflow changes.
---

# LangGraph Workflow Safety

Review:

## State ownership
- typed, serializable state;
- durable domain facts referenced by IDs;
- no accidental second system of record.

## Topology
- START/END paths;
- conditional edges use explicit typed status;
- bounded retries;
- no unreachable or infinite path;
- fail closed.

## Checkpoint/resume
- stable thread/run IDs;
- replay/resume does not duplicate unsafe side effects;
- side-effecting nodes are idempotent/deduplicated.

## Interrupts
- pre-interrupt side effects safe/idempotent;
- resume data validated;
- interrupt not a substitute for deterministic checks.

## Selective ToT
- explicit entry condition;
- branch factor 3;
- beam width 2;
- max depth 3;
- max model/reasoning calls 8;
- deterministic hard prune before qualitative score;
- no acceptable branch -> lower confidence/abstain.

## Trace
Persist observable decisions, evidence IDs, scores, prune reasons, node names, stop reasons — not private chain-of-thought.

Unsafe replay, unbounded loop, or deterministic-authority bypass is a BLOCKER.
