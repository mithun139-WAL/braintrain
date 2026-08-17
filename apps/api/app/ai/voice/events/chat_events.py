import json
import datetime
import logging

logger = logging.getLogger("chat_events")

async def emit_chat_message(transport, message: dict) -> None:
    """
    Sends a structured JSON message over LiveKit data channel.
    message = {
        "role": "interviewer",
        "content": str,          # markdown/plain text
        "content_type": str,     # "text" | "code" | "dsa" | "system_design"
        "language": str | None,  # e.g. "python", "javascript"
    }
    """
    try:
        payload = json.dumps({
            "type": "CHAT_MESSAGE",
            "role": message.get("role", "interviewer"),
            "content": message.get("content", ""),
            "content_type": message.get("content_type", "text"),
            "language": message.get("language"),
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        if hasattr(transport, "room") and transport.room:
            data_bytes = payload.encode("utf-8")
            await transport.room.local_participant.publish_data(data_bytes)
            logger.info("Published chat message over data channel: %s...", message.get("content", "")[:60])
        else:
            logger.warning("Transport room not connected, unable to emit chat message.")
    except Exception as exc:
        logger.error("Failed to emit chat message: %s", exc)
