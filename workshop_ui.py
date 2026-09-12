import asyncio
import json
import os
import signal
import sys
import threading
import webbrowser
from pathlib import Path

from aiohttp import web


ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / "student-settings.env"
PERSONALITY_PATH = ROOT / "personality.txt"
EVENTS_PATH = ROOT / "runtime-events.jsonl"
INDEX_PATH = ROOT / "web" / "index.html"
SETTINGS_TEMPLATE_PATH = ROOT / "student-settings.example.env"


class Studio:
    def __init__(self) -> None:
        self.process: asyncio.subprocess.Process | None = None
        self.output_task: asyncio.Task | None = None
        self.last_error = ""

    @property
    def running(self) -> bool:
        return self.process is not None and self.process.returncode is None

    async def start(self) -> None:
        if self.running:
            return
        EVENTS_PATH.write_text("", encoding="utf-8")
        self.last_error = ""
        if getattr(sys, "frozen", False):
            agent_command = [str(ROOT / ("voice-agent.exe" if os.name == "nt" else "voice-agent")), "console"]
        else:
            agent_command = [sys.executable, "agent.py", "console"]
        self.process = await asyncio.create_subprocess_exec(
            *agent_command,
            cwd=ROOT,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        self.output_task = asyncio.create_task(self._capture_output())

    async def _capture_output(self) -> None:
        assert self.process and self.process.stdout
        recent: list[str] = []
        while line := await self.process.stdout.readline():
            clean = line.decode(errors="replace").strip()
            if clean:
                recent.append(clean)
                recent = recent[-12:]
        code = await self.process.wait()
        if code and recent:
            self.last_error = "The voice agent stopped unexpectedly. Check your account settings and try again."

    async def stop(self) -> None:
        if not self.running or not self.process:
            return
        self.process.send_signal(signal.SIGINT)
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5)
        except asyncio.TimeoutError:
            self.process.terminate()
            await self.process.wait()


studio = Studio()


def ensure_settings_file() -> None:
    if not SETTINGS_PATH.exists():
        SETTINGS_PATH.write_text(
            SETTINGS_TEMPLATE_PATH.read_text(encoding="utf-8"), encoding="utf-8"
        )


def read_settings() -> dict[str, str]:
    ensure_settings_file()
    values: dict[str, str] = {}
    for line in SETTINGS_PATH.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def write_setting(name: str, value: str) -> None:
    ensure_settings_file()
    lines = SETTINGS_PATH.read_text(encoding="utf-8").splitlines()
    prefix = f"{name}="
    updated = [prefix + value if line.startswith(prefix) else line for line in lines]
    SETTINGS_PATH.write_text("\n".join(updated) + "\n", encoding="utf-8")


def read_transcript() -> list[dict]:
    if not EVENTS_PATH.exists():
        return []
    messages = []
    for line in EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            messages.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return messages[-30:]


async def index(_: web.Request) -> web.FileResponse:
    return web.FileResponse(INDEX_PATH)


async def get_state(_: web.Request) -> web.Response:
    settings = read_settings()
    return web.json_response(
        {
            "running": studio.running,
            "error": studio.last_error,
            "voiceId": settings.get("GRADIUM_VOICE_ID", ""),
            "gradiumReady": bool(settings.get("GRADIUM_API_KEY")),
            "livekitReady": all(
                settings.get(key)
                for key in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")
            ),
            "personality": PERSONALITY_PATH.read_text(encoding="utf-8"),
            "transcript": read_transcript(),
        }
    )


async def save_setup(request: web.Request) -> web.Response:
    if studio.running:
        raise web.HTTPConflict(text="Stop the agent before changing its setup.")
    data = await request.json()
    required = {
        "GRADIUM_API_KEY": str(data.get("gradiumApiKey", "")).strip(),
        "GRADIUM_VOICE_ID": str(data.get("voiceId", "")).strip(),
        "LIVEKIT_URL": str(data.get("livekitUrl", "")).strip(),
        "LIVEKIT_API_KEY": str(data.get("livekitApiKey", "")).strip(),
        "LIVEKIT_API_SECRET": str(data.get("livekitApiSecret", "")).strip(),
    }
    if not all(required.values()):
        raise web.HTTPBadRequest(text="Complete all five account fields.")
    if not required["LIVEKIT_URL"].startswith(("wss://", "ws://")):
        raise web.HTTPBadRequest(text="The LiveKit URL must begin with wss://.")
    for name, value in required.items():
        write_setting(name, value)
    return web.json_response({"saved": True})


async def save_settings(request: web.Request) -> web.Response:
    if studio.running:
        raise web.HTTPConflict(text="Stop the agent before changing its settings.")
    data = await request.json()
    personality = str(data.get("personality", "")).strip()
    voice_id = str(data.get("voiceId", "")).strip()
    if not personality or not voice_id:
        raise web.HTTPBadRequest(text="Personality and voice ID are required.")
    PERSONALITY_PATH.write_text(personality + "\n", encoding="utf-8")
    write_setting("GRADIUM_VOICE_ID", voice_id)
    return web.json_response({"saved": True})


async def start_agent(request: web.Request) -> web.Response:
    await save_settings(request)
    settings = read_settings()
    if not settings.get("GRADIUM_API_KEY"):
        raise web.HTTPBadRequest(text="Add your private Gradium API key first.")
    await studio.start()
    return web.json_response({"running": True})


async def stop_agent(_: web.Request) -> web.Response:
    await studio.stop()
    return web.json_response({"running": False})


async def cleanup(_: web.Application) -> None:
    await studio.stop()


app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/api/state", get_state)
app.router.add_post("/api/setup", save_setup)
app.router.add_post("/api/settings", save_settings)
app.router.add_post("/api/start", start_agent)
app.router.add_post("/api/stop", stop_agent)
app.on_cleanup.append(cleanup)


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        threading.Timer(1.2, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    web.run_app(app, host="127.0.0.1", port=int(os.getenv("WORKSHOP_UI_PORT", "8765")))
