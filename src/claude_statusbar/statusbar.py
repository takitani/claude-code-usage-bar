#!/usr/bin/env python3
"""
Claude Subscription Status
Shows: Model+T | Session% ⏱️reset | Week% ⏱️reset
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

# ANSI colors
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
RESET = '\033[0m'
DIM = '\033[2m'

USAGE_FILE = Path.home() / '.claude-usage.json'
CACHE_FILE = Path.home() / '.claude-status-cache.json'

def load_usage_config():
    """Load manual usage config"""
    defaults = {
        'session_percent': None,
        'session_reset_hour': 21,  # 9pm
        'week_percent': None,
        'week_reset': None
    }
    try:
        if USAGE_FILE.exists():
            with open(USAGE_FILE) as f:
                data = json.load(f)
                defaults.update(data)
    except:
        pass
    return defaults

def get_model_from_jsonl():
    """Get model and thinking from recent JSONL files"""
    data_path = Path.home() / '.claude' / 'projects'
    if not data_path.exists():
        return None, False

    jsonl_files = sorted(
        data_path.rglob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    latest_model = None
    has_thinking = False

    for f in jsonl_files[:30]:
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
                    except:
                        continue
        except:
            continue
        if latest_model:
            break

    return latest_model, has_thinking

def format_model(model, has_thinking):
    """Format model name"""
    if not model:
        return "?"
    if 'opus' in model.lower():
        name = 'Op'
    elif 'sonnet' in model.lower():
        name = 'So'
    elif 'haiku' in model.lower():
        name = 'Ha'
    else:
        name = '?'
    if has_thinking:
        return f"{name}+T"
    return name

def get_color(pct):
    """Color based on percentage"""
    if pct is None:
        return DIM
    if pct >= 80:
        return RED
    if pct >= 50:
        return YELLOW
    return GREEN

def time_until(target_hour=None, target_datetime=None):
    """Calculate time until target"""
    now = datetime.now()

    if target_datetime:
        # Parse ISO datetime
        try:
            if isinstance(target_datetime, str):
                target = datetime.fromisoformat(target_datetime.replace('Z', '+00:00'))
                if target.tzinfo:
                    target = target.replace(tzinfo=None)
            else:
                target = target_datetime
        except:
            return "?"
    elif target_hour is not None:
        target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
    else:
        return "?"

    if target <= now:
        return "0m"

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

def main():
    # Load config
    cfg = load_usage_config()

    # Get model
    model, has_thinking = get_model_from_jsonl()
    model_str = format_model(model, has_thinking)

    # Session info
    s_pct = cfg.get('session_percent')
    # Prefer session_reset (datetime) over session_reset_hour (backwards compat)
    if cfg.get('session_reset'):
        s_reset = time_until(target_datetime=cfg.get('session_reset'))
    else:
        s_reset = time_until(target_hour=cfg.get('session_reset_hour', 21))
    s_color = get_color(s_pct)
    s_str = f"{s_pct}%" if s_pct is not None else "?%"

    # Week info
    w_pct = cfg.get('week_percent')
    w_reset = time_until(target_datetime=cfg.get('week_reset'))
    w_color = get_color(w_pct)
    w_str = f"{w_pct}%" if w_pct is not None else "?%"

    # Output: 🤖Op+T | 📊16%⏱️2h | 📅13%⏱️5d
    print(
        f"{CYAN}🤖{model_str}{RESET} | "
        f"{s_color}📊{s_str}{RESET} ⏱️{s_reset} | "
        f"{w_color}📆{w_str}{RESET} ⏱️{w_reset}"
    )

if __name__ == '__main__':
    main()
