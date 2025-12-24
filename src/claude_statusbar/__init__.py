"""
Claude Code Subscription Status Bar

Shows your Claude subscription usage in the terminal/status bar:
- Current model (Opus/Sonnet/Haiku) with thinking indicator (+T)
- Session usage % and time until reset
- Weekly usage % and time until reset

For Claude Code Pro/Team subscription users.
"""

__version__ = "2.0.0"

from .statusbar import main, format_output, get_model_from_jsonl
from .update_usage import fetch_usage_via_pty, parse_usage_output

__all__ = [
    'main',
    'format_output',
    'get_model_from_jsonl',
    'fetch_usage_via_pty',
    'parse_usage_output',
]
