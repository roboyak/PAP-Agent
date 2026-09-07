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
8. Push, open, and merge the verified PR under the user's explicit authorization.
9. Keep local human review commands available; do not claim human testing occurred.
10. Proceed to the next PR. The user watches PR01/02, then work continues autonomously.

Keep each increment minimal, with one terse lesson in the PR body and commit message.
