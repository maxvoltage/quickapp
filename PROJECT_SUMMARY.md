# QuickApp - Project Summary

## What We Built

A terminal-based coding agent that generates complete FastAPI + Jinja2 + SQLite web applications from simple prompts using AI.

## Architecture

### Core Components

1. **`quickapp.py`** - Main CLI application
   - Async event loop for handling user input
   - Command processing (clear, status, help, exit)
   - Integration of agent and generator

2. **`agent.py`** - AI agent using PydanticAI + Mistral
   - Structured output using Pydantic models
   - Conversation history management
   - Token usage tracking
   - Context window monitoring

3. **`generator.py`** - Code generation engine
   - Transforms AI specifications into actual files
   - Creates complete project structure
   - Generates FastAPI routes, models, templates, and pyproject.toml

4. **`templates.py`** - Code templates
   - FastAPI application template with lifespan management
   - SQLAlchemy models with optimized SQLite WAL mode
   - Jinja2 HTML templates
   - Modern CSS styling

5. **`ui.py`** - ASCII UI utilities
   - Rotating spinner (`\ | / -`)
   - Context usage display with progress bar
   - Colored terminal output
   - User input handling

## Features

✅ **AI-Powered Generation** - Uses Mistral AI via PydanticAI  
✅ **Context Tracking** - Shows token usage (e.g., `1,250/32,000`)  
✅ **Conversation History** - Maintains context across prompts  
✅ **Multi-file Apps** - Generates complete project structure  
✅ **SQLite WAL Mode** - Optimized database configuration  
✅ **Simple ASCII UI** - Clean terminal interface  
✅ **uv Integration** - Fast dependency management  

## Usage

1. Set your Mistral API key in `.env`:
```bash
MISTRAL_API_KEY=your-key-here
```

2. Run QuickApp:
```bash
uv run python quickapp.py
```

3. Describe your app:
```
You: Create a to-do list app
```

4. Run the generated app:
```bash
cd apps/todo-list
uv run uvicorn main:app --reload
```

## Generated App Structure

```
apps/your-app-name/
├── main.py              # FastAPI application
├── models.py            # SQLAlchemy models
├── database.py          # DB config with WAL mode
├── templates/
│   ├── base.html        # Base Jinja2 template
│   └── index.html       # Main page
├── static/
│   └── style.css        # Modern CSS
├── pyproject.toml       # Modern uv project config
└── README.md           # App documentation
```

## Tech Stack

- **PydanticAI** - Agent framework
- **Mistral AI** - LLM provider
- **FastAPI** - Web framework for generated apps
- **Jinja2** - Template engine
- **SQLAlchemy** - ORM
- **SQLite** - Database with WAL mode
- **uv** - Package manager

## Commands

- `clear` - Clear conversation history
- `status` - Show context usage
- `help` - Show help message
- `exit`/`quit` - Exit application

## Next Steps

1. Add your Mistral API key to `.env`
2. Test the application with a simple prompt
3. Customize templates in `templates.py` if needed
4. Extend the agent's system prompt in `agent.py` for better results

## Notes

- Context window varies by model:
  - `mistral-small-latest`: 32,000 tokens
  - `mistral-medium-latest`: 32,000 tokens
  - `mistral-large-latest`: 128,000 tokens

- Token usage is estimated based on message history
- Generated apps use SQLite with WAL mode for better concurrency
- All generated apps include modern, responsive CSS
