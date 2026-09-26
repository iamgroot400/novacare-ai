"""Pipecat full-duplex voice bot.

Pipeline:  WebRTC in -> Silero VAD -> Groq STT -> NovaCare agent (backend HTTP)
           -> Groq/Piper TTS -> WebRTC out

The agent itself lives in the backend (one agent for chat + voice). This module
only does audio + transport and forwards transcripts.
"""
from __future__ import annotations

import asyncio
import logging

from config import config
from agent_client import voice_turn

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
    from pipecat.frames.frames import TTSAudioRawFrame, TTSStartedFrame, TTSStoppedFrame
    from pipecat.services.ai_services import SegmentedSTTService, TTSService
    from pipecat.utils.time import time_now_iso8601
    from pipecat.transports.base_transport import TransportParams
    from pipecat.transports.network.small_webrtc import SmallWebRTCTransport
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.audio.vad.vad_analyzer import VADParams

    PIPECAT_AVAILABLE = True
except Exception as exc:  # noqa: BLE001
    log.warning("Pipecat not fully available (%s); full-duplex disabled, PTT still works", exc)
    PIPECAT_AVAILABLE = False
    FrameProcessor = SegmentedSTTService = TTSService = object  # type: ignore


class GroqSTT(SegmentedSTTService):  # type: ignore[misc]
    """VAD-segmented utterance (WAV bytes) -> Groq Whisper -> TranscriptionFrame."""

    async def run_stt(self, audio: bytes):
        import stt

        text = await asyncio.to_thread(stt.transcribe_file, audio)
        if text:
            yield TranscriptionFrame(text, "user", time_now_iso8601())


class GroqPiperTTS(TTSService):  # type: ignore[misc]
    """Sentence -> Groq TTS (Piper fallback, see tts.py) -> 24 kHz PCM frames."""

    async def run_tts(self, text: str):
        import numpy as np

        import tts

        yield TTSStartedFrame()
        audio = await asyncio.to_thread(tts.synthesize, text)
        audio = tts.resample(audio, config.sample_rate, self.sample_rate)
        pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        yield TTSAudioRawFrame(pcm, self.sample_rate, 1)
        yield TTSStoppedFrame()


class NovaCareAgentProcessor(FrameProcessor):  # type: ignore[misc]
    """Turns final transcripts into agent replies, emitted as TextFrames for TTS."""

    def __init__(self, conversation_id: str, on_event=None) -> None:
        super().__init__()
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
            import tts

            lang = "ne" if tts.is_nepali(user_text) else "en"
            turn_task = asyncio.create_task(voice_turn(self._conversation_id, user_text))
            done, _ = await asyncio.wait({turn_task}, timeout=config.filler_after_secs)
            if not done:  # slow turn = tools running (plus free-tier rate limits): don't leave dead air
                await self.push_frame(TextFrame(FILLER[lang]))
            try:
                turn = await turn_task
                reply, spoken = turn["reply"], turn["spoken"]
            except Exception:  # noqa: BLE001
                log.exception("agent call failed")
                reply = spoken = AGENT_DOWN[lang]
            if self._on_event:
                await self._on_event({"kind": "ai_transcript", "text": reply})
            # One frame per sentence: TTS voices sentence 1 while the rest queue, so speech starts sooner.
            for sentence in tts.sentences(spoken):
                await self.push_frame(TextFrame(sentence))
            await self.push_frame(LLMFullResponseEndFrame())
            return

        await self.push_frame(frame, direction)


FILLER = {"ne": "एकछिन पर्खनुहोला, म हेर्दैछु।", "en": "One moment, let me check that."}
AGENT_DOWN = {
    "ne": "माफ गर्नुहोला, अहिले सिस्टममा समस्या आयो। एकछिनपछि फेरि भन्नुहोला।",
    "en": "Sorry, I had trouble reaching the support system. Please try again.",
}

PHONE_GREETING = (
    "नमस्ते! म NovaStore को NovaCare सहयोग सेवाबाट बोल्दैछु। तपाईंलाई के सहयोग चाहियो? "
    "Hello, this is NovaCare support from NovaStore. How can I help you today?"
)


def warm_tts() -> None:
    """Pre-synthesize every fixed phrase so fillers and prompts start instantly."""
    import tts
    from agent_client import _T

    fixed = [*FILLER.values(), *AGENT_DOWN.values(), PHONE_GREETING,
             *(p for lang in _T.values() for p in lang.values() if "{" not in p)]
    tts.warm([s for p in fixed for s in tts.sentences(p)])


def _vad():
    return SileroVADAnalyzer(params=VADParams(stop_secs=config.vad_stop_secs))


async def _run(transport, conversation_id: str, out_rate: int, in_rate: int, on_event=None,
               greeting: str | None = None) -> None:
    pipeline = Pipeline([
        transport.input(),
        GroqSTT(),
        NovaCareAgentProcessor(conversation_id, on_event=on_event),
        GroqPiperTTS(aggregate_sentences=False),  # sample rate comes from PipelineParams
        transport.output(),
    ])
    task = PipelineTask(pipeline, params=PipelineParams(
        allow_interruptions=True, audio_in_sample_rate=in_rate, audio_out_sample_rate=out_rate))

    @transport.event_handler("on_client_connected")
    async def _on_connected(_t, _client):  # noqa: ANN001
        if on_event:
            await on_event({"kind": "status", "text": "connected"})
        if greeting:
            import tts

            await task.queue_frames([TextFrame(s) for s in tts.sentences(greeting)])

    @transport.event_handler("on_client_disconnected")
    async def _on_disconnected(_t, _client):  # noqa: ANN001
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)


async def run_bot(webrtc_connection, conversation_id: str, on_event=None) -> None:
    """Browser call over WebRTC."""
    if not PIPECAT_AVAILABLE:
        raise RuntimeError("Pipecat is not available in this build")
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        # vad_enabled + passthrough: without both, VAD never runs / STT never receives audio.
        params=TransportParams(audio_in_enabled=True, audio_out_enabled=True, vad_enabled=True,
                               vad_audio_passthrough=True, vad_analyzer=_vad()),
    )
    await _run(transport, conversation_id, config.sample_rate, 16000, on_event)


async def run_phone_bot(websocket, stream_sid: str, conversation_id: str) -> None:
    """Phone call: Twilio Media Stream (8 kHz mu-law) over a FastAPI websocket."""
    if not PIPECAT_AVAILABLE:
        raise RuntimeError("Pipecat is not available in this build")
    from pipecat.serializers.twilio import TwilioFrameSerializer
    from pipecat.transports.network.fastapi_websocket import (
        FastAPIWebsocketParams,
        FastAPIWebsocketTransport,
    )

    transport = FastAPIWebsocketTransport(websocket=websocket, params=FastAPIWebsocketParams(
        audio_in_enabled=True, audio_out_enabled=True, add_wav_header=False,
        vad_enabled=True, vad_audio_passthrough=True, vad_analyzer=_vad(),
        serializer=TwilioFrameSerializer(stream_sid), session_timeout=15 * 60,
    ))
    await _run(transport, conversation_id, 8000, 8000, greeting=PHONE_GREETING)
