# Claude Code Status Bar - Windows Installer
# Usage: irm https://raw.githubusercontent.com/takitani/claude-code-usage-bar/master/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Claude Code Status Bar - Subscription Usage Monitor     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "Shows: " -NoNewline
Write-Host "🤖Op+T" -ForegroundColor Green -NoNewline
Write-Host " | " -NoNewline
Write-Host "📊16%" -ForegroundColor Yellow -NoNewline
Write-Host " ⏱️2h | " -NoNewline
Write-Host "📆13%" -ForegroundColor Yellow -NoNewline
Write-Host " ⏱️5d"
Write-Host "       Model  │ Session usage │ Weekly usage"
Write-Host ""

# Check Python
function Test-Python {
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python 3\.") {
            Write-Host "✓ $pythonVersion found" -ForegroundColor Green
            return $true
        }
    } catch {}

    try {
        $pythonVersion = & python3 --version 2>&1
        if ($pythonVersion -match "Python 3\.") {
            Write-Host "✓ $pythonVersion found" -ForegroundColor Green
            return $true
        }
    } catch {}

    Write-Host "✗ Python 3 is required but not installed" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ from https://python.org"
    exit 1
}

# Check Claude Code
function Test-Claude {
    try {
        $null = Get-Command claude -ErrorAction Stop
        Write-Host "✓ Claude Code found" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "⚠ Claude Code not found in PATH" -ForegroundColor Yellow
        Write-Host "  Install Claude Code first to use the status bar"
        return $false
    }
}

# Install package
function Install-Package {
    Write-Host ""
    Write-Host "Installing claude-statusbar..." -ForegroundColor Blue

    # Check for uv
    try {
        $null = Get-Command uv -ErrorAction Stop
        Write-Host "Using uv..."
        & uv tool uninstall claude-statusbar 2>$null
        & uv tool install claude-statusbar
        Write-Host "✓ claude-statusbar installed" -ForegroundColor Green
        return
    } catch {}

    # Check for pipx
    try {
        $null = Get-Command pipx -ErrorAction Stop
        Write-Host "Using pipx..."
        & pipx uninstall claude-statusbar 2>$null
        & pipx install claude-statusbar
        Write-Host "✓ claude-statusbar installed" -ForegroundColor Green
        return
    } catch {}

    # Use pip
    Write-Host "Using pip..."
    try {
        & pip install --user --upgrade claude-statusbar
        Write-Host "✓ claude-statusbar installed" -ForegroundColor Green
    } catch {
        & python -m pip install --user --upgrade claude-statusbar
        Write-Host "✓ claude-statusbar installed" -ForegroundColor Green
    }
}

# Configure Claude Code settings
function Configure-Claude {
    Write-Host ""
    Write-Host "Configuring Claude Code status bar..." -ForegroundColor Blue

    $claudeDir = Join-Path $env:USERPROFILE ".claude"
    $settingsFile = Join-Path $claudeDir "settings.json"

    # Create directory
    if (-not (Test-Path $claudeDir)) {
        New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
    }

    # Backup existing settings
    if (Test-Path $settingsFile) {
        $backupFile = "$settingsFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $settingsFile $backupFile
    }

    # Find claude-statusbar command
    $statusbarCmd = "claude-statusbar"
    try {
        $statusbarPath = (Get-Command claude-statusbar -ErrorAction Stop).Source
        $statusbarCmd = $statusbarPath
    } catch {}

    # Update settings
    $settings = @{}
    if (Test-Path $settingsFile) {
        try {
            $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json -AsHashtable
        } catch {}
    }

    $settings["statusLine"] = @{
        "type" = "command"
        "command" = $statusbarCmd
        "padding" = 0
    }

    $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8

    Write-Host "✓ Claude Code settings configured" -ForegroundColor Green
}

# Create initial config
function Initialize-Config {
    $usageFile = Join-Path $env:USERPROFILE ".claude-usage.json"

    if (-not (Test-Path $usageFile)) {
        '{"session_percent": null, "week_percent": null}' | Set-Content $usageFile -Encoding UTF8
        Write-Host "✓ Created initial config file" -ForegroundColor Green
    }
}

# Test installation
function Test-Installation {
    Write-Host ""
    Write-Host "Testing installation..." -ForegroundColor Blue

    try {
        $output = & claude-statusbar 2>&1
        Write-Host "✓ Status bar working!" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Output: $output"
    } catch {
        Write-Host "⚠ Status bar test failed: $_" -ForegroundColor Yellow
    }
}

# Show summary
function Show-Summary {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  Installation Complete! 🎉" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note for Windows users:" -ForegroundColor White
    Write-Host ""
    Write-Host "  Auto-update is not available on Windows (requires PTY)."
    Write-Host "  You can update usage data manually:"
    Write-Host ""
    Write-Host "    claude-statusbar --update" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Or set up a scheduled task to run it periodically."
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host ""
    Write-Host "  claude-statusbar          Show current status"
    Write-Host "  claude-statusbar --update Fetch fresh usage data"
    Write-Host "  claude-statusbar --json   Output in JSON format"
    Write-Host ""
    Write-Host "Restart Claude Code to see the status bar!" -ForegroundColor White
    Write-Host ""
}

# Main
Test-Python
Test-Claude
Install-Package
Configure-Claude
Initialize-Config
Test-Installation
Show-Summary
