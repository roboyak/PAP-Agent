---
name: mcp-contract-safety
description: Review Telemetry or Weather/Solar MCP server/client changes for read-only behavior, versioning, provenance, failure semantics, and T3 validation.
---

# MCP Contract Safety

Verify:
1. tool/resource surface remains read-only;
2. no write/control action;
3. schema includes source identity, source timestamp, version, provenance, and missing/error status;
4. transport/provider details do not leak into PAP domain or LangGraph control flow;
5. T3 still validates after acquisition;
6. unavailable != zero;
7. no invented missing values;
8. tests cover normal, stale, malformed, timeout, schema mismatch;
9. HIL shows how to inspect the tool surface and confirm no control tool exists.

Any write-capable Telemetry/Weather MCP surface is a BLOCKER.
