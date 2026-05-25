import asyncio
import logging
from app.ai.voice.events.event import Event
from app.ai.voice.realtime.timing_controller import TimingController

logger = logging.getLogger("audio_subscriber")

class AudioSubscriber:
    def __init__(self, timing_controller: TimingController = None):
        self.agent = None
        self.timing_controller = timing_controller or TimingController()

    def set_agent(self, agent) -> None:
        """Sets the active VoiceAgent reference."""
        self.agent = agent

    async def on_response_generated(self, event: Event) -> None:
        """Listens for generated responses and triggers TTS/audio stream playback on the VoiceAgent."""
        if not self.agent:
            logger.warning("audio_subscriber | voice agent is not registered yet")
            return
            
        clean_text = event.payload.get("clean_text")
        speaker_name = event.payload.get("speaker_name")
        voice_name = event.payload.get("voice_name")
        raw_text = event.payload.get("raw_text")

        # 1. Calculate and execute natural pacing delay (Step 7G: TimingController)
        decision = event.metadata.get("decision")
        signals = getattr(self.agent.state, "behavioral_signals", None)
        
        if decision:
            delay_sec = self.timing_controller.calculate_response_delay(decision, signals)
            logger.info("audio_subscriber | introducing natural thoughtful delay of %.2fs", delay_sec)
            await asyncio.sleep(delay_sec)

        logger.info("audio_subscriber | response received -> playing agent audio via VoiceAgent")
        
        # 2. Trigger actual speech playback on the VoiceAgent
        await self.agent.speak(
            text=clean_text,
            speaker_name=speaker_name,
            voice_name=voice_name,
            raw_text=raw_text,
        )
