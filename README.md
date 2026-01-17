# QuickApp

AI-powered tool for generating FastAPI web applications.

## Features

- **Mistral AI**: Uses PydanticAI for reasoning and code generation.
- **FastAPI + Jinja2**: Generates full-stack web apps with SQLite.
- **Standalone Apps**: Each app is a separate `uv` project.
- **Conversational**: Maintains context for iterative development.
- **Live Tracking**: Displays token usage and agent actions.

## Example App

[Simple CRUD Budget App](https://github.com/maxvoltage/simple-crud-budget)

## Architecture

### Workflow (Who does what?)

1.  **Start (Framework)**: You run `quickapp.py`. The **Framework** sets up the environment and loads your API keys.
2.  **Prompt (User)**: You describe an app. The **Framework** packages this request with the current project state (if any) and sends it to the **LLM**.
3.  **Plan (LLM)**: The **LLM** (the "Agent") processes your request, looks at existing files, and creates a mental map of the tasks required.
4.  **Execute (System/LLM)**: 
    - The **LLM** decides *which* tool to use (e.g., "I need to write to models.py").
    - The **Framework** provides the *hands* (the Python functions that actually touch your hard drive).
5.  **Verify (Iterative)**: The **LLM** runs a shell command via the **Framework** to check for syntax errors. If it sees a mistake, the **LLM** decides how to fix it and repeats the loop.
6.  **Report (Framework)**: The **Framework** streams the LLM's "thoughts" and actions to your terminal in real-time.

### Core Modules

- **`quickapp.py`**: The **System Orchestrator**. It manages the CLI life cycle, handles user input/commands, and provides the LLM with access to your computer's tools.
- **`agent.py`**: The **Intelligence Layer**. It defines the PydanticAI agent and the **System Prompt** (the instructions that tell the LLM it is a Senior Developer). It also defines the *Tools* (filesystem APIs) that the LLM is allowed to call.
- **`ui.py`**: The **Interface Layer**. A styling module that turns raw logic and agent events into a terminal experience.

### Division of Labor

| Feature | The LLM (The Brain) | The Framework (The Body) |
| :--- | :--- | :--- |
| **Logic** | Decides *what* code to write and *how* to fix bugs. | Doesn't know code; just follows the LLM's tool calls. |
| **Filesystem** | Requests to read/write specific files. | Actually opens the files and writes to disk. |
| **Console** | Thinks in text and `<thought>` tags. | Extracts thoughts and prints them with colors and spinners. |
| **Safety** | Restricted to the tools provided in `agent.py`. | Enforces the boundaries (e.g., staying within the `apps/` directory). |

### The "Hands vs. Brain" Relationship

QuickApp uses a **tool-calling architecture** (via PydanticAI) to bridge the gap between AI reasoning and physical file operations:

1.  **The Brain (LLM)**: When you ask for an app to be created, the LLM thinks about the structure and realizes it needs to create a file. It looks at its available tools and decides to call `write_file(filename="main.py", content="...")`.
2.  **The Hands (Framework)**: The Python code in `agent.py` receives this request. It validates the path (ensuring the LLM isn't trying to write to your system folders) and then physically creates the file on your disk.
3.  **The Loop**: After writing, the LLM might decide to call `execute_command("python -m py_compile main.py")`. The framework runs the command, captures the output, and sends it back to the LLM. If there's a syntax error, the LLM reads it and issues a new `write_file` call to fix the mistake.

This creates a self-healing development cycle where the LLM is responsible for the intent and the Framework is responsible for the action and safety.

### The "FileSystem as Context" Hypothesis

Legacy files like `generator.py` and `templates.py` are no longer executed by the core application. However, they remain in the repository as a **"Blueprint Reference"** for the AI.

When the agent uses the `read_file` tool to explore the root directory, it seems like it "studies" these files to understand the preferred coding patterns, database linking strategies, and template structures. This acts as a form of few-shot prompting, improving the quality and consistency of generated applications without hardcoding logic.

This is a bit counterintuitive to me, but I noticed the created apps often fail when those files are deleted.

## App Structure

```
apps/
└── [app_name]/
    ├── main.py        # FastAPI routes & logic
    ├── models.py      # SQLAlchemy models
    ├── database.py    # DB connection & init_db()
    ├── templates/     # Jinja2 templates (Tailwind 4)
    ├── static/        # Static assets
    └── pyproject.toml # Dependencies managed by uv
```

## Installation

1. Clone repository.
2. Install dependencies:
```bash
uv sync
```
3. Set up environment variables:
   - Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` and add your API key (e.g., `MISTRAL_API_KEY` for Mistral models):
   ```env
   MISTRAL_API_KEY=your-key-here
   QUICKAPP_MODEL=mistral:mistral-small-latest
   ```
   Find more about model API key env variable key and model name string in PydanticAI docs Models&Providers [page](https://ai.pydantic.dev/models/overview/). These env variables are used in PydanticAI.

   Some examples:
   - **Mistral**: `mistral:mistral-small-latest` (set `MISTRAL_API_KEY`)
   - **OpenAI**: `openai:gpt-4o` (set `OPENAI_API_KEY`)
   - **Anthropic**: `anthropic:claude-3-5-sonnet-latest` (set `ANTHROPIC_API_KEY`)
   - **Gemini**: `google-gla:gemini-1.5-flash` (set `GOOGLE_API_KEY`)


## Usage

```bash
uv run python quickapp.py
```

### Commands
- `new`: Start fresh project. Without this command fired, it will overwrite the files in the current workspace (folder).
- `open [name]`: Resume work in existing app folder.
- `clear`: Clear conversation history.
- `status`: Check token usage and how many conversation are in the history.
- `help`: Show commands.
- `exit`: Quit.


## Running Apps

```bash
cd apps/[app_name]
uv run uvicorn main:app --reload
```

## Requirements

- Python 3.10+
- Mistral API key


## Current Limitations

- It seems like it often write bad codes when the app doesn't need a database actions.
- It doesn't seem like capable of reverting the changes when it makes a mistake. However, this is probably due to the mistral-small-latest model having a small context window.
- Currently it leads the LLM to use fastapi, jinja2, sqlalchemy, and tailwindcss and suitable to make a simple CRUD based apps. It usually needs multiple prompt to create actions little by little.


## License

MIT
