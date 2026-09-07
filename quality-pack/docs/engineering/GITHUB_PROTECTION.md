# GitHub Protection Requirements

Repository policy must be reinforced in GitHub rulesets.

Recommended:
- require PR before merge;
- require at least one human approval;
- require automated status checks;
- resolve conversations;
- block force pushes;
- restrict bypass;
- only merge after HUMAN-ONLY local test signoff.

Protect/high-review:
- `.github/`
- `.codex/`
- `.agents/`
- migrations/Alembic
- MCP servers
- deterministic calculation/constraint code
- LangGraph workflow code
- runtime/deployment scripts
