# AI Telescopic Text (`TelescopicAIGen`)

AI Telescopic Text is an interactive, state-driven recursive writing workspace inspired by the classic [Telescopic Text](https://www.telescopictext.org/) format. Instead of using a predefined, static hierarchy of substitutions, this application dynamically generates contextual expansions using Large Language Models (LLMs) in real-time.

---

## Core Concept & Technical Mechanics

1. **Contextual Blank Expansion**: Clicking any word trigger in a sentence extracts the full sentence context, replaces the clicked word with a blank placeholder (`_`), and sends it to the backend endpoint `/api/expand`.
2. **Recursive Trigger Generation**: The backend prompts the selected LLM to return a strict JSON payload containing a single key:
   ```json
   {
     "replacement": "hot water for my [[favorite oolong tea]]"
   }
   ```
   The frontend tokenizes bracketed words (`[[triggers]]`) into new interactive clickable nodes while leaving unbracketed text static, allowing infinite nested story branches.
3. **Interactive Collapsing**: Double-clicking any expanded section instantly collapses it back to its original single word.
4. **Strict In-Memory BYOK (Bring Your Own Key)**: All API keys (OpenAI, Gemini, Anthropic) are held strictly in frontend JavaScript memory per session. They are passed directly in request payloads to `/api/expand`, never logged or saved on the backend server, and never written to `localStorage` or `sessionStorage`.

---

## Supported LLM Providers & Models

- **OpenAI**: `gpt-5.4-nano`
- **Google Gemini**: `gemini-3.5-flash`
- **Anthropic**: `claude-haiku-4-5` (`claude-haiku-4-5-20251001`)

Model configurations are loaded dynamically on page load from the backend `/api/config` endpoint, controlled via the `AVAILABLE_MODELS` environment variable in `.env`.

---

## API Reference

### `GET /api/config`
Returns the list of available AI models and their providers configured in `.env`.
- **Response**: `{"models": [{"provider": "openai", "name": "GPT-5.4 Nano", "id": "gpt-5.4-nano"}, ...]}`

### `POST /api/expand`
Executes a dynamic expansion request against the chosen LLM provider.
- **Request Payload**:
  ```json
  {
    "sentence_with_blank": "I steeped the leaves in _.",
    "provider": "anthropic",
    "model": "claude-haiku-4-5-20251001",
    "api_key": "your-api-key-here"
  }
  ```
- **Response**: `{"replacement": "[[hot water]] to release delicate flavors"}`

---

## Repository & Governance Structure (Multi-Vendor Agentic Framework)

The project adheres to the open-source **Single Source of Truth (SSOT)** agentic specification (`AGENTS.md`), providing cross-platform vendor support without duplicate instruction files.

```text
E:\TelescopicAIGen\
├── AGENTS.md                   # [SSOT] Master repository governance file
├── CLAUDE.md                   # @AGENTS.md import directive for Claude Code
├── .cursorrules                # Cursor instructions (SSOT link -> AGENTS.md)
├── .agents/                    # Antigravity 2.0 & Standard Agentic AI
│   ├── mcp.json                # MCP server configuration
│   ├── hooks/
│   │   └── preCommit.json      # Pre-commit linter hook configuration
│   └── skills/                 # Agent Skills link -> ../skills
├── .gemini/                    # Google Antigravity Configuration
│   ├── settings.json           # Antigravity settings (contextFileName: AGENTS.md)
│   └── hooks/
│       └── preCommit.json      # Primary SSOT pre-commit linter hook
├── .github/
│   ├── copilot-instructions.md # GitHub Copilot instructions (SSOT link -> AGENTS.md)
│   ├── hooks/
│   │   └── preCommit.json      # Copilot pre-commit linter hook
│   └── skills/                 # Skills link -> ../skills
├── .codex/
│   └── instructions.md         # OpenAI Codex instructions (SSOT link -> AGENTS.md)
├── scripts/
│   └── run_linters.py          # Deterministic Python & JS/TS linter script
├── skills/                     # [Primary Source] Agent Skills (playbooks)
│   └── e2e-evaluator/
│       ├── SKILL.md            # Pre-push end-to-end evaluation playbook
│       └── run_e2e.py          # Automated E2E test execution script
├── src/                        # Frontend Angular SPA components (Classic Telescopic UI)
│   ├── AGENTS.md               # Scope override for Frontend development
│   ├── app.component.html      # Top nav, BYOK settings drawer & telescopic canvas
│   ├── app.component.ts        # Signals, state management, model selection & collapse
│   ├── app.component.spec.ts   # Angular component unit test suite
│   └── components/
│       └── story-node/         # Recursive story node component (grey pill triggers)
├── tests/
│   ├── test_app.py             # Pytest backend API unit test suite
│   └── test_e2e_browser.py     # Browser & API E2E verification test suite
├── index.html                  # Angular SPA entry HTML & classic typographic CSS
├── app.py                      # FastAPI backend server
├── pyproject.toml              # Python project configuration (uv)
└── README.md                   # Project documentation
```

---

## Getting Started

### 1. Prerequisites
- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (fast Python package manager)
- Node.js 18+ (for frontend Angular development & linting)

### 2. Installation & Setup
Clone the repository and sync virtual environment dependencies:
```bash
uv sync
```

### 3. Run the Web Application
Start the FastAPI server:
```bash
uv run python app.py
```
Open your browser and navigate to `http://127.0.0.1:8000`.

---

## Development & Testing Workflow

- **Start Dev Server**: `uv run python app.py`
- **Backend Unit Tests**: `uv run pytest`
- **Frontend Unit Tests**: `npm test`
- **E2E Evaluation Skill**: `uv run python skills/e2e-evaluator/run_e2e.py` (explicitly invoked by agent before commit/push)
- **Deterministic Antigravity Hook**: `uv run python scripts/run_linters.py` (triggered automatically via `.gemini/hooks/preCommit.json`).
