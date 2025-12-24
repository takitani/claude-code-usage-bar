#!/usr/bin/env python3
"""
Claude Usage Updater - Background job to fetch /usage data

This script spawns Claude Code via PTY, runs /usage command,
parses the output, and updates ~/.claude-usage.json.

Run via cron every 10-15 minutes:
  */15 * * * * /path/to/update_usage.py >> ~/.claude-usage-update.log 2>&1

Note: Only works on Linux/macOS (requires PTY support).
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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
    """Parse /usage command output text into structured data"""
    data = {}

    # Try compact format first: 📊16% ⏱️20m | 📆13% ⏱️5d20h
    compact_session = re.search(r'📊(\d+)%', text)
    compact_week = re.search(r'📆(\d+)%', text)

    if compact_session:
        data['session_percent'] = int(compact_session.group(1))
    if compact_week:
        data['week_percent'] = int(compact_week.group(1))

    # If compact format found, return early
    if compact_session or compact_week:
        return data

    # Session percentage: look for "XX% used" after "Current session"
    session_match = re.search(
        r'Current session.*?(\d+)%\s*used',
        text, re.DOTALL | re.IGNORECASE
    )
    if session_match:
        data['session_percent'] = int(session_match.group(1))

    # Session reset time: "Resets XXpm" or "Resets XX:XXam/pm"
    session_reset = re.search(
        r'Current session.*?Resets?\s+(\d+(?::\d+)?(?:am|pm))',
        text, re.DOTALL | re.IGNORECASE
    )
    if session_reset:
        reset_time = session_reset.group(1).lower()
        # Parse to 24-hour format
        if ':' in reset_time:
            hour = int(reset_time.split(':')[0])
        else:
            hour = int(re.match(r'\d+', reset_time).group())

        if 'pm' in reset_time and hour != 12:
            hour += 12
        elif 'am' in reset_time and hour == 12:
            hour = 0

        data['session_reset_hour'] = hour

    # Week percentage: "XX% used" after "Current week"
    week_match = re.search(
        r'Current week.*?(\d+)%\s*used',
        text, re.DOTALL | re.IGNORECASE
    )
    if week_match:
        data['week_percent'] = int(week_match.group(1))

    # Week reset: "Resets Dec 30, 5pm" or similar formats
    week_reset = re.search(
        r'Current week.*?Resets?\s+([A-Za-z]+\s+\d+),?\s*(\d+(?::\d+)?(?:am|pm))',
        text, re.DOTALL | re.IGNORECASE
    )
    if week_reset:
        date_str = week_reset.group(1)  # "Dec 30"
        time_str = week_reset.group(2).lower()  # "5pm"

        # Parse time
        if ':' in time_str:
            parts = time_str.rstrip('apm').split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        else:
            hour = int(re.match(r'\d+', time_str).group())
            minute = 0

        if 'pm' in time_str and hour != 12:
            hour += 12
        elif 'am' in time_str and hour == 12:
            hour = 0

        # Parse date
        try:
            now = datetime.now()
            month_day = datetime.strptime(date_str, "%b %d")
            year = now.year
            target = datetime(year, month_day.month, month_day.day, hour, minute)

            # If target is in the past, assume next year
            if target < now:
                target = datetime(year + 1, month_day.month, month_day.day, hour, minute)

            data['week_reset'] = target.isoformat()
        except Exception:
            pass

    return data


def fetch_usage_via_pty():
    """Fetch usage data by spawning Claude Code in a PTY"""
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

        # Start Claude Code
        cmd = claude_cmd.split() if ' ' in claude_cmd else [claude_cmd]
        proc = subprocess.Popen(
            cmd,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            preexec_fn=os.setsid,
            env={**os.environ, 'TERM': 'xterm-256color'}
        )

        os.close(slave)

        output = b''
        start_time = time.time()
        timeout = 20

        # Wait for initial prompt
        time.sleep(3)

        # Drain initial output
        while True:
            ready, _, _ = select.select([master], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                    if chunk:
                        output += chunk
                    else:
                        break
                except OSError:
                    break
            else:
                break

        # Send /usage command
        os.write(master, b'/usage\n')
        time.sleep(1)

        # Read output until we have both session and week data
        usage_output = b''
        while time.time() - start_time < timeout:
            ready, _, _ = select.select([master], [], [], 0.5)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                    if chunk:
                        usage_output += chunk
                        text = usage_output.decode('utf-8', errors='ignore')

                        # Check if we got complete data (either format)
                        has_compact = '📊' in text and '📆' in text
                        has_full = ('Current session' in text and
                                   'Current week' in text and
                                   text.count('% used') >= 2)

                        if has_compact or has_full:
                            time.sleep(0.5)
                            try:
                                chunk = os.read(master, 4096)
                                usage_output += chunk
                            except OSError:
                                pass
                            break
                except OSError:
                    break

        # Exit Claude
        try:
            os.write(master, b'/exit\n')
            time.sleep(0.3)
        except OSError:
            pass

        # Cleanup
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()

        try:
            os.close(master)
        except OSError:
            pass

        # Clean and parse output
        text = usage_output.decode('utf-8', errors='ignore')
        # Remove ANSI escape codes
        text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
        text = re.sub(r'\x1b\][^\x07]*\x07', '', text)  # OSC sequences

        return parse_usage_output(text), text

    except ImportError:
        return {'error': 'PTY not available (Windows?)'}, ''
    except FileNotFoundError:
        return {'error': 'Claude Code not found. Is it installed?'}, ''
    except Exception as e:
        return {'error': str(e)}, ''


def update_usage_file(new_data):
    """Merge new data into the usage JSON file"""
    current = {}
    try:
        if USAGE_FILE.exists():
            with open(USAGE_FILE) as f:
                current = json.load(f)
    except Exception:
        pass

    # Update with new values
    for key in ['session_percent', 'session_reset_hour', 'week_percent', 'week_reset']:
        if key in new_data:
            current[key] = new_data[key]

    current['last_updated'] = datetime.now().isoformat()

    with open(USAGE_FILE, 'w') as f:
        json.dump(current, f, indent=2)

    return current


def main():
    """Main entry point"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Fetching Claude usage data...")

    data, raw = fetch_usage_via_pty()

    if 'error' in data:
        print(f"[{timestamp}] Error: {data['error']}")
        sys.exit(1)

    if not data:
        print(f"[{timestamp}] Could not parse usage data")
        if raw:
            print(f"[{timestamp}] Raw output preview: {raw[:300]}...")
        sys.exit(1)

    updated = update_usage_file(data)
    print(f"[{timestamp}] Updated {USAGE_FILE}")
    print(f"[{timestamp}] Session: {updated.get('session_percent', '?')}% | "
          f"Week: {updated.get('week_percent', '?')}%")


if __name__ == '__main__':
    main()
