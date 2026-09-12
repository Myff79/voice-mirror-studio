import os
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, inference
from livekit.plugins import gradium


APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
load_dotenv(APP_ROOT / "student-settings.env")


def load_personality() -> str:
    return (APP_ROOT / "personality.txt").read_text(encoding="utf-8").strip()


def record_conversation_item(event) -> None:
    item = event.item
    if getattr(item, "type", None) != "message":
        return
    text = getattr(item, "text_content", None)
    if not text:
        return
    payload = {"role": item.role, "text": text, "created_at": event.created_at}
    with (APP_ROOT / "runtime-events.jsonl").open("a", encoding="utf-8") as events_file:
        events_file.write(json.dumps(payload, ensure_ascii=False) + "\n")


class WorkshopAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=load_personality())


server = AgentServer()


@server.rtc_session(agent_name="my-gradium-voice")
async def workshop_session(ctx: agents.JobContext) -> None:
    voice_id = os.environ["GRADIUM_VOICE_ID"]

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="google/gemma-4-31b-it"),
        tts=gradium.TTS(voice_id=voice_id),
    )
    session.on("conversation_item_added", record_conversation_item)

    await session.start(room=ctx.room, agent=WorkshopAgent())
    await session.generate_reply(
        instructions="Greet the student and explain that you are speaking in their chosen voice."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
