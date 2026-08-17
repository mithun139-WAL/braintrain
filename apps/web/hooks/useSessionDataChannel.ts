import { useCallback, useEffect, useState } from "react";
import { Room, RoomEvent } from "livekit-client";

export interface ChatMessage {
    id: string;
    role: "interviewer" | "candidate";
    content: string;
    content_type: "text" | "code" | "dsa" | "system_design";
    language?: string;
    timestamp: string;
    source?: "voice" | "text";
}

export function useSessionDataChannel(room: Room | null) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    useEffect(() => {
        if (!room) return;

        const handleDataReceived = (
            payload: Uint8Array,
            participant?: any,
            _blockIndex?: any,
            _recipient?: any
        ) => {
            try {
                const text = new TextDecoder().decode(payload);
                const data = JSON.parse(text);

                if (data.type === "CHAT_MESSAGE") {
                    setMessages((prev) => {
                        // Deduplicate by content and timestamp
                        const exists = prev.some(
                            (m) =>
                                m.content === data.content &&
                                m.timestamp === data.timestamp
                        );
                        if (exists) return prev;

                        return [
                            ...prev,
                            {
                                id: `${data.role}-${data.timestamp}-${Math.random().toString(36).substr(2, 9)}`,
                                role: data.role,
                                content: data.content,
                                content_type: data.content_type || "text",
                                language: data.language,
                                timestamp: data.timestamp || new Date().toISOString(),
                            },
                        ];
                    });
                }
            } catch (err) {
                console.error("Error parsing data channel message:", err);
            }
        };

        room.on(RoomEvent.DataReceived, handleDataReceived);
        return () => {
            room.off(RoomEvent.DataReceived, handleDataReceived);
        };
    }, [room]);

    const sendMessage = useCallback(
        async (content: string, imageFile?: File) => {
            if (!room) return;

            let image_b64: string | null = null;
            if (imageFile) {
                const reader = new FileReader();
                image_b64 = await new Promise<string>((resolve) => {
                    reader.onloadend = () => {
                        const base64String = reader.result as string;
                        // Strip data prefix
                        resolve(base64String.split(",")[1]);
                    };
                    reader.readAsDataURL(imageFile);
                });
            }

            const payload = JSON.stringify({
                type: "CANDIDATE_MESSAGE",
                content,
                image_b64,
            });

            const data = new TextEncoder().encode(payload);
            await room.localParticipant.publishData(data, { reliable: true });

            // Add locally to messages state
            setMessages((prev) => [
                ...prev,
                {
                    id: `candidate-${Date.now()}`,
                    role: "candidate",
                    content,
                    content_type: "text",
                    timestamp: new Date().toISOString(),
                    source: "text",
                },
            ]);
        },
        [room]
    );

    return { messages, setMessages, sendMessage };
}
