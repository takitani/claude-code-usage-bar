#!/bin/bash
# Claude Code Status Bar - Local Installer
# For local development/testing. For web install, use:
# curl -fsSL https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/web-install.sh | bash

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}  ${BOLD}Claude Code Status Bar${NC} - Local Install                   ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python 3 found"

# Install from local source
echo ""
echo -e "${BLUE}Installing from local source...${NC}"

if command -v uv &> /dev/null; then
    echo "Using uv..."
    uv tool uninstall claude-statusbar 2>/dev/null || true
    uv tool install "$SCRIPT_DIR"
elif command -v pipx &> /dev/null; then
    echo "Using pipx..."
    pipx uninstall claude-statusbar 2>/dev/null || true
    pipx install "$SCRIPT_DIR"
else
    echo "Using pip..."
    pip3 install --user -e "$SCRIPT_DIR"
fi

echo -e "${GREEN}✓${NC} Installed"

# Configure Claude Code
echo ""
echo -e "${BLUE}Configuring Claude Code...${NC}"

CLAUDE_SETTINGS="$HOME/.claude/settings.json"
STATUSBAR_CMD=$(which claude-statusbar 2>/dev/null || echo "claude-statusbar")

mkdir -p "$HOME/.claude"

python3 << EOF
import json
from pathlib import Path

settings_file = Path.home() / '.claude' / 'settings.json'
settings = {}

try:
    if settings_file.exists():
        with open(settings_file) as f:
            settings = json.load(f)
except:
    pass

settings['statusLine'] = {
    'type': 'command',
    'command': '$STATUSBAR_CMD',
    'padding': 0
}

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
EOF

echo -e "${GREEN}✓${NC} Claude Code configured"

# Setup cron
echo ""
echo -e "${BLUE}Setting up cron job...${NC}"

UPDATE_CMD=$(which claude-usage-update 2>/dev/null || echo "")
if [ -n "$UPDATE_CMD" ]; then
    if ! crontab -l 2>/dev/null | grep -q "claude-usage-update"; then
        (crontab -l 2>/dev/null; echo "# claude-statusbar auto-update"; echo "*/15 * * * * $UPDATE_CMD >> $HOME/.claude-usage-update.log 2>&1") | crontab -
        echo -e "${GREEN}✓${NC} Cron job added"
    else
        echo -e "${GREEN}✓${NC} Cron job already exists"
    fi
else
    echo -e "${YELLOW}⚠${NC} Update command not found, skipping cron"
fi

# Create initial config
if [ ! -f "$HOME/.claude-usage.json" ]; then
    echo '{"session_percent": null, "week_percent": null}' > "$HOME/.claude-usage.json"
fi

# Test
echo ""
echo -e "${BLUE}Testing...${NC}"
OUTPUT=$(claude-statusbar 2>&1 || echo "?")
echo -e "${GREEN}✓${NC} Output: $OUTPUT"

# Done
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Run 'claude-statusbar --update' to fetch initial data"
echo "Restart Claude Code to see the status bar!"
echo ""
