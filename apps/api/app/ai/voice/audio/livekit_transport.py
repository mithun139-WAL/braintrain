import json
import logging
import time
from typing import Callable
from jose import jwt
from livekit import rtc

logger = logging.getLogger("livekit_transport")

class LiveKitTransport:
    def __init__(self, room_name: str, livekit_url: str, api_key: str, api_secret: str):
        """
        Manages LiveKit room connections, track publication, and data channels.
        
        :param room_name: Name of the LiveKit room to connect to.
        :param livekit_url: LiveKit URL.
        :param api_key: LiveKit API key.
        :param api_secret: LiveKit API secret.
        """
        self.room_name = room_name
        self.livekit_url = livekit_url
        self.api_key = api_key
        self.api_secret = api_secret
        
        self.room = rtc.Room()
        self.audio_source = rtc.AudioSource(sample_rate=24000, num_channels=1)
        self.audio_track = rtc.LocalAudioTrack.create_audio_track(
            "agent-voice", self.audio_source
        )

    def generate_token(self, identity: str, expiration_seconds: int = 3600) -> str:
        """Mints a LiveKit JWT token for the agent's identity."""
        current_time = int(time.time())
        payload = {
            "iss": self.api_key,
            "sub": identity,
            "nbf": current_time - 60,
            "exp": current_time + expiration_seconds,
            "video": {
                "roomJoin": True,
                "room": self.room_name,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            },
        }
        return jwt.encode(payload, self.api_secret, algorithm="HS256")

    async def connect(self, agent_token: str) -> None:
        """Connects to the LiveKit room."""
        await self.room.connect(self.livekit_url, agent_token)

    async def publish_audio(self) -> None:
        """Publishes the local audio track to the room."""
        publish_options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_MICROPHONE
        )
        await self.room.local_participant.publish_track(
            self.audio_track, publish_options
        )

    async def broadcast_transcript(self, speaker: str, text: str) -> None:
        """
        Broadcasts transcript JSON to the frontend via LiveKit Data Channel.
        Measures broadcast latency.
        """
        start_time = time.perf_counter()
        payload = json.dumps({"speaker": speaker, "text": text}).encode("utf-8")
        await self.room.local_participant.publish_data(payload)
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.debug("transcript_broadcast_completed | speaker: %s | latency: %.2fms", speaker, latency_ms)

    def register_handlers(
        self,
        on_track_subscribed: Callable[[rtc.RemoteTrack, rtc.RemoteTrackPublication, rtc.RemoteParticipant], None],
        on_participant_disconnected: Callable[[rtc.RemoteParticipant], None]
    ) -> None:
        """Registers callback handlers for room events."""
        @self.room.on("track_subscribed")
        def _on_track_subscribed(track, publication, participant):
            on_track_subscribed(track, publication, participant)

        @self.room.on("participant_disconnected")
        def _on_participant_disconnected(participant):
            on_participant_disconnected(participant)

    def get_remote_participants(self) -> dict:
        """Returns the dictionary of remote participants connected to the room."""
        return self.room.remote_participants

    async def disconnect(self) -> None:
        """Disconnects cleanly from the LiveKit room."""
        await self.room.disconnect()
