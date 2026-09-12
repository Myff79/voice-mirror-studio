# Voice Mirror Studio — guidance for coding assistants

## Purpose

Help a student run a short, local voice-agent workshop. Preserve the simple
browser experience. Do not turn this into a cloud deployment unless the student
explicitly asks for one and understands the credential implications.

## Architecture

- `workshop_ui.py` serves the local browser interface and starts/stops the agent.
- `agent.py` uses LiveKit for microphone transport, Deepgram transcription,
  Gemma responses, turn-taking, and interruptions.
- Gradium TTS uses the student's own API key and voice ID.
- `personality.txt` is the editable system prompt.
- `student-settings.env` contains private account credentials.
- `runtime-events.jsonl` contains the local conversation transcript.

## Safety rules

- Never print, commit, upload, or paste values from `student-settings.env`.
- Never add `student-settings.env`, `.env`, transcripts, or `.venv` to Git.
- Do not move student credentials into browser JavaScript or GitHub Pages.
- Do not replace the student's cloned voice ID without asking.
- Before any Git operation, verify ignored private files with `git status` and
  scan staged files for credentials.

## Setup checklist

1. Confirm `uv` is installed.
2. Run `uv sync` in the repository.
3. Start `workshop_ui.py` and open the local Studio page.
4. Let the student enter their own LiveKit project URL, API key, API secret,
   Gradium API key, and voice ID in the one-time setup panel.
5. Confirm both readiness labels are active without revealing secret values.
6. Start a short conversation and verify transcription, response, audio, and
   interruption handling.

## Troubleshooting order

1. Missing readiness label: check that all required settings exist, but report
   only which field is missing—never its value.
2. No transcription: check microphone permission and LiveKit connectivity.
3. Text but no voice: check the Gradium key, voice ownership, and voice ID.
4. No model response: check the LiveKit allowance and project credentials.
5. Agent exits: run the console locally and summarize the error without exposing
   credentials or raw authorization headers.

## Workshop constraints

Keep changes understandable for beginners and compatible with macOS. Prefer
clear labels and one-click actions over terminal-heavy instructions. The main
workshop path may use LiveKit Builder with preset voices; this repository is the
advanced path for custom or cloned Gradium voices.
