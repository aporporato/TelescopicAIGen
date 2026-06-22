# AI Telescopic Text

AI Telescopic Text is an interactive writing experiment inspired by the classic [Telescopic Text](https://www.telescopictext.org/) format. Instead of using a predefined, hardcoded hierarchy of substitutions, this application dynamically requests contextual expansions from an LLM (Anthropic's Claude 3) in real-time.

Clicking any word in a sentence automatically replaces that word with a blank (`_`) in the background, asks the LLM to write a fitting, detailed expansion for that blank, and injects it recursively.

## Features

- **Dynamic LLM Expansions**: Contextualized, natural phrase expansions generated on-the-fly by Anthropic's Claude API.
- **Recursive Branching**: Expanded words themselves can be clicked to be expanded further.
- **Interactive Collapsing**: Hovering over any expanded block displays a collapse handler (`×`) to fold it back to its original state.
- **Premium Dark Design System**: Built with modern typography (Outfit & Inter), glassmorphism, glowing accents, and smooth hover/loader states.
- **State-driven Rendering**: Dynamic tree-based DOM reconstruction on the frontend with zero build tools (Vanilla JS/CSS).
- **FastAPI Backend**: Simple, asynchronous, type-safe API routing.

## Project Structure

```text
TelescopicAI/
├── static/
│   └── style.css          # Premium dark design styles and animations
├── templates/
│   └── index.html         # Main workspace layout and state-driven JS
├── app.py                 # FastAPI backend server with /api/expand endpoint
├── pyproject.toml         # Python project configuration for uv dependency management
├── .env                   # Environment config (API keys)
└── README.md              # Project documentation
```

## Setup Instructions

### Prerequisites
- [uv](https://github.com/astral-sh/uv) (Astral's fast Python package installer and resolver)
- An Anthropic API Key

### 1. Configure Environment Variables
Create or update your `.env` file in the root directory and add your Anthropic API Key:
```env
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
```

### 2. Setup the Environment
Using `uv`, you can install dependencies and prepare the virtual environment automatically:
```bash
uv sync
```
This command creates a local virtual environment (`.venv`) and syncs all dependencies listed in `pyproject.toml`.

### 3. Run the Application
You can run the application directly within the virtual environment using:
```bash
uv run python app.py
```
Or start uvicorn directly:
```bash
uv run uvicorn app:app --reload
```

Open your browser and navigate to `http://127.0.0.1:8000` to start expanding your texts!

## How It Works Under the Hood

1. **State representation**: The text is modeled as a tree. Nodes are either plain words or expandable nodes with children arrays.
2. **Context Creation**: When a word is clicked, the tree is traversed to form the full current sentence, replacing the clicked node with a blank `_`.
3. **API Call**: The sentence (e.g. `"I _ tea."`) is sent to the backend `/api/expand` route.
4. **LLM Generation**: Claude receives the sentence with the blank, generates a 2-6 word replacement, and returns a JSON payload:
   ```json
   {
     "replacement": "carefully brewed a hot cup of",
     "sentence": "I carefully brewed a hot cup of tea."
   }
   ```
5. **DOM Injection**: The frontend tokenizes the replacement, converts it to nested tree nodes, and dynamically updates the DOM.
