"use client";

import { useState, useCallback, useEffect, useRef } from "react";

export interface UseSpeechSynthesisReturn {
    speak: (text: string) => void;
    stop: () => void;
    isSpeaking: boolean;
    isSupported: boolean;
}

/**
 * useSpeechSynthesis
 *
 * Uses the browser's built-in Web Speech Synthesis API — completely free,
 * no external APIs, no cost, open-source browser implementation.
 * Works in Chrome, Edge, Safari, and Firefox.
 *
 * Chrome-specific bugs handled:
 *  1. cancel() + speak() in the same tick silently drops the utterance →
 *     deferred speak via setTimeout(100ms).
 *  2. getVoices() returns [] on first call because voices load asynchronously →
 *     populated via the "voiceschanged" event and stored in a ref.
 *  3. speechSynthesis pauses when the tab is hidden →
 *     resumed on visibilitychange.
 */
export function useSpeechSynthesis(): UseSpeechSynthesisReturn {
    const [isSpeaking, setIsSpeaking] = useState(false);

    // Timer ref for the deferred speak (cancel/speak bug workaround)
    const pendingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    // Voices ref — populated once the browser loads them
    const voicesRef = useRef<SpeechSynthesisVoice[]>([]);

    const isSupported =
        typeof window !== "undefined" && "speechSynthesis" in window;

    // Populate voicesRef as soon as voices are available
    useEffect(() => {
        if (!isSupported) return;

        const loadVoices = () => {
            voicesRef.current = window.speechSynthesis.getVoices();
        };

        loadVoices(); // already populated in Firefox/Safari
        window.speechSynthesis.addEventListener("voiceschanged", loadVoices);
        return () => {
            window.speechSynthesis.removeEventListener("voiceschanged", loadVoices);
        };
    }, [isSupported]);

    const stop = useCallback(() => {
        if (!isSupported) return;
        // Cancel any pending deferred speak
        if (pendingTimerRef.current !== null) {
            clearTimeout(pendingTimerRef.current);
            pendingTimerRef.current = null;
        }
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    }, [isSupported]);

    const speak = useCallback(
        (text: string) => {
            if (!isSupported || !text.trim()) return;

            // Cancel any pending deferred speak
            if (pendingTimerRef.current !== null) {
                clearTimeout(pendingTimerRef.current);
                pendingTimerRef.current = null;
            }

            // Cancel current speech synchronously
            window.speechSynthesis.cancel();

            // Chrome bug: cancel() + speak() in the same synchronous call silently
            // drops the utterance. Defer speak() by 100ms to let cancel() settle.
            pendingTimerRef.current = setTimeout(() => {
                pendingTimerRef.current = null;

                const utterance = new SpeechSynthesisUtterance(text);

                // Prefer cached voices; fall back to a fresh getVoices() call
                const allVoices = voicesRef.current.length
                    ? voicesRef.current
                    : window.speechSynthesis.getVoices();

                const preferredVoice =
                    allVoices.find((v) => v.name === "Google US English") ||
                    allVoices.find((v) => v.name === "Samantha") ||
                    allVoices.find((v) =>
                        v.name === "Microsoft Zira - English (United States)"
                    ) ||
                    allVoices.find((v) => v.lang === "en-US" && v.localService) ||
                    allVoices.find((v) => v.lang === "en-US") ||
                    allVoices.find((v) => v.lang.startsWith("en")) ||
                    allVoices[0] ||
                    null;

                if (preferredVoice) utterance.voice = preferredVoice;

                // Slightly slower rate for clarity in an interview context
                utterance.rate = 0.92;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;

                utterance.onstart = () => setIsSpeaking(true);
                utterance.onend = () => setIsSpeaking(false);
                utterance.onerror = () => setIsSpeaking(false);

                window.speechSynthesis.speak(utterance);
            }, 100);
        },
        [isSupported]
    );

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pendingTimerRef.current !== null) {
                clearTimeout(pendingTimerRef.current);
            }
            if (isSupported) {
                window.speechSynthesis.cancel();
            }
        };
    }, [isSupported]);

    // Chrome bug: speechSynthesis pauses when the tab is hidden.
    // Resume it when the tab becomes visible again.
    useEffect(() => {
        if (!isSupported) return;

        const handleVisibilityChange = () => {
            if (!document.hidden && window.speechSynthesis.paused) {
                window.speechSynthesis.resume();
            }
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);
        return () => {
            document.removeEventListener(
                "visibilitychange",
                handleVisibilityChange
            );
        };
    }, [isSupported]);

    return { speak, stop, isSpeaking, isSupported };
}
