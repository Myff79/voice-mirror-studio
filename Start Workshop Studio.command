#!/bin/zsh
set -e

cd "${0:A:h}"
uv sync
uv run python workshop_ui.py
