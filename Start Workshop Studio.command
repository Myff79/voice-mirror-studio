#!/bin/zsh
set -e

cd "${0:A:h}"
if ! command -v uv >/dev/null 2>&1; then
  open "https://docs.astral.sh/uv/getting-started/installation/"
  osascript -e 'display dialog "Voice Mirror Studio needs uv first. The installation page is now open. Install uv, then double-click this file again." buttons {"OK"} default button "OK" with icon note'
  exit 1
fi
uv sync
uv run python workshop_ui.py &
studio_pid=$!
sleep 1
open "http://127.0.0.1:8765"
wait $studio_pid
