#!/usr/bin/env python3
"""
Background job to capture /usage from Claude Code and update config
Run via cron or systemd timer every 5-10 minutes
"""

import subprocess
import sys
import re
import json
import os
import shutil
from pathlib import Path
from datetime import datetime

USAGE_FILE = Path.home() / '.claude-usage.json'

def find_claude():
    """Find claude executable in common locations"""
    # Try shutil.which first (uses PATH)
    claude = shutil.which('claude')
    if claude:
        return claude

    # Common installation paths
    home = Path.home()
    common_paths = [
        home / '.npm-global' / 'bin' / 'claude',
        home / '.local' / 'bin' / 'claude',
        home / '.nvm' / 'versions' / 'node',  # Will check subdirs
        Path('/usr/local/bin/claude'),
        Path('/usr/bin/claude'),
    ]

    for p in common_paths:
        if p.exists() and p.is_file():
            return str(p)
        # Check nvm versions
        if 'nvm' in str(p) and p.exists():
            for node_ver in p.iterdir():
                claude_path = node_ver / 'bin' / 'claude'
                if claude_path.exists():
                    return str(claude_path)

    # Last resort: try npx
    if shutil.which('npx'):
        return 'npx claude'

    return None

def parse_usage_output(text):
    """Parse /usage output text from Claude CLI"""
    data = {}

    # Session percentage: "XX% used" after "Current session"
    session_match = re.search(r'Current session\s+[█░▓\s]*(\d+)%\s*used', text, re.DOTALL)
    if session_match:
        data['session_percent'] = int(session_match.group(1))

    # Session reset: "Resets 1:59am" or "Resets 2pm" - parse to full datetime
    session_reset = re.search(r'Current session.*?Resets?\s+(\d+(?::\d+)?)(am|pm)', text, re.DOTALL | re.IGNORECASE)
    if session_reset:
        time_part = session_reset.group(1)  # "1:59" or "2"
        ampm = session_reset.group(2).lower()  # "am" or "pm"

        # Parse hour and minute
        if ':' in time_part:
            hour = int(time_part.split(':')[0])
            minute = int(time_part.split(':')[1])
        else:
            hour = int(time_part)
            minute = 0

        # Convert to 24h
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12:
            hour = 0

        # Calculate next reset datetime
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target = target.replace(day=target.day + 1)
        data['session_reset'] = target.isoformat()
        data['session_reset_hour'] = hour  # Keep for backwards compat

    # Week percentage (all models)
    week_match = re.search(r'Current week \(all models\)\s+[█░▓\s]*(\d+)%\s*used', text, re.DOTALL)
    if week_match:
        data['week_percent'] = int(week_match.group(1))

    # Week reset: "Resets Dec 30, 5pm" or similar
    week_reset = re.search(r'Current week.*?Resets?\s+([A-Za-z]+\s+\d+),?\s*(\d+(?::\d+)?(?:am|pm))', text, re.DOTALL | re.IGNORECASE)
    if week_reset:
        date_str = week_reset.group(1)  # "Dec 30"
        time_str = week_reset.group(2).lower()  # "5pm"

        # Parse time
        if ':' in time_str:
            hour = int(time_str.split(':')[0])
            minute = int(time_str.split(':')[1].rstrip('apm'))
        else:
            hour = int(re.match(r'\d+', time_str).group())
            minute = 0
        if 'pm' in time_str and hour != 12:
            hour += 12
        elif 'am' in time_str and hour == 12:
            hour = 0

        # Parse date (assume current or next year)
        try:
            now = datetime.now()
            month_day = datetime.strptime(date_str, "%b %d")
            year = now.year
            target = datetime(year, month_day.month, month_day.day, hour, minute)
            # If target is in the past, use next year
            if target < now:
                target = datetime(year + 1, month_day.month, month_day.day, hour, minute)
            data['week_reset'] = target.isoformat()
        except:
            pass

    return data

def fetch_usage_via_pty():
    """Fetch usage via PTY - runs 'claude /usage' directly"""
    try:
        import pty
        import select
        import time

        # Find claude executable
        claude_cmd = find_claude()
        if not claude_cmd:
            return {'error': 'Claude not found. Install Claude Code first.'}, ''

        # Create PTY
        master, slave = pty.openpty()

        # Run 'claude /usage' directly (not interactive mode)
        cmd = [claude_cmd, '/usage'] if ' ' not in claude_cmd else claude_cmd.split() + ['/usage']
        proc = subprocess.Popen(
            cmd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            preexec_fn=os.setsid,
            env={**os.environ, 'TERM': 'xterm-256color'}
        )

        os.close(slave)

        # Wait for usage data to load (fixed time)
        time.sleep(8)

        # Read all available output
        usage_output = b''
        while True:
            ready, _, _ = select.select([master], [], [], 0.3)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                    if chunk:
                        usage_output += chunk
                    else:
                        break
                except OSError:
                    break
            else:
                break

        # Send exit
        try:
            os.write(master, b'/exit\n')
            time.sleep(0.3)
        except:
            pass

        # Cleanup
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except:
            proc.kill()

        os.close(master)

        # Parse output
        text = usage_output.decode('utf-8', errors='ignore')
        # Remove ANSI codes
        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        text = re.sub(r'\x1b\][^\x07]*\x07', '', text)  # OSC sequences

        return parse_usage_output(text), text

    except Exception as e:
        return {'error': str(e)}, ''

def update_usage_file(new_data):
    """Merge new data into usage file"""
    current = {}
    try:
        if USAGE_FILE.exists():
            with open(USAGE_FILE) as f:
                current = json.load(f)
    except:
        pass

    # Update with new values (only if they exist)
    for key in ['session_percent', 'session_reset', 'session_reset_hour', 'week_percent', 'week_reset']:
        if key in new_data:
            current[key] = new_data[key]

    current['last_updated'] = datetime.now().isoformat()

    with open(USAGE_FILE, 'w') as f:
        json.dump(current, f, indent=2)

    return current

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching usage data...")

    data, raw = fetch_usage_via_pty()

    if 'error' in data:
        print(f"Error: {data['error']}")
        sys.exit(1)

    if not data:
        print("Could not parse usage data")
        print(f"Raw output (full):\n{raw}")
        sys.exit(1)

    updated = update_usage_file(data)

    print(f"Updated {USAGE_FILE}:")
    print(json.dumps(updated, indent=2))

if __name__ == '__main__':
    main()
