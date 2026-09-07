# PR 08 — T9 Semantic Retrieval with PostgreSQL + pgvector

```text
You are working on PR 08 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/08-pgvector-semantic-retrieval

GOAL
Add semantic external memory using pgvector in the same PostgreSQL database.

Lesson: **stored knowledge becomes useful memory only when retrieval selects the right evidence**.

BOUNDARY
RAG is for:
- validated forecast/outcome episodes;
- synthetic operating guidance;
- public references.

RAG is not authoritative for:
- current MCP telemetry/weather;
- arithmetic;
- equipment limits;
- reserve enforcement.

EMBEDDING PROVIDER
- embed_documents;
- embed_query;
- deterministic test provider;
- configurable real development provider;
- automated tests never require network/model download;
- record model/version/dimension when real provider used.

PGVECTOR SCHEMA
Create semantic_memory_records with:
- record id/type;
- content;
- embedding vector;
- source/source id;
- date/validity;
- configuration class;
- event type;
- validation status;
- version;
- provenance;
- embedding model/version;
- timestamps.

For MVP scale, exact search is acceptable.
Only add HNSW/IVFFlat if model dimension is pinned and a benchmark justifies it.
Document similarity metric.

CORPUS
- structured forecast/outcome episode: one event per semantic record;
- narrative guidance/reference: semantic sections ~350–500 tokens with small overlap.

Only approved public/synthetic/anonymized validated records are embedded.

T9
Input natural-language retrieval need + metadata constraints.
Return first-stage FIVE candidates with score and provenance.

INGESTION
Idempotent CLI/job to select eligible records, chunk if needed, embed, version, and upsert.

Do not create Chroma/Pinecone/FAISS persistence.

TEST
migration, vector round trip, semantic retrieval with wording variation, metadata filters, validated-only indexing, idempotent reindex.

PLAYWRIGHT
Debug retrieval endpoint returns ranked IDs/scores/provenance.

DOCUMENT
docs/lessons/08-postgres-pgvector-memory.md.

SPECIAL
Use `db-migration-safety`.

QUALITY HANDOFF — REQUIRED BEFORE STOP

- Run `make verify`.
- Update the current reusable lesson with `lesson-capture`.
- Run `pr-readiness`; resolve all BLOCKER/MAJOR findings.
- Run every specialized skill applicable to this PR:
  - `db-migration-safety`
  - `mcp-contract-safety`
  - `langgraph-workflow-safety`
  - `langchain-agent-boundary`
  - `observability-trace-safety`
- Run `hil-local-verification`; include exact copy/paste human test commands and expected results.
- Run `pr-description`; use the repository PR template.
- Leave all HUMAN-ONLY boxes unchecked.
- Never push, open, approve, merge, or tag remotely.

STOP
Return the local handoff report and stop before remote actions.
```
