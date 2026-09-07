# Pull Request Workflow

1. One architectural lesson per PR.
2. Implement narrowly.
3. Run `make verify`.
4. Run `pr-readiness`.
5. Run specialized skills when applicable:
   - db-migration-safety
   - mcp-contract-safety
   - langgraph-workflow-safety
   - langchain-agent-boundary
   - observability-trace-safety
6. Generate HIL with `hil-local-verification`.
7. Draft PR body with `pr-description`.
8. Agent stops.
9. Human reviews diff and runs HIL.
10. Human opens/reviews/merges PR.

Only a human merges.
