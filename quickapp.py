#!/usr/bin/env python3
"""
QuickApp - AI-Powered Web App Generator
Main CLI application
"""

import asyncio
import os
import sys
import shutil
from dotenv import load_dotenv

from agent import CodeGenAgent
from ui import (
    Spinner,
    print_header,
    print_context_usage,
    print_separator,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_thought,
    get_user_input,
)


class QuickAppCLI:
    """Main CLI application"""
    
    def __init__(self, initial_app: str | None = None):
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.agent: CodeGenAgent | None = None
        self.running = True
        self.current_app_dir = initial_app
        
        if self.current_app_dir:
            # Normalize path
            if not os.path.isabs(self.current_app_dir) and not self.current_app_dir.startswith("apps/"):
                # If just a name is given, assume it's in apps/
                self.current_app_dir = os.path.join("apps", self.current_app_dir)
            
            if not os.path.exists(self.current_app_dir):
                print_warning(f"Note: Path {self.current_app_dir} does not exist yet. It will be created on first prompt.")

    
    def initialize_agent(self):
        """Initialize the AI agent"""
        try:
            model = os.getenv("QUICKAPP_MODEL", "mistral:mistral-small-latest")
            self.agent = CodeGenAgent(model_str=model)
            
            print_success(f"Initialized agent with model: {model}")
            
        except Exception as e:
            print_error(f"Failed to initialize agent: {e}")
            sys.exit(1)

        # Check for uv
        if shutil.which("uv") is None:
            print_error("❌ 'uv' is not installed or not in PATH.")
            print_info("Please install uv: https://docs.astral.sh/uv/getting-started/installation/")
            sys.exit(1)
    
    async def process_prompt(self, prompt: str):
        """Process user prompt and generate app"""
        # 1. Determine app directory
        if not self.current_app_dir:
            # Let the LLM decide the name
            candidate_name = await self.agent.get_suggested_name(prompt)
            
            print_info(f"🆕 Starting new app: {candidate_name}")
            self.current_app_dir = os.path.join("apps", candidate_name)
            os.makedirs(self.current_app_dir, exist_ok=True)
        else:
            print_info(f"🔄 updating app in: {self.current_app_dir}")
        
        # Remove spinner, let the agent print its actions
        spinner = Spinner("Agent is thinking")
        
        def handle_agent_log(msg: str):
            """Handle logs from the agent by pausing spinner"""
            if spinner.running:
                spinner.stop()
                print_info(msg)
                spinner.start()
            else:
                print_info(msg)

        try:
            # print_info("🧠 Agent is thinking...")
            spinner.start()
            # print_separator()
            
            # Configure agent logging
            self.agent.set_log_callback(handle_agent_log)
            
            # Run the autonomous agent
            result = await self.agent.run_task(prompt, self.current_app_dir)
            
            spinner.stop()
            print_success("Agent finished the task")
            
            # Parse and display thoughts
            import re
            thought_match = re.search(r'<thought>(.*?)</thought>', str(result), re.DOTALL)
            if thought_match:
                thought = thought_match.group(1).strip()
                print_thought(thought)
                # Remove thought from final message
                result_clean = re.sub(r'<thought>.*?</thought>', '', str(result), flags=re.DOTALL).strip()
            else:
                result_clean = str(result).strip()

            print_info("Agent Message:")
            print(f"\n{result_clean}\n")
            
            # Show how to run it
            print_separator()
            print_info(f"App location: {self.current_app_dir}")
            print_info("To run the app:")
            print_success(f"cd {self.current_app_dir}")
            print_success("uv run uvicorn main:app --reload")
            
            print_separator()
            
            # Show context usage
            current, max_tokens = self.agent.get_context_usage()
            print_context_usage(current, max_tokens)
            
        except Exception as e:
            spinner.stop()
            print_error(f"Agent building failed: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_command(self, user_input: str) -> bool:
        """
        Handle special commands
        
        Returns:
            True if command was handled, False otherwise
        """
        command = user_input.lower().strip()
        
        if command in ['exit', 'quit', 'q']:
            print_info("Goodbye! 👋")
            self.running = False
            return True
        
        if command == 'clear':
            self.agent.clear_history()
            print_success("Conversation history cleared")
            return True

        if command == 'new':
            self.current_app_dir = None
            self.agent.clear_history()
            print_success("Started a new session. Next prompt will create a new app.")
            return True
        
        if command == 'help':
            self.show_help()
            return True
        
        if command == 'status':
            self.show_status()
            return True
        
        if command.startswith('open '):
            path = user_input[5:].strip()
            if not os.path.isabs(path) and not path.startswith("apps/"):
                path = os.path.join("apps", path)
            
            self.current_app_dir = path
            os.makedirs(self.current_app_dir, exist_ok=True)
            print_success(f"Context switched to: {self.current_app_dir}")
            return True
        
        return False
    
    def show_help(self):
        """Show help message"""
        print_separator()
        print("\n📖 QuickApp Commands:\n")
        print("  [prompt]    - Describe the app you want to create")
        print("  open [name] - Switch to an existing app in apps/")
        print("  new         - Start a new app (reset context)")
        print("  clear       - Clear conversation history")
        print("  status      - Show current context usage")
        print("  help        - Show this help message")
        print("  exit/quit   - Exit QuickApp")
        print()
        print_separator()
    
    def show_status(self):
        """Show current status"""
        current, max_tokens = self.agent.get_context_usage()
        message_count = self.agent.get_message_count()
        
        print_separator()
        print(f"\n📊 Status:")
        print(f"  Current App: {self.current_app_dir or 'None'}")
        print(f"  Messages in history: {message_count}")
        print_context_usage(current, max_tokens)
        print_separator()
    
    async def run(self):
        """Main application loop"""
        print_header()
        
        print_info("Initializing QuickApp...")
        self.initialize_agent()
        
        if self.current_app_dir:
            print_info(f"📁 Resuming work in: {self.current_app_dir}")

        print_separator()
        print("\n💡 Tip: Describe the web app you want to create")
        print("   Example: 'Create a to-do list app'")
        print("   Type 'help' for commands\n")
        print_separator()
        
        while self.running:
            try:
                # Get user input
                user_input = get_user_input()
                
                if not user_input:
                    continue
                
                # Handle commands
                if self.handle_command(user_input):
                    continue
                
                # Process as app generation prompt
                await self.process_prompt(user_input)
                
            except KeyboardInterrupt:
                print("\n")
                print_info("Use 'exit' to quit")
                continue
            except EOFError:
                print("\n")
                break
            except Exception as e:
                print_error(f"Unexpected error: {e}")
                import traceback
                traceback.print_exc()
        
def main():
    """Entry point"""
    import argparse
    parser = argparse.ArgumentParser(description="QuickApp CLI")
    parser.add_argument("app_path", nargs="?", help="Optional path to an existing app directory")
    args = parser.parse_args()

    cli = QuickAppCLI(initial_app=args.app_path)
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
