#!/bin/sh
set -eu
repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
command -v uv >/dev/null 2>&1 || { echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/' >&2; exit 1; }
command -v codex >/dev/null 2>&1 || { echo 'Codex CLI must be on PATH.' >&2; exit 1; }
uv sync --frozen --project "$repository_root/plugins/derbysoft-logs"
codex plugin marketplace add "$repository_root"
codex plugin add derbysoft-logs@derbysoft-logs
printf '%s\n' 'Installed. Open DerbySoft Logs plugin settings to configure environments.' 'Disable an older derbysoft-logs-local copy to avoid duplicate tools.'
