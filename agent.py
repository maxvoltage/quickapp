"""
Core autonomous agent using PydanticAI tools for filesystem interaction.
"""

import os
import subprocess
import shlex
from typing import Optional, List, Dict
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.mistral import MistralModel


@dataclass
class AgentDeps:
    """Dependencies for the tools"""
    base_path: str  # The directory of the app being built


class CodeGenAgent:
    """Autonomous agent that uses tools to build web applications"""
    
    SYSTEM_PROMPT = """You are an autonomous web developer. 
Your goal is to build a functional, beautiful Web Application (not just a JSON API) in the provided directory.

WORKFLOW:
1. EXPLORE: Check the directory.
2. PLAN: Write out the DB schema and the UI pages needed.
3. BUILD:
   - Use `make_directory` to create folders like `static/` or `templates/` before using them.
   - `models.py`: SQLAlchemy models.
   - `database.py`: SQLite connection and SessionLocal setup.
   - `templates/`: Jinja2 HTML templates. Use Tailwind CSS v4.
   - `main.py`: FastAPI routes that return `Jinja2Templates.TemplateResponse`.
4. VERIFY: Run `python -m py_compile main.py` or similar to check for syntax errors.

CRITICAL RULES:
- WEB APP, NOT API: Your routes MUST return HTML using templates.
- TEMPLATES: Use Jinja2 syntax (e.g., `{% if ... %}`, `{{ variable }}`). DO NOT use Mako/Perl syntax (e.g., `% if ...`).
- FORM INPUTS: Use `Form(...)` parameters in your routes for POST requests. DO NOT try to use SQLAlchemy models as Pydantic request bodies (this causes crashes).
- CONTEXT ISOLATION: If the user asks for a NEW application (e.g., you built a Joke app and now they ask for a Todo app), you MUST start from scratch mentally. Do not mix models, routes, or logic from the previous application. Each app is its own isolated workspace.
- SCOPE: Build the simplest possible version (MVP). Do NOT add User Authentication, Login, or complex relationships unless explicitly asked. Assume a single-user environment.
- COMPLETE: Ensure `init_db()` is called on startup to create tables.

If you encounter an error (e.g., 'Address already in use'), ignore it and focus on ensuring the CODE in the files is correct and complete.
"""

    def __init__(self, api_key: Optional[str] = None, model: str = "mistral-large-latest"):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY not set")
            
        self.agent = Agent(
            f'mistral:{model}',
            deps_type=AgentDeps,
            system_prompt=self.SYSTEM_PROMPT,
        )
        
        # Conversation history and stats
        self.history = []
        self.total_usage = {"input": 0, "output": 0}
        
        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Define the 'Hands' of the agent"""
        
        @self.agent.tool
        async def list_files(ctx: RunContext[AgentDeps], path: str = ".") -> str:
            """List files and directories in a path"""
            full_path = os.path.join(ctx.deps.base_path, path)
            try:
                items = os.listdir(full_path)
                return "\n".join(items) if items else "Directory is empty"
            except Exception as e:
                return f"Error: {str(e)}"

        @self.agent.tool
        async def read_file(ctx: RunContext[AgentDeps], filename: str) -> str:
            """Read the content of a file"""
            full_path = os.path.join(ctx.deps.base_path, filename)
            try:
                with open(full_path, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading {filename}: {str(e)}"

        @self.agent.tool
        async def make_directory(ctx: RunContext[AgentDeps], path: str) -> str:
            """Create a directory (and any parent directories)"""
            full_path = os.path.join(ctx.deps.base_path, path)
            try:
                os.makedirs(full_path, exist_ok=True)
                return f"Successfully created directory {path}"
            except Exception as e:
                return f"Error creating directory {path}: {str(e)}"

        @self.agent.tool
        async def write_file(ctx: RunContext[AgentDeps], filename: str, content: str) -> str:
            """Write content to a file (creates parent directories if needed)"""
            full_path = os.path.join(ctx.deps.base_path, filename)
            try:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
                return f"Successfully wrote to {filename}"
            except Exception as e:
                return f"Error writing {filename}: {str(e)}"

        @self.agent.tool
        async def search_files(ctx: RunContext[AgentDeps], pattern: str, path: str = ".") -> str:
            """Search for a pattern (grep) in the workspace"""
            full_path = os.path.join(ctx.deps.base_path, path)
            try:
                # Use grep -r for searching
                result = subprocess.run(
                    ["grep", "-r", pattern, "."],
                    cwd=full_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout if result.stdout else "No matches found."
            except Exception as e:
                return f"Search failed: {str(e)}"

        @self.agent.tool
        async def execute_command(ctx: RunContext[AgentDeps], command: str) -> str:
            """Execute a shell command in the app directory and return output"""
            try:
                # Use shlex to handle command and avoid injection issues? 
                # Actually, we want the agent to be powerful.
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=ctx.deps.base_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                return output
            except Exception as e:
                return f"Command execution failed: {str(e)}"

    async def run_task(self, prompt: str, app_path: str):
        """Run the agent on a specific task within an app directory"""
        deps = AgentDeps(base_path=app_path)
        
        # Run with history
        result = await self.agent.run(prompt, deps=deps, message_history=self.history)
        
        # Update history and usage
        self.history = result.all_messages()
        self.total_usage["input"] += result.usage().request_tokens or 0
        self.total_usage["output"] += result.usage().response_tokens or 0
        
        # Safe attribute access for different PydanticAI versions
        return getattr(result, 'data', getattr(result, 'output', str(result)))

    def get_context_usage(self) -> tuple[int, int]:
        """Return (current_tokens, max_tokens)"""
        total = self.total_usage["input"] + self.total_usage["output"]
        return total, 32000

    def get_message_count(self) -> int:
        """Return number of messages in history"""
        return len(self.history)

    def clear_history(self):
        """Reset the conversation history"""
        self.history = []
