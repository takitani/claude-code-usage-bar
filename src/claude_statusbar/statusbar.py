#!/usr/bin/env python3
"""
Claude Subscription Status
Shows: Model+T | Session: X% Yh, Zpm | Week: X% Yd, DD/mon Ham
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

def parse_datetime(dt_str):
    """Parse ISO datetime string to datetime object"""
    if not dt_str:
        return None
    try:
        if isinstance(dt_str, str):
            target = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            if target.tzinfo:
                target = target.replace(tzinfo=None)
            return target
        return dt_str
    except:
        return None

def time_until(target):
    """Calculate time until target datetime"""
    if not target:
        return "?"

    now = datetime.now()
    if target <= now:
        return "0m"

    diff = target - now
    total_minutes = int(diff.total_seconds() / 60)
    total_hours = total_minutes // 60
    days = total_hours // 24

    if days > 0:
        return f"{days}d"
    elif total_hours > 0:
        return f"{total_hours}h"
    return f"{total_minutes}m"

def format_session_reset(target):
    """Format session reset time like '3pm' or '3:30pm'"""
    if not target:
        return "?"

    hour = target.hour
    minute = target.minute
    ampm = "am" if hour < 12 else "pm"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12

    if minute == 0:
        return f"{hour_12}{ampm}"
    return f"{hour_12}:{minute:02d}{ampm}"

def format_week_reset(target):
    """Format week reset like '01/jan 5am'"""
    if not target:
        return "?"

    day = target.day
    month = target.strftime("%b").lower()
    hour = target.hour
    minute = target.minute
    ampm = "am" if hour < 12 else "pm"
    hour_12 = hour % 12
    if hour_12 == 0:
        hour_12 = 12

    if minute == 0:
        return f"{day:02d}/{month} {hour_12}{ampm}"
    return f"{day:02d}/{month} {hour_12}:{minute:02d}{ampm}"

def main():
    # Load config
    cfg = load_usage_config()

    # Get model
    model, has_thinking = get_model_from_jsonl()
    model_str = format_model(model, has_thinking)

    # Session info
    s_pct = cfg.get('session_percent')
    s_target = parse_datetime(cfg.get('session_reset'))
    s_time = time_until(s_target)
    s_reset_str = format_session_reset(s_target)
    s_color = get_color(s_pct)
    s_pct_str = f"{s_pct}%" if s_pct is not None else "?"

    # Week info
    w_pct = cfg.get('week_percent')
    w_target = parse_datetime(cfg.get('week_reset'))
    w_time = time_until(w_target)
    w_reset_str = format_week_reset(w_target)
    w_color = get_color(w_pct)
    w_pct_str = f"{w_pct}%" if w_pct is not None else "?"

    # Output: 🤖Op+T | 📊2% 3h, 3pm | 📆1% 6d, 01/jan 5am
    print(
        f"{CYAN}🤖{model_str}{RESET} | "
        f"{s_color}📊{s_pct_str}{RESET} {s_time}, {s_reset_str} | "
        f"{w_color}📆{w_pct_str}{RESET} {w_time}, {w_reset_str}"
    )

if __name__ == '__main__':
    main()
