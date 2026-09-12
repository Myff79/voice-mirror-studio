# Voice Mirror Studio

Voice Mirror Studio is a small workshop interface for building a conversational
voice character. LiveKit handles the microphone, transcription, language model,
turn-taking, and interruptions. Gradium speaks the responses using a voice from
the student's own account, including a designed or cloned voice.

Private keys and conversation transcripts are deliberately excluded from Git.

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Download or clone this repository.
3. Copy `student-settings.example.env` to `student-settings.env`.
4. Add your Gradium API key and voice ID.
5. Add your LiveKit project URL, API key, and API secret.
6. On macOS, double-click `Start Workshop Studio.command`.
7. Open `http://127.0.0.1:8765` if the page does not open automatically.

You can also start it from Terminal:

```bash
uv sync
uv run python workshop_ui.py
```

## Workshop interface

The local browser page lets students edit the character personality, select a
Gradium voice ID, start or stop the conversation, and read the transcript. The
API keys remain only in `student-settings.env` on the student's computer.

## Change the personality

Edit the personality directly in the browser interface, or change
`personality.txt` before starting the voice agent. No Python editing is required.

The LiveKit credentials pay for Deepgram transcription and the Gemma language
model through the student's LiveKit free allowance. Gradium text-to-speech uses
the student's separate Gradium allowance.

## Important

This is a local application, not a GitHub Pages site. GitHub distributes the
workshop kit; each student's computer runs it so their credentials stay private.
