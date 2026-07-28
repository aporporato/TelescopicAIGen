# Master AGENTS.md - Repository Governance

## Project Overview & Core Functionality
AI Telescopic Text is an interactive, state-driven recursive writing workspace inspired by telescopictext.org.
- **Contextual Blank Expansion**: Clicking a word trigger sends the full sentence context to the LLM with a blank (`_`) placeholder at the target word location.
- **Recursive Trigger Generation**: The LLM returns a strict JSON payload `{"replacement": "phrase with 1-2 [[triggers]]"}`. The frontend tokenizes `[[triggers]]` into interactive DOM nodes while keeping unbracketed words static, enabling infinite nested storytelling branches.
- **Strict In-Memory BYOK**: All API keys (OpenAI, Gemini, Anthropic) are held purely in frontend JS memory during the session and passed per-request; the backend never stores, logs, or caches keys.

## Operational Commands
- **Backend Dev Server**: `uv run python app.py`
- **Backend Unit Tests**: `uv run pytest`
- **Frontend Unit Tests**: `npm test`
- **E2E Evaluation Skill**: `uv run python skills/e2e-evaluator/run_e2e.py`
- **Package Sync**: `uv sync`

## Agentic Quality Directives
- **Skill Usage**: Before performing `git commit` or `git push`, the agent MUST explicitly execute the E2E evaluation skill: `uv run python skills/e2e-evaluator/run_e2e.py`.
- **Agentic Hooks Governance**: For ecosystems supporting pre-command hooks (Cursor, Codex, Mistral Vibe), hooks intercept the `"git add"` command prefix to run linters before commits. For other platforms (Google Antigravity 2.0, Claude Code), linters are executed at the end of the session (`onAgentComplete` / `Postrun` hooks).