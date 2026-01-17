"""
Core autonomous agent using PydanticAI tools for filesystem interaction.
"""

import os
import asyncio
import uuid
from typing import Optional
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext


@dataclass
class AgentDeps:
    """Dependencies for the tools"""
    base_path: str  # The directory of the app being built


class CodeGenAgent:
    """Autonomous agent that uses tools to build web applications"""
    
    SYSTEM_PROMPT = """You are an autonomous web developer. 
Your goal is to build a functional, beautiful Web Application (not just a JSON API) in the provided directory.

THOUGHT PROCESS:
Start your response with a concise thinking process wrapped in <thought> tags (e.g., <thought>I need to create the database schema first.</thought>). This helps the user understand your reasoning.

WORKFLOW:
1. EXPLORE: Check the directory. If files exist, you are MODIFYING an existing app. Do not overwrite unless asked.
2. PLAN: Write out the DB schema and the UI pages needed.
3. BUILD:
   - Run `uv init --app --no-workspace` in the app directory to create a standalone `pyproject.toml`.
   - Use `uv add fastapi uvicorn sqlalchemy jinja2 python-multipart` (and any others needed) to manage dependencies via `pyproject.toml`.
   - Use `make_directory` to create folders like `static/` or `templates/`.
   - `models.py`: SQLAlchemy models.
   - `database.py`: SQLite connection and SessionLocal setup.
   - `templates/`: Jinja2 HTML templates. Use Tailwind CSS v4.
   - `main.py`: FastAPI routes that return `Jinja2Templates.TemplateResponse`. THIS MUST BE IN THE ROOT of the app directory.
4. VERIFY: Run `python -m py_compile main.py` or similar to check for syntax errors.

CRITICAL RULES:
- DEPENDENCIES: Do NOT use `requirements.txt`. Use `uv add` commands to install dependencies into the app's `pyproject.toml`.
- WEB APP, NOT API: Your routes MUST return HTML using templates.
- TEMPLATES: Use Jinja2 syntax (e.g., `{% if ... %}`, `{{ variable }}`). DO NOT use Mako/Perl syntax (e.g., `% if ...`).
- FORM INPUTS: Use `Form(...)` parameters in your routes for POST requests. DO NOT try to use SQLAlchemy models as Pydantic request bodies.
- NO NEW FOLDERS: Do NOT create a subfolder for the app (e.g., `apps/todo/todo_app`). Put `main.py` directly in the base path provided.
- SCOPE: Build the simplest possible version (MVP). Do NOT add User Authentication unless explicitly asked.
- DB LINKING: You MUST import Base from database.py into models.py (do not create a new Base).
- COMPLETE: Ensure `init_db()` is called on startup to create tables.

If you encounter an error (e.g., 'Address already in use'), ignore it and focus on ensuring the CODE in the files is correct and complete.
"""

    def __init__(self, model_str: str = "mistral:mistral-small-latest"):
        """Initialize agent with a model string like 'openai:gpt-4o'"""
        self.agent = Agent(
            model_str,
            deps_type=AgentDeps,
            system_prompt=self.SYSTEM_PROMPT,
        )
        
        # Conversation history and stats
        self.history = []
        self.total_usage = {"input": 0, "output": 0}
        
        # Logging callback
        self.log_callback = None
        
        # Register tools
        self._register_tools()

    def set_log_callback(self, callback):
        """Set a callback for logging agent actions"""
        self.log_callback = callback

    def log(self, message: str):
        """Log a message using callback or print"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message, flush=True)

    def _register_tools(self):
        """Define the 'Hands' of the agent"""
        
        @self.agent.tool
        async def list_files(ctx: RunContext[AgentDeps], path: str = ".") -> str:
            """List files and directories in a path"""
            self.log(f"📂 Agent is listing files in: {path}")
            full_path = os.path.join(ctx.deps.base_path, path)
            try:
                if not os.path.exists(full_path):
                    return "Directory does not exist."
                items = os.listdir(full_path)
                return "\n".join(items) if items else "Directory is empty"
            except Exception as e:
                return f"Error: {str(e)}"

        @self.agent.tool
        async def read_file(ctx: RunContext[AgentDeps], filename: str) -> str:
            """Read the content of a file"""
            self.log(f"📖 Agent is reading file: {filename}")
            full_path = os.path.join(ctx.deps.base_path, filename)
            try:
                with open(full_path, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading {filename}: {str(e)}"

        @self.agent.tool
        async def make_directory(ctx: RunContext[AgentDeps], path: str) -> str:
            """Create a directory (and any parent directories)"""
            self.log(f"📂 Agent is creating directory: {path}")
            full_path = os.path.join(ctx.deps.base_path, path)
            try:
                os.makedirs(full_path, exist_ok=True)
                return f"Successfully created directory {path}"
            except Exception as e:
                return f"Error creating directory {path}: {str(e)}"

        @self.agent.tool
        async def write_file(ctx: RunContext[AgentDeps], filename: str, content: str) -> str:
            """Write content to a file (creates parent directories if needed)"""
            self.log(f"✍️  Agent is writing file: {filename}")
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
            self.log(f"🔍 Agent is searching for '{pattern}' in {path}")
            full_path = os.path.join(ctx.deps.base_path, path)
            try:
                # Use grep -r for searching, async
                process = await asyncio.create_subprocess_exec(
                    "grep", "-r", pattern, ".",
                    cwd=full_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=10)
                output = stdout.decode()
                return output if output else "No matches found."
            except asyncio.TimeoutError:
                return "Search timed out."
            except Exception as e:
                return f"Search failed: {str(e)}"

        @self.agent.tool
        async def execute_command(ctx: RunContext[AgentDeps], command: str) -> str:
            """Execute a shell command in the app directory and return output"""
            self.log(f"💻 Agent is executing command: {command}")
            try:
                # Use asyncio for non-blocking execution
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=ctx.deps.base_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
                
                output = f"STDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}"
                return output
            except asyncio.TimeoutError:
                return "Command execution timed out after 30 seconds."
            except Exception as e:
                return f"Command execution failed: {str(e)}"

    async def get_suggested_name(self, prompt: str) -> str:
        """Ask the LLM for a suitable one-word folder name for the app"""
        self.log("🤖 Agent is suggesting an app name...")
        
        # Prepare a suffix
        suffix = uuid.uuid4().hex[:3]
        
        try:
            # We use the internal agent to generate a name
            result = await self.agent.run(
                f"Suggest a single, concise, lowercase alphanumeric word (e.g. 'todo', 'inventory', 'finance') to use as a folder name for this request: '{prompt}'. Output ONLY the word, no punctuation or explanation.",
                deps=AgentDeps(base_path=".")
            )
            
            # Safe attribute access for different PydanticAI versions/result types
            raw_output = str(getattr(result, 'data', getattr(result, 'output', result))).strip()
            self.log(f"📝 Raw naming response: {raw_output}")
            
            # 1. Strip out thought tags if they exist
            import re
            clean_output = re.sub(r'<thought>.*?</thought>', '', raw_output, flags=re.DOTALL).strip().lower()
            
            # 2. Extract just the first word in case it gave an explanation
            first_word = clean_output.split()[0] if clean_output else ""
            
            # 3. Clean to only alphanumeric
            clean_name = "".join(c for c in first_word if c.isalnum())
            
            # Combine with our suffix
            final_name = f"{clean_name}_{suffix}" if clean_name else f"app_{suffix}"
            return final_name
            
        except Exception as e:
            self.log(f"⚠️ Naming failed: {e}")
            return f"app_{suffix}"

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
