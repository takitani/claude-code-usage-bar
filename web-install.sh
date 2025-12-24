#!/bin/bash
# Claude Code Status Bar - Web Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/web-install.sh | bash

set -e

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
echo -e "${CYAN}║${NC}  ${BOLD}Claude Code Status Bar${NC} - Subscription Usage Monitor     ${CYAN}║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Shows: ${GREEN}🤖Op+T${NC} | ${YELLOW}📊16%${NC} ⏱️2h | ${YELLOW}📆13%${NC} ⏱️5d"
echo -e "       Model  │ Session usage │ Weekly usage"
echo ""

# Check OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    echo -e "${RED}Windows detected. Please use the PowerShell installer instead:${NC}"
    echo ""
    echo "  irm https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/install.ps1 | iex"
    echo ""
    exit 1
fi

# Check Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
        return 0
    else
        echo -e "${RED}✗ Python 3 is required but not installed${NC}"
        echo "  Please install Python 3.9+ from https://python.org"
        exit 1
    fi
}

# Check Claude Code
check_claude() {
    if command -v claude &> /dev/null; then
        echo -e "${GREEN}✓${NC} Claude Code found"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Claude Code not found in PATH"
        echo "  Auto-update won't work until Claude Code is installed"
        return 1
    fi
}

# Detect/install package manager
install_package() {
    echo ""
    echo -e "${BLUE}Installing claude-statusbar...${NC}"

    if command -v uv &> /dev/null; then
        echo "Using uv..."
        uv tool uninstall claude-statusbar 2>/dev/null || true
        uv tool install claude-statusbar
    elif command -v pipx &> /dev/null; then
        echo "Using pipx..."
        pipx uninstall claude-statusbar 2>/dev/null || true
        pipx install claude-statusbar
    elif command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
        echo "Using pip..."
        if command -v pip3 &> /dev/null; then
            pip3 install --user --upgrade claude-statusbar
        else
            pip install --user --upgrade claude-statusbar
        fi
        # Ensure ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            export PATH="$HOME/.local/bin:$PATH"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc 2>/dev/null || true
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
        fi
    else
        echo -e "${YELLOW}No package manager found. Installing uv first...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
        uv tool install claude-statusbar
    fi

    echo -e "${GREEN}✓${NC} claude-statusbar installed"
}

# Configure Claude Code settings
configure_claude() {
    echo ""
    echo -e "${BLUE}Configuring Claude Code status bar...${NC}"

    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
    STATUSBAR_CMD=$(which claude-statusbar 2>/dev/null || echo "claude-statusbar")

    mkdir -p "$HOME/.claude"

    # Backup existing settings
    if [ -f "$CLAUDE_SETTINGS" ]; then
        cp "$CLAUDE_SETTINGS" "$CLAUDE_SETTINGS.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # Update or create settings
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

# Add statusLine configuration
settings['statusLine'] = {
    'type': 'command',
    'command': '$STATUSBAR_CMD',
    'padding': 0
}

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print('Settings updated')
EOF

    echo -e "${GREEN}✓${NC} Claude Code settings configured"
}

# Setup cron job for auto-updates
setup_cron() {
    echo ""
    echo -e "${BLUE}Setting up automatic usage updates...${NC}"

    # Get the update command path
    UPDATE_CMD=$(which claude-usage-update 2>/dev/null || echo "")

    if [ -z "$UPDATE_CMD" ]; then
        echo -e "${YELLOW}⚠${NC} claude-usage-update not found, skipping cron setup"
        echo "  You can update manually: claude-statusbar --update"
        return
    fi

    # Create log file
    LOG_FILE="$HOME/.claude-usage-update.log"
    touch "$LOG_FILE"

    # Add cron job (every 15 minutes)
    CRON_JOB="*/15 * * * * $UPDATE_CMD >> $LOG_FILE 2>&1"
    CRON_MARKER="# claude-statusbar auto-update"

    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "claude-usage-update"; then
        echo -e "${GREEN}✓${NC} Cron job already exists"
    else
        # Add new cron job
        (crontab -l 2>/dev/null; echo "$CRON_MARKER"; echo "$CRON_JOB") | crontab -
        echo -e "${GREEN}✓${NC} Cron job added (runs every 15 minutes)"
    fi

    echo -e "   Log file: ${DIM}$LOG_FILE${NC}"
}

# Create initial usage file
create_initial_config() {
    USAGE_FILE="$HOME/.claude-usage.json"

    if [ ! -f "$USAGE_FILE" ]; then
        echo '{"session_percent": null, "week_percent": null}' > "$USAGE_FILE"
        echo -e "${GREEN}✓${NC} Created initial config file"
    fi
}

# Test installation
test_installation() {
    echo ""
    echo -e "${BLUE}Testing installation...${NC}"

    if OUTPUT=$(claude-statusbar 2>&1); then
        echo -e "${GREEN}✓${NC} Status bar working!"
        echo ""
        echo -e "   Output: $OUTPUT"
    else
        echo -e "${YELLOW}⚠${NC} Status bar test returned: $OUTPUT"
    fi
}

# Show summary
show_summary() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Installation Complete! 🎉${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BOLD}How it works:${NC}"
    echo ""
    echo "  1. A background job runs every 15 minutes"
    echo "  2. It fetches your usage data from Claude's /usage command"
    echo "  3. The status bar reads from cached data (instant, no delay)"
    echo ""
    echo -e "${BOLD}Commands:${NC}"
    echo ""
    echo "  claude-statusbar          Show current status"
    echo "  claude-statusbar --update Fetch fresh usage data now"
    echo "  claude-statusbar --json   Output in JSON format"
    echo ""
    echo -e "${BOLD}First run:${NC}"
    echo ""
    echo "  Run this to fetch initial data:"
    echo -e "  ${CYAN}claude-statusbar --update${NC}"
    echo ""
    echo "  Or wait for the cron job to run (within 15 minutes)"
    echo ""
    echo -e "${BOLD}Restart Claude Code to see the status bar!${NC}"
    echo ""
}

# Main
main() {
    check_python
    check_claude || true
    install_package
    configure_claude
    create_initial_config
    setup_cron
    test_installation
    show_summary
}

main "$@"
