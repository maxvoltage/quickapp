# QuickApp - AI-Powered Web App Generator

QuickApp is a terminal-based coding agent that generates complete FastAPI + Jinja2 + SQLite web applications from simple prompts.

## Features

- 🤖 **AI-Powered**: Uses Mistral AI via PydanticAI to understand your requirements
- 🚀 **Fast Generation**: Creates multi-file FastAPI applications in seconds
- 💬 **Conversational**: Maintains context across multiple prompts
- 📊 **Context Tracking**: Shows token usage to prevent context overflow
- 🎨 **Simple ASCII UI**: Clean terminal interface with progress indicators
- 🗄️ **SQLite + WAL**: Generated apps use SQLite with Write-Ahead Logging

## Installation

1. Clone this repository
2. Install dependencies using uv:
```bash
uv sync
```

3. Set your Mistral API key:
```bash
export MISTRAL_API_KEY="your-api-key-here"
```

## Usage

Run the CLI:
```bash
uv run python quickapp.py
```

Then simply describe what you want to build:
```
You: Create a to-do list app
```

The agent will:
1. Generate a complete FastAPI application
2. Create all necessary files (main.py, templates, models, etc.)
3. Set up SQLite database with WAL mode
4. Provide the command to run your new app

### Commands

- Type your prompt to generate/modify apps
- `clear` - Clear conversation history
- `exit` or `quit` - Exit the application

## Generated App Structure

```
apps/
└── your-app-name/
    ├── main.py              # FastAPI application
    ├── models.py            # Database models
    ├── database.py          # Database configuration
    ├── templates/
    │   ├── base.html        # Base template
    │   └── index.html       # Main page
    ├── static/
    │   └── style.css        # Styles
    └── requirements.txt     # App dependencies
```

## Running Generated Apps

After generation, run:
```bash
cd apps/your-app-name
uv run uvicorn main:app --reload
```

Or install dependencies first:
```bash
cd apps/your-app-name
uv venv
uv pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000 in your browser.

## Requirements

- Python 3.10+
- Mistral API key
- Internet connection

## License

MIT
