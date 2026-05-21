"use client";

import { useState, useCallback, useEffect, useRef } from "react";

// ── Web Speech API type declarations ─────────────────────────────────────────
// These are part of the WICG spec and not always present in TS DOM lib typings.
interface SpeechRecognitionErrorEvent extends Event {
    readonly error: string;
    readonly message: string;
}

interface SpeechRecognitionResultItem {
    readonly transcript: string;
    readonly confidence: number;
}

interface SpeechRecognitionResult {
    readonly isFinal: boolean;
    readonly length: number;
    [index: number]: SpeechRecognitionResultItem;
}

interface SpeechRecognitionResultList {
    readonly length: number;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionEvent extends Event {
    readonly resultIndex: number;
    readonly results: SpeechRecognitionResultList;
}

interface ISpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    maxAlternatives: number;
    onstart: (() => void) | null;
    onend: (() => void) | null;
    onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    start(): void;
    stop(): void;
    abort(): void;
}

declare global {
    interface Window {
        SpeechRecognition?: new () => ISpeechRecognition;
        webkitSpeechRecognition?: new () => ISpeechRecognition;
    }
}
// ─────────────────────────────────────────────────────────────────────────────

export interface UseSpeechRecognitionOptions {
    /** Called continuously as the live transcript updates.
     *  Receives the full text (baseText + new speech). */
    onTranscriptChange?: (fullText: string) => void;
    /** Called when the recognition session ends (user stopped or auto-stopped). */
    onListeningStop?: () => void;
}

export interface UseSpeechRecognitionReturn {
    /** Start listening. Pass existing textarea text as `baseText` to preserve it. */
    startListening: (baseText?: string) => void;
    stopListening: () => void;
    isListening: boolean;
    /** The speech-only portion of the transcript (not including baseText). */
    transcript: string;
    isSupported: boolean;
    resetTranscript: () => void;
}

/**
 * useSpeechRecognition
 *
 * Uses the browser's built-in Web Speech Recognition API — completely free,
 * no external APIs, no cost, open-source browser implementation.
 * Supported natively in Chrome and Edge; requires internet on those browsers
 * (Google's recognition server is used under the hood).
 * Firefox does not support it natively.
 *
 * Chrome-specific bugs handled:
 *  1. continuous:true is unreliable in Chrome — stops after ~30s of silence or
 *     network hiccup, firing onend without restarting →
 *     replaced with restart-on-end pattern (continuous:false + auto-restart).
 *  2. Stale onend from an aborted old session fires after a new session starts,
 *     setting isListening back to false →
 *     fixed with a per-session numeric token stored in a ref; callbacks that
 *     don't match the current token are silently discarded.
 */
