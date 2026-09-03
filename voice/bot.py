"""Pipecat full-duplex voice bot.

Pipeline:  WebRTC in -> Silero VAD -> Whisper STT -> NovaCare agent (backend HTTP)
           -> Kokoro TTS -> WebRTC out

The agent itself lives in the backend (one agent for chat + voice). This module
only does audio + transport and forwards transcripts.
"""
from __future__ import annotations

import logging

from config import config
from agent_client import AgentClient

log = logging.getLogger("novacare.voice.bot")

try:  # pipecat is heavy and API-versioned; degrade to PTT-only if unavailable
    from pipecat.frames.frames import (
        Frame,
        LLMFullResponseEndFrame,
        LLMFullResponseStartFrame,
        StartInterruptionFrame,
        TextFrame,
        TranscriptionFrame,
    )
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
    from pipecat.services.whisper.stt import WhisperSTTService
    from pipecat.services.kokoro.tts import KokoroTTSService
    from pipecat.transports.base_transport import TransportParams
    from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
    from pipecat.audio.vad.silero import SileroVADAnalyzer

    PIPECAT_AVAILABLE = True
except Exception as exc:  # noqa: BLE001
    log.warning("Pipecat not fully available (%s); full-duplex disabled, PTT still works", exc)
    PIPECAT_AVAILABLE = False
    FrameProcessor = object  # type: ignore


class NovaCareAgentProcessor(FrameProcessor):  # type: ignore[misc]
    """Turns final transcripts into agent replies, emitted as TextFrames for TTS."""

    def __init__(self, conversation_id: str, on_event=None) -> None:
        super().__init__()
        self._client = AgentClient()
        self._conversation_id = conversation_id
        self._on_event = on_event

    async def process_frame(self, frame, direction):  # type: ignore[override]
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame) and frame.text and frame.text.strip():
            user_text = frame.text.strip()
            if self._on_event:
                await self._on_event({"kind": "user_transcript", "text": user_text})
            await self.push_frame(StartInterruptionFrame())
            await self.push_frame(LLMFullResponseStartFrame())
            try:
                data = await self._client.send_message(self._conversation_id, user_text)
                reply = data.get("reply", "")
                pending = data.get("pending_action")
                if pending:
                    reply += " I've prepared that action — please confirm it on your screen."
            except Exception as e:  # noqa: BLE001
                log.exception("agent call failed")
                reply = "Sorry, I had trouble reaching the support system. Please try again."
            if self._on_event:
                await self._on_event({"kind": "ai_transcript", "text": reply})
            await self.push_frame(TextFrame(reply))
            await self.push_frame(LLMFullResponseEndFrame())
            return

        await self.push_frame(frame, direction)


async def run_bot(webrtc_connection, conversation_id: str, on_event=None) -> None:
    if not PIPECAT_AVAILABLE:
        raise RuntimeError("Pipecat is not available in this build")

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    stt = WhisperSTTService(model=config.whisper_model, device=config.whisper_device)
    tts = KokoroTTSService(voice=config.kokoro_voice, lang=config.kokoro_lang,
                           sample_rate=config.sample_rate)
    agent = NovaCareAgentProcessor(conversation_id, on_event=on_event)

    pipeline = Pipeline([
        transport.input(),
        stt,
        agent,
        tts,
        transport.output(),
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(allow_interruptions=True, audio_out_sample_rate=config.sample_rate),
    )

    @transport.event_handler("on_client_connected")
    async def _on_connected(_t, _client):  # noqa: ANN001
        if on_event:
            await on_event({"kind": "status", "text": "connected"})

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnected(_t, _client):  # noqa: ANN001
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)
    await runner.run(task)
