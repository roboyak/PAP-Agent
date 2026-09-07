# Bootstrap and Start Codex

```bash
mkdir -p ~/code/dragonwings-pap-agent
cd ~/code/dragonwings-pap-agent

git init
git branch -M main
```

Copy:
- quality-pack contents -> repository root
- pr-prompts contents -> `docs/build-prompts/`

Commit the governance baseline yourself:

```bash
git add .
git status
git commit -m "chore: bootstrap agentic engineering workflow v4"
```

Start Codex:

```bash
codex
```

First prompt:

```text
Do not modify files.

Read AGENTS.md, docs/engineering/, .agents/skills/, .codex/agents/,
.github/PULL_REQUEST_TEMPLATE.md, and docs/build-prompts/.

Summarize the runtime architecture, LangGraph vs LangChain responsibilities,
PostgreSQL/pgvector, MCP boundaries, deterministic authority, optional
LangSmith behavior, HIL requirements, prohibited remote actions, and the
12-PR sequence.

Confirm Deep Agents is not part of the PAP MVP.
```

Then start a fresh session and run PR 01.
