#!/usr/bin/env python3
"""
Claude Code Subscription Status Bar
Shows: Model+T | Session% ⏱️reset | Week% ⏱️reset

Works with Claude Code subscription plans (Pro/Team).
Usage data is cached in ~/.claude-usage.json and updated by a background job.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ANSI colors
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
RESET = '\033[0m'
DIM = '\033[2m'

# File paths
USAGE_FILE = Path.home() / '.claude-usage.json'
CLAUDE_PROJECTS = Path.home() / '.claude' / 'projects'


def load_usage_config():
    """Load usage config from JSON file"""
    defaults = {
        'session_percent': None,
        'session_reset_hour': None,
        'week_percent': None,
        'week_reset': None
    }
    try:
        if USAGE_FILE.exists():
            with open(USAGE_FILE) as f:
                data = json.load(f)
                defaults.update(data)
    except Exception:
        pass
    return defaults


def get_model_from_jsonl():
    """Get current model and thinking mode from recent JSONL conversation files"""
    if not CLAUDE_PROJECTS.exists():
        return None, False

    try:
        jsonl_files = sorted(
            CLAUDE_PROJECTS.rglob("*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
    except Exception:
        return None, False

    latest_model = None
    has_thinking = False

    for f in jsonl_files[:30]:
        # Skip subagent files
        if 'agent-' in f.name:
            continue
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                for line in fp:
                    try:
                        d = json.loads(line)
                        msg = d.get('message', {})
                        m = msg.get('model')
                        if m:
                            latest_model = m
                        content = msg.get('content', [])
                        if isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get('type') == 'thinking':
                                    has_thinking = True
                    except Exception:
                        continue
        except Exception:
            continue
        if latest_model:
            break

    return latest_model, has_thinking


def format_model(model, has_thinking):
    """Format model name for display (Op, So, Ha + T for thinking)"""
    if not model:
        return "?"

    model_lower = model.lower()
    if 'opus' in model_lower:
        name = 'Op'
    elif 'sonnet' in model_lower:
        name = 'So'
    elif 'haiku' in model_lower:
        name = 'Ha'
    else:
        name = '?'

    if has_thinking:
        return f"{name}+T"
    return name


def get_color(pct):
    """Get ANSI color based on usage percentage"""
    if pct is None:
        return DIM
    if pct >= 80:
        return RED
    if pct >= 50:
        return YELLOW
    return GREEN


def time_until(target_hour=None, target_datetime=None):
    """Calculate human-readable time until reset"""
    now = datetime.now()

    if target_datetime:
        try:
            if isinstance(target_datetime, str):
                # Handle ISO format with optional timezone
                target = datetime.fromisoformat(target_datetime.replace('Z', '+00:00'))
                if target.tzinfo:
                    target = target.replace(tzinfo=None)
            else:
                target = target_datetime
        except Exception:
            return "?"
    elif target_hour is not None:
        target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
    else:
        return "?"

    if target <= now:
        return "now"

    diff = target - now
    total_minutes = int(diff.total_seconds() / 60)
    total_hours = total_minutes // 60
    days = total_hours // 24

    if days > 0:
        hours = total_hours % 24
        return f"{days}d{hours}h"
    elif total_hours > 0:
        mins = total_minutes % 60
        return f"{total_hours}h{mins:02d}m"
    return f"{total_minutes}m"


def format_output(model_str, s_pct, s_reset, w_pct, w_reset, use_color=True):
    """Format the status bar output"""
    if use_color:
        s_color = get_color(s_pct)
        w_color = get_color(w_pct)

        s_str = f"{s_pct}%" if s_pct is not None else "?%"
        w_str = f"{w_pct}%" if w_pct is not None else "?%"

        return (
            f"{CYAN}🤖{model_str}{RESET} | "
            f"{s_color}📊{s_str}{RESET} ⏱️{s_reset} | "
            f"{w_color}📆{w_str}{RESET} ⏱️{w_reset}"
        )
    else:
        s_str = f"{s_pct}%" if s_pct is not None else "?%"
        w_str = f"{w_pct}%" if w_pct is not None else "?%"
        return f"🤖{model_str} | 📊{s_str} ⏱️{s_reset} | 📆{w_str} ⏱️{w_reset}"


def main():
    """Main entry point"""
    # Check for --no-color flag
    use_color = '--no-color' not in sys.argv

    # Load usage config
    cfg = load_usage_config()

    # Get model info from JSONL files
    model, has_thinking = get_model_from_jsonl()
    model_str = format_model(model, has_thinking)

    # Session info
    s_pct = cfg.get('session_percent')
    s_reset_hour = cfg.get('session_reset_hour')
    s_reset = time_until(target_hour=s_reset_hour) if s_reset_hour else "?"

    # Week info
    w_pct = cfg.get('week_percent')
    w_reset = time_until(target_datetime=cfg.get('week_reset'))

    # Output
    print(format_output(model_str, s_pct, s_reset, w_pct, w_reset, use_color))


if __name__ == '__main__':
    main()
