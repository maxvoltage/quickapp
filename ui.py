"""
ASCII UI utilities for QuickApp CLI
Provides simple terminal UI elements like spinners and status displays
"""

import sys
import time
import threading
from typing import Optional


class Spinner:
    """Simple ASCII spinner using rotating characters"""
    
    FRAMES = ['\\', '|', '/', '-']
    
    def __init__(self, message: str = "Processing"):
        self.message = message
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_index = 0
    
    def start(self):
        """Start the spinner animation"""
        self.running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()
    
    def stop(self, final_message: Optional[str] = None):
        """Stop the spinner animation"""
        self.running = False
        if self._thread:
            self._thread.join()
        # Clear the line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
        if final_message:
            print(final_message)
    
    def _animate(self):
        """Animation loop"""
        start_time = time.time()
        while self.running:
            frame = self.FRAMES[self._frame_index % len(self.FRAMES)]
            # Add elapsed time to dynamic appearance
            elapsed = int(time.time() - start_time)
            sys.stdout.write(f'\r{frame} {self.message} ({elapsed}s)...')
            sys.stdout.flush()
            self._frame_index += 1
            time.sleep(0.1)


def print_header():
    """Print the QuickApp header"""
    header = """
╔═══════════════════════════════════════════════════════════╗
║                      QuickApp v1.0                        ║
║            AI-Powered Web App Generator                   ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(header)


def print_context_usage(current_tokens: int, max_tokens: int):
    """Print context window usage"""
    percentage = (current_tokens / max_tokens) * 100
    display_percentage = min(percentage, 100.0)
    
    # Color coding based on usage
    if percentage < 50:
        color = '\033[92m'  # Green
    elif percentage < 80:
        color = '\033[93m'  # Yellow
    else:
        color = '\033[91m'  # Red
    
    reset = '\033[0m'
    
    print(f"\n{color}Usage: {current_tokens:,} / {max_tokens:,} tokens ({display_percentage:.1f}%){reset}")


def print_separator():
    """Print a simple separator line"""
    print("─" * 60)


def print_success(message: str):
    """Print success message in green"""
    print(f"\033[92m✓ {message}\033[0m")


def print_error(message: str):
    """Print error message in red"""
    print(f"\033[91m✗ {message}\033[0m")


def print_info(message: str):
    """Print info message in blue"""
    print(f"\033[94mℹ {message}\033[0m")


def print_warning(message: str):
    """Print warning message in yellow"""
    print(f"\033[93m⚠ {message}\033[0m")


def print_thought(text: str):
    """Print model's thought process in a dimmed style"""
    print(f"\n\033[2m💭 {text}\033[0m")


def get_user_input(prompt: str = "You") -> str:
    """Get user input with a formatted prompt"""
    return input(f"\n\033[96m{prompt}:\033[0m ").strip()
