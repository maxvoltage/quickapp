#!/usr/bin/env python3
"""
QuickApp - AI-Powered Web App Generator
Main CLI application
"""

import asyncio
import os
import sys
from pathlib import Path
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
    get_user_input,
)


class QuickAppCLI:
    """Main CLI application"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.agent: CodeGenAgent | None = None
        self.running = True
    
    def initialize_agent(self):
        """Initialize the AI agent"""
        try:
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                print_error("MISTRAL_API_KEY not found in environment variables")
                print_info("Please set your Mistral API key:")
                print_info("  export MISTRAL_API_KEY='your-key-here'")
                sys.exit(1)
            
            model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
            self.agent = CodeGenAgent(api_key=api_key, model=model)
            
            print_success(f"Initialized agent with model: {model}")
            
        except Exception as e:
            print_error(f"Failed to initialize agent: {e}")
            sys.exit(1)
    
    async def process_prompt(self, prompt: str):
        """Process user prompt and generate app"""
        # 1. Prepare directory
        app_name = prompt.lower().split()[0] # Crude way to get a name if not specified
        app_dir = os.path.join("apps", app_name)
        os.makedirs(app_dir, exist_ok=True)
        
        spinner = Spinner("Agent is building your app autonomously")
        
        try:
            spinner.start()
            
            # Run the autonomous agent
            result = await self.agent.run_task(prompt, app_dir)
            
            spinner.stop()
            print_success("Agent finished the task")
            
            print_info("Agent Message:")
            print(f"\n{result}\n")
            
            # Show how to run it
            print_separator()
            print_info(f"App built at: {app_dir}")
            print(f"\n  cd {app_dir}")
            print(f"  uv run uvicorn main:app --reload")
            print(f"\n  Then open: http://localhost:8000\n")
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
        
        if command == 'help':
            self.show_help()
            return True
        
        if command == 'status':
            self.show_status()
            return True
        
        return False
    
    def show_help(self):
        """Show help message"""
        print_separator()
        print("\n📖 QuickApp Commands:\n")
        print("  [prompt]  - Describe the app you want to create")
        print("  clear     - Clear conversation history")
        print("  status    - Show current context usage")
        print("  help      - Show this help message")
        print("  exit/quit - Exit QuickApp")
        print()
        print_separator()
    
    def show_status(self):
        """Show current status"""
        current, max_tokens = self.agent.get_context_usage()
        message_count = self.agent.get_message_count()
        
        print_separator()
        print(f"\n📊 Status:")
        print(f"  Messages in history: {message_count}")
        print_context_usage(current, max_tokens)
        print_separator()
    
    async def run(self):
        """Main application loop"""
        print_header()
        
        print_info("Initializing QuickApp...")
        self.initialize_agent()
        
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
    cli = QuickAppCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
