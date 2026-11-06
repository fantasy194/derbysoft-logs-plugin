[CmdletBinding()]
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $repositoryRoot 'plugins\derbysoft-logs'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/ . Then run this installer again.'
}
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw 'Codex CLI was not found on PATH. Install/enable the Codex command-line tool, then retry.'
}
uv sync --frozen --project $pluginRoot
if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed.' }
if ($CheckOnly) { Write-Output 'Runtime ready. Plugin settings were not changed.'; exit 0 }
codex plugin marketplace add $repositoryRoot
if ($LASTEXITCODE -ne 0) { throw 'Marketplace registration failed.' }
codex plugin add 'derbysoft-logs@derbysoft-logs'
if ($LASTEXITCODE -ne 0) { throw 'Plugin installation failed.' }
Write-Output 'Installed. Open DerbySoft Logs in the plugin settings to add environments and connections.'
Write-Output 'If the old derbysoft-logs-local plugin is enabled, disable that copy to avoid duplicate tools.'