export function useSpeechRecognition(
    options: UseSpeechRecognitionOptions = {}
): UseSpeechRecognitionReturn {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState("");

    const recognitionRef = useRef<ISpeechRecognition | null>(null);

    // Session token: incremented on every startListening call.
    // All async callbacks check this token and discard themselves if stale.
    const sessionTokenRef = useRef(0);

    // Whether we *want* recognition to be active. Checked in onend to decide
    // whether to restart (restart-on-end pattern) or truly stop.
    const shouldListenRef = useRef(false);

    // Stored so the restart closure has access without a stale closure over
    // startListening's local baseText parameter.
    const baseTextRef = useRef("");

    // Accumulated final transcript segments across recognition restarts.
    const finalTranscriptRef = useRef("");

    // Keep callbacks in refs to avoid stale-closure issues
    const onTranscriptChangeRef = useRef(options.onTranscriptChange);
    const onListeningStopRef = useRef(options.onListeningStop);

    useEffect(() => {
        onTranscriptChangeRef.current = options.onTranscriptChange;
    }, [options.onTranscriptChange]);

    useEffect(() => {
        onListeningStopRef.current = options.onListeningStop;
    }, [options.onListeningStop]);

    const isSupported =
        typeof window !== "undefined" &&
        ("SpeechRecognition" in window || "webkitSpeechRecognition" in window);

    const resetTranscript = useCallback(() => {
        setTranscript("");
        finalTranscriptRef.current = "";
    }, []);

    /**
     * Internal: create and start one recognition segment for `token`.
     * If the segment ends while shouldListenRef is still true, it restarts
     * itself — implementing the restart-on-end pattern.
     */
    const startSession = useCallback(
        (token: number) => {
            if (!isSupported) return;
            // Guard: discard if the token is already stale
            if (sessionTokenRef.current !== token) return;

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const SpeechRecognitionAPI: new () => ISpeechRecognition =
                window.SpeechRecognition ?? window.webkitSpeechRecognition!;

            const recognition = new SpeechRecognitionAPI();
            recognitionRef.current = recognition;

            // continuous:false is more reliable; we restart manually in onend.
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = "en-US";
            recognition.maxAlternatives = 1;

            recognition.onstart = () => {
                if (sessionTokenRef.current !== token) return;
                setIsListening(true);
            };

            recognition.onend = () => {
                if (sessionTokenRef.current !== token) return;
                recognitionRef.current = null;

                if (shouldListenRef.current) {
                    // Restart-on-end: keep the session alive.
                    // Delay 150ms so Chrome's SpeechRecognition API fully resets
                    // before we call start() on the next instance.
                    setTimeout(() => {
                        // Re-check: user may have stopped listening during the delay
                        if (sessionTokenRef.current === token && shouldListenRef.current) {
                            startSession(token);
                        }
                    }, 150);
                } else {
                    setIsListening(false);
                    onListeningStopRef.current?.();
                }
            };

            recognition.onerror = (event) => {
                if (sessionTokenRef.current !== token) return;

                // "aborted" means we called abort() ourselves — ignore entirely.
                // Chrome will fire onend next; don't touch any state here.
                if (event.error === "aborted") return;

                if (event.error !== "no-speech") {
                    console.warn("Speech recognition error:", event.error);
                }

                // Permission denied — stop trying; retrying is futile.
                if (
                    event.error === "not-allowed" ||
                    event.error === "service-not-allowed"
                ) {
                    shouldListenRef.current = false;
                    setIsListening(false);
                    return;
                }

                // For all other errors (network, no-speech, audio-capture, etc.)
                // DO NOT restart here. Chrome always fires onend after onerror.
                // Restarting in both onerror AND onend creates two simultaneous
                // recognition instances that cascade into an unrecoverable state.
                // onend is the single authoritative place to restart.
            };

            recognition.onresult = (event) => {
                if (sessionTokenRef.current !== token) return;

                let interimTranscript = "";

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        finalTranscriptRef.current += result[0].transcript;
                    } else {
                        interimTranscript += result[0].transcript;
                    }
                }

                const speechText = (
                    finalTranscriptRef.current + interimTranscript
                ).trim();
                setTranscript(speechText);

                // Merge with any text that was already in the textarea
                const trimmedBase = baseTextRef.current.trimEnd();
                const separator = trimmedBase && speechText ? " " : "";
                const fullText = trimmedBase + separator + speechText;
                onTranscriptChangeRef.current?.(fullText);
            };

            try {
                recognition.start();
            } catch (e) {
                // start() throws if called on an already-started instance
                console.warn("Speech recognition start error:", e);
            }
        },
        [isSupported]
    );

    const startListening = useCallback(
        (baseText: string = "") => {
            if (!isSupported) return;

            // Abort any existing session immediately.
            // Use abort() (not stop()) so it stops without waiting for final results,
            // preventing its onend from triggering a ghost restart.
            if (recognitionRef.current) {
                recognitionRef.current.abort();
                recognitionRef.current = null;
            }

            // Reset state for new session
            baseTextRef.current = baseText;
            finalTranscriptRef.current = "";
            setTranscript("");
            shouldListenRef.current = true;

            // Increment token — invalidates all callbacks from the previous session
            sessionTokenRef.current += 1;
            const token = sessionTokenRef.current;

            startSession(token);
        },
        [isSupported, startSession]
    );

    const stopListening = useCallback(() => {
        // Signal that we no longer want recognition active (prevents restart-on-end)
        shouldListenRef.current = false;
        // Invalidate any pending restart callbacks
        sessionTokenRef.current += 1;

        if (recognitionRef.current) {
            recognitionRef.current.abort();
            recognitionRef.current = null;
        }
        setIsListening(false);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            shouldListenRef.current = false;
            sessionTokenRef.current += 1; // invalidate any pending restarts
            if (recognitionRef.current) {
                recognitionRef.current.abort();
                recognitionRef.current = null;
            }
        };
    }, []);

    return {
        startListening,
        stopListening,
        isListening,
        transcript,
        isSupported,
        resetTranscript,
    };
}
