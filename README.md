# AI Telescopic Text

AI Telescopic Text is an interactive writing experiment inspired by the classic [Telescopic Text](https://www.telescopictext.org/) format. Instead of using a predefined, hardcoded hierarchy of substitutions, this application dynamically requests contextual expansions from an LLM in real-time.

Clicking any word in a sentence replaces that word with a blank (`_`) in the background, requests a detailed expansion from your chosen LLM, and injects it recursively, letting you create deeply nested, expandable stories.

---

## Features

- **Multiple LLM Providers**: Choose dynamically between:
  - **OpenAI** `gpt-5.4-nano`
  - **Google** `gemini-3.5-flash`
  - **Anthropic** `claude-haiku-4-5`
- **Bring Your Own Key (BYOK)**: Strict privacy-first design. All API keys are processed strictly in-memory, never recorded on the server, and never saved in `localStorage` or `sessionStorage` (lost instantly upon page refresh). Keys are cached in-memory per provider for convenient switching.
- **Recursive Branching**: Expanded words themselves can be clicked to be expanded further.
- **Interactive Collapsing**: Double-click any expanded block to collapse it back to its original state.
- **Minimalist Typographic Design**: A clean, light typographic style reminiscent of the classic telescopictext.org, using high-quality serif body font, subtle shaded triggers, and smooth micro-animations.
- **FastAPI Backend**: A lightweight, asynchronous, type-safe API backend with clean JSON-parsing fallbacks.

---

## Project Structure

```text
TelescopicAI/
├── static/
│   └── style.css          # Minimalist typographic styling and transition effects
├── templates/
│   └── index.html         # Main workspace layout and state-driven Vanilla JS
├── app.py                 # FastAPI backend server with /api/expand and /api/config endpoints
├── pyproject.toml         # Python project configuration for uv dependency management
├── uv.lock                # Locked dependencies for reproducible environments
└── README.md              # Project documentation
```

---

## Setup Instructions

### Prerequisites
- [uv](https://github.com/astral-sh/uv) (Astral's fast Python package installer and manager)

### 1. Setup the Python Environment
Using `uv`, you can prepare the virtual environment and sync dependencies automatically:
```bash
uv sync
```
This command creates a local virtual environment (`.venv`) and installs all dependencies listed in `pyproject.toml`.

### 2. Run the Application
Start the FastAPI server using `uv run`:
```bash
uv run python app.py
```
Or start uvicorn directly:
```bash
uv run uvicorn app:app --reload
```

The application will start running at `http://127.0.0.1:8000`.

---

## How to Use It

1. Open your browser and navigate to `http://127.0.0.1:8000`.
2. Click **Settings** in the top-right navigation bar to open the settings drawer.
3. Select your preferred LLM provider by clicking its card:
   - **OpenAI** (`gpt-5.4-nano`)
   - **Google** (`gemini-3.5-flash`)
   - **Anthropic** (`claude-haiku-4-5`)
4. Paste your API key into the input field. Note that each provider maintains its own key state in-memory so you can switch models freely without losing your keys.
5. Click on any shaded word trigger in the canvas (e.g. `"I"`, `"made"`, or `"tea"`) to trigger a dynamic AI expansion.
6. **Double-click** anywhere inside an expanded phrase to collapse it back into its original single word.
7. Click **Reset** in the top-right navigation bar at any point to start over.
