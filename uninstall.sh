#!/bin/bash
# Claude Code Status Bar - Uninstaller
# Usage: curl -fsSL https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/uninstall.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Claude Code Status Bar - Uninstaller                    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Confirm uninstallation
read -p "This will remove claude-statusbar and its configuration. Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Uninstallation cancelled${NC}"
    exit 0
fi

echo ""

# Remove cron job
remove_cron() {
    echo -e "${BLUE}Removing cron job...${NC}"

    if crontab -l 2>/dev/null | grep -q "claude-usage-update"; then
        crontab -l 2>/dev/null | grep -v "claude-usage-update" | grep -v "claude-statusbar auto-update" | crontab -
        echo -e "${GREEN}✓${NC} Cron job removed"
    else
        echo -e "${GREEN}✓${NC} No cron job found"
    fi
}

# Remove Claude Code statusLine config
remove_claude_config() {
    echo -e "${BLUE}Removing Claude Code status bar config...${NC}"

    CLAUDE_SETTINGS="$HOME/.claude/settings.json"

    if [ -f "$CLAUDE_SETTINGS" ]; then
        python3 << 'EOF'
import json
from pathlib import Path

settings_file = Path.home() / '.claude' / 'settings.json'

try:
    with open(settings_file) as f:
        settings = json.load(f)

    if 'statusLine' in settings:
        del settings['statusLine']
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        print('Removed statusLine from settings')
    else:
        print('No statusLine config found')
except Exception as e:
    print(f'Could not update settings: {e}')
EOF
        echo -e "${GREEN}✓${NC} Claude Code config cleaned"
    else
        echo -e "${GREEN}✓${NC} No Claude Code settings found"
    fi
}

# Uninstall package
uninstall_package() {
    echo -e "${BLUE}Uninstalling claude-statusbar package...${NC}"

    # Try uv
    if command -v uv &> /dev/null; then
        if uv tool list 2>/dev/null | grep -q "claude-statusbar"; then
            uv tool uninstall claude-statusbar
            echo -e "${GREEN}✓${NC} Uninstalled with uv"
            return
        fi
    fi

    # Try pipx
    if command -v pipx &> /dev/null; then
        if pipx list 2>/dev/null | grep -q "claude-statusbar"; then
            pipx uninstall claude-statusbar
            echo -e "${GREEN}✓${NC} Uninstalled with pipx"
            return
        fi
    fi

    # Try pip
    if pip3 show claude-statusbar &>/dev/null 2>&1; then
        pip3 uninstall -y claude-statusbar
        echo -e "${GREEN}✓${NC} Uninstalled with pip"
        return
    fi

    echo -e "${GREEN}✓${NC} Package not found (already uninstalled?)"
}

# Remove config files
remove_files() {
    echo -e "${BLUE}Removing config files...${NC}"

    # Usage cache
    if [ -f "$HOME/.claude-usage.json" ]; then
        rm "$HOME/.claude-usage.json"
        echo -e "${GREEN}✓${NC} Removed ~/.claude-usage.json"
    fi

    # Update log
    if [ -f "$HOME/.claude-usage-update.log" ]; then
        rm "$HOME/.claude-usage-update.log"
        echo -e "${GREEN}✓${NC} Removed ~/.claude-usage-update.log"
    fi

    echo -e "${GREEN}✓${NC} Config files cleaned"
}

# Remove shell aliases
remove_aliases() {
    echo -e "${BLUE}Removing shell aliases...${NC}"

    CONFIG_FILES=(
        "$HOME/.bashrc"
        "$HOME/.zshrc"
    )

    for config_file in "${CONFIG_FILES[@]}"; do
        if [ -f "$config_file" ] && grep -q "claude-statusbar" "$config_file"; then
            # Remove claude-statusbar related lines
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' '/claude-statusbar/d' "$config_file"
                sed -i '' "/alias cs='claude-statusbar'/d" "$config_file"
                sed -i '' "/alias cstatus='claude-statusbar'/d" "$config_file"
            else
                sed -i '/claude-statusbar/d' "$config_file"
                sed -i "/alias cs='claude-statusbar'/d" "$config_file"
                sed -i "/alias cstatus='claude-statusbar'/d" "$config_file"
            fi
            echo -e "${GREEN}✓${NC} Cleaned $config_file"
        fi
    done
}

# Summary
show_summary() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Uninstallation Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Removed:"
    echo "  • claude-statusbar package"
    echo "  • Cron job (auto-update)"
    echo "  • Claude Code statusLine config"
    echo "  • Config files (~/.claude-usage.json)"
    echo ""
    echo "Restart Claude Code to apply changes."
    echo ""
}

# Main
remove_cron
remove_claude_config
uninstall_package
remove_files
remove_aliases
show_summary
