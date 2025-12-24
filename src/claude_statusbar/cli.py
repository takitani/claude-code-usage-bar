#!/usr/bin/env python3
"""CLI entry point for claude-statusbar"""

import sys
import argparse
from . import __version__


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Claude Code Subscription Status Bar',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-statusbar          # Show current usage status
  claude-statusbar --update # Fetch fresh data from Claude /usage

Output format:
  🤖Op+T | 📊16% ⏱️2h30m | 📆13% ⏱️5d21h

  🤖Op+T     = Model (Opus) + Extended Thinking
  📊16%      = Session usage (16% of daily limit)
  ⏱️2h30m    = Time until session reset
  📆13%      = Weekly usage (13% of weekly limit)
  ⏱️5d21h    = Time until weekly reset

For subscription users (Pro/Team). Usage data is cached in ~/.claude-usage.json
and updated automatically by a background job (cron).
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '--update',
        action='store_true',
        help='Fetch fresh usage data from Claude (runs /usage via PTY)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )

    args = parser.parse_args()

    if sys.version_info < (3, 9):
        print("claude-statusbar requires Python 3.9+", file=sys.stderr)
        return 1

    try:
        if args.update:
            # Run the updater
            from .update_usage import main as update_main
            update_main()
            return 0

        if args.json:
            # JSON output
            import json
            from pathlib import Path
            from .statusbar import get_model_from_jsonl, format_model, load_usage_config

            cfg = load_usage_config()
            model, has_thinking = get_model_from_jsonl()

            output = {
                'model': model,
                'model_short': format_model(model, has_thinking),
                'has_thinking': has_thinking,
                'session_percent': cfg.get('session_percent'),
                'session_reset_hour': cfg.get('session_reset_hour'),
                'week_percent': cfg.get('week_percent'),
                'week_reset': cfg.get('week_reset'),
                'last_updated': cfg.get('last_updated'),
            }
            print(json.dumps(output, indent=2))
            return 0

        # Normal status bar output
        if args.no_color:
            sys.argv.append('--no-color')

        from .statusbar import main as statusbar_main
        statusbar_main()
        return 0

    except KeyboardInterrupt:
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
