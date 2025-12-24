# Claude Code Status Bar

🔋 Status bar for Claude Code subscription usage - shows model, session/weekly limits and reset times.

![Claude Code Status Bar](https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/img.png)

## What it shows

```
🤖Op+T | 📊16% ⏱️2h30m | 📆13% ⏱️5d21h
```

| Icon | Meaning |
|------|---------|
| 🤖Op+T | Model (Opus) + Extended Thinking |
| 📊16% | Session usage (16% of daily limit) |
| ⏱️2h30m | Time until session reset |
| 📆13% | Weekly usage (13% of weekly limit) |
| ⏱️5d21h | Time until weekly reset |

**Color coding:** 🟢 <50% | 🟡 50-80% | 🔴 >80%

## ✨ One-Line Install

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/web-install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/install.ps1 | iex
```

This automatically:
- ✅ Installs the `claude-statusbar` package
- ✅ Configures Claude Code status bar settings
- ✅ Sets up a cron job to update usage every 15 minutes (Linux/macOS)
- ✅ Creates initial config files

> 💡 **After installation:** Restart Claude Code to see the status bar!

## 📦 Alternative Install Methods

```bash
# PyPI
pip install claude-statusbar

# uv (recommended - fast)
uv tool install claude-statusbar

# pipx (isolated)
pipx install claude-statusbar
```

Then configure manually (see [Manual Configuration](#manual-configuration)).

## 🚀 Usage

```bash
# Show status (reads from cache - instant)
claude-statusbar

# Fetch fresh data from Claude /usage
claude-statusbar --update

# JSON output for scripts
claude-statusbar --json
```

## ⚙️ How it works

1. **Background job** runs every 15 minutes (cron on Linux/macOS)
2. Spawns Claude Code, runs `/usage` command, parses the output
3. Saves data to `~/.claude-usage.json`
4. Status bar reads from cache (instant, no delay)

The usage data comes from the same `/usage` command you can run inside Claude Code.

## 🔧 Manual Configuration

If you installed manually, add this to `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "claude-statusbar",
    "padding": 0
  }
}
```

To set up the auto-update cron job:

```bash
# Add to crontab (runs every 15 minutes)
(crontab -l 2>/dev/null; echo "*/15 * * * * claude-usage-update >> ~/.claude-usage-update.log 2>&1") | crontab -
```

## 📂 Files

| File | Purpose |
|------|---------|
| `~/.claude-usage.json` | Cached usage data |
| `~/.claude/settings.json` | Claude Code settings |
| `~/.claude-usage-update.log` | Update job logs |

## 🪟 Windows Notes

Windows doesn't support PTY (pseudo-terminal), so auto-update doesn't work. You can:

1. **Manual update**: Run `claude-statusbar --update` periodically
2. **Scheduled task**: Set up a Windows Task Scheduler job

## 🔄 Upgrading

```bash
# Re-run installer
curl -fsSL https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/web-install.sh | bash

# Or via package manager
pip install --upgrade claude-statusbar
uv tool upgrade claude-statusbar
pipx upgrade claude-statusbar
```

## 🗑️ Uninstall

```bash
# Linux/macOS
curl -fsSL https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/uninstall.sh | bash

# Or manually
pip uninstall claude-statusbar
# Remove cron job
crontab -l | grep -v "claude-usage-update" | crontab -
# Remove config files
rm ~/.claude-usage.json ~/.claude-usage-update.log
```

## 💖 Support

If you find this tool helpful:
- ⭐ Star this repo
- 🐛 Report issues

## 📄 License

MIT

---

*For Claude Code subscription users (Pro/Team). Shows the same data as the `/usage` command.*
