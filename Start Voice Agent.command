#!/bin/zsh
set -e

cd "${0:A:h}"

if ! command -v uv >/dev/null 2>&1; then
  echo "The uv tool is missing. Install it before starting the workshop app."
  read "?Press Return to close."
  exit 1
fi

echo "Starting your LiveKit agent with your private Gradium voice..."
uv sync
uv run python agent.py console
