"use client";

import React, { useState, useEffect, useRef } from "react";
import {
    LiveKitRoom,
    RoomAudioRenderer,
    useRoomContext,
    useConnectionState,
    useLocalParticipant,
} from "@livekit/components-react";
import { ConnectionState, RoomEvent } from "livekit-client";
import type { Participant } from "livekit-client";
import {
    Mic,
    MicOff,
    PhoneOff,
    Loader2,
    ShieldAlert,
    MessageSquare,
    Wifi,
    WifiOff,
    BrainCircuit,
    User,
} from "lucide-react";
import { sessionsApi } from "@/lib/api/sessions.api";
import { cn } from "@/lib/utils";
import { InterviewMode } from "@braintrain/shared";

// ── Types ─────────────────────────────────────────────────────────────────────

interface VoiceInterviewSessionProps {
    sessionId: string;
    candidateName: string;
    onEndSession: () => void;
    interviewMode?: string;
}

interface TranscriptLine {
    speaker: string;
    text: string;
    time: string;
}

// ── Root component ────────────────────────────────────────────────────────────

/**
 * Fetches the LiveKit JWT token, then mounts the room.
 * Nothing LiveKit-specific lives here — keeps token fetch logic separate.
 */
export const VoiceInterviewSession: React.FC<VoiceInterviewSessionProps> = ({
    sessionId,
    candidateName,
    onEndSession,
    interviewMode,
}) => {
    const [token, setToken] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        sessionsApi
            .getWebRTCToken(sessionId)
            .then((res) => {
                if (res.success && res.data?.token) {
                    setToken(res.data.token);
                } else {
                    setError("Failed to generate LiveKit access token.");
                }
            })
            .catch((err: Error) => setError(err.message || "Error fetching token."));
    }, [sessionId]);

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-full min-h-[70vh] bg-[#202124] rounded-2xl text-white p-8">
                <ShieldAlert className="size-14 text-red-500 mb-4" />
                <p className="text-red-400 font-bold text-lg mb-1">Connection Failed</p>
                <p className="text-sm text-gray-400 mb-6 text-center max-w-sm">{error}</p>
                <button
                    onClick={onEndSession}
                    className="px-6 py-2.5 bg-neutral-700 hover:bg-neutral-600 text-white rounded-full transition-colors text-sm font-medium"
                >
                    Return to Session
                </button>
            </div>
        );
    }

    if (!token) {
        return (
            <div className="flex flex-col items-center justify-center h-full min-h-[70vh] bg-[#202124] rounded-2xl text-white">
                <div className="relative mb-5">
                    <div className="size-14 rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
                    <BrainCircuit className="absolute inset-0 m-auto size-6 text-indigo-400" />
                </div>
                <p className="text-sm text-gray-400 animate-pulse">
                    Setting up your interview room…
                </p>
            </div>
        );
    }

    return (
        <LiveKitRoom
            video={false}
            audio={true}
            token={token}
            serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880"}
            connectOptions={{ autoSubscribe: true }}
            className="flex flex-col w-full h-full min-h-0"
        >
            <MeetRoomContainer
                candidateName={candidateName}
                onEndSession={onEndSession}
                interviewMode={interviewMode}
            />
            <RoomAudioRenderer />
        </LiveKitRoom>
    );
};

// ── Google Meet-style room ────────────────────────────────────────────────────

const MeetRoomContainer: React.FC<{
    candidateName: string;
    onEndSession: () => void;
    interviewMode?: string;
}> = ({ candidateName, onEndSession, interviewMode }) => {
    const room = useRoomContext();
    const connectionState = useConnectionState();
    const { localParticipant } = useLocalParticipant();

    const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
    const [showTranscript, setShowTranscript] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
    const [isUserSpeaking, setIsUserSpeaking] = useState(false);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const [currentSpeaker, setCurrentSpeaker] = useState<string>("Marcus");

    const isConnected = connectionState === ConnectionState.Connected;

    // ── Elapsed-time counter ────────────────────────────────────────────────
    useEffect(() => {
        if (!isConnected) return;
        const id = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
        return () => clearInterval(id);
    }, [isConnected]);

    const formatElapsed = (s: number) =>
        `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

    // ── Transcript via LiveKit Data Channel ─────────────────────────────────
    useEffect(() => {
        const handleData = (payload: Uint8Array) => {
            try {
                const data = JSON.parse(new TextDecoder().decode(payload)) as {
                    speaker?: string;
                    text?: string;
                };
                if (data.speaker) {
                    if (["Marcus", "Sarah", "David"].includes(data.speaker)) {
                        setCurrentSpeaker(data.speaker);
                    }
                    if (data.text) {
                        setTranscript((prev) => [
                            ...prev,
                            {
                                speaker: data.speaker!,
                                text: data.text!,
                                time: new Date().toLocaleTimeString([], {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                    second: "2-digit",
                                }),
                            },
                        ]);
                    }
                }
            } catch {
                // Malformed packet — ignore
            }
        };

        room.on(RoomEvent.DataReceived, handleData);
        return () => {
            room.off(RoomEvent.DataReceived, handleData);
        };
    }, [room]);

    // ── Active-speaker detection via LiveKit server VAD ─────────────────────
    useEffect(() => {
        const handleActiveSpeakers = (speakers: Participant[]) => {
            setIsAgentSpeaking(
                speakers.some((p) => p.identity === "AI_Interviewer")
            );
            setIsUserSpeaking(
                speakers.some((p) => p.identity !== "AI_Interviewer")
            );
        };

        room.on(RoomEvent.ActiveSpeakersChanged, handleActiveSpeakers);
        return () => {
            room.off(RoomEvent.ActiveSpeakersChanged, handleActiveSpeakers);
        };
    }, [room]);

    const toggleMute = async () => {
        if (!localParticipant) return;
        const next = !isMuted;
        setIsMuted(next);
        await localParticipant.setMicrophoneEnabled(!next);
    };

    const isMarcusSpeaking = isAgentSpeaking && currentSpeaker === "Marcus";
    const isSarahSpeaking = isAgentSpeaking && currentSpeaker === "Sarah";
    const isDavidSpeaking = isAgentSpeaking && currentSpeaker === "David";

    return (
        <div
            className="flex flex-col w-full h-full min-h-0 rounded-2xl overflow-hidden border border-border bg-background"
        >
            {/* ── Top bar ──────────────────────────────────────────────────── */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-card/45 backdrop-blur-md">
                <div className="flex items-center gap-3">
                    <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
                        <BrainCircuit className="size-4" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-foreground leading-tight">
                            Mock Interview
                        </p>
                        <p className="text-[10px] text-muted-foreground leading-tight">
                            AI-Powered Session
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {isConnected && (
                        <span className="text-sm font-mono text-muted-foreground tabular-nums">
                            {formatElapsed(elapsedSeconds)}
                        </span>
                    )}
                    <div
                        className={cn(
                            "flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wide border",
                            isConnected
                                ? "bg-emerald/10 text-emerald border-emerald/20"
                                : "bg-gold/10 text-gold border-gold/20"
                        )}
                    >
                        {isConnected ? (
                            <Wifi size={10} />
                        ) : (
                            <WifiOff size={10} />
                        )}
                        {connectionState === ConnectionState.Connecting
                            ? "Connecting…"
                            : isConnected
                            ? "Live"
                            : "Disconnected"}
                    </div>
                </div>
            </div>

            {/* ── Participant tiles + transcript ────────────────────────── */}
            <div className="flex-1 flex flex-col lg:flex-row gap-3 p-3 min-h-0">
                {/* Participant tiles */}
                {interviewMode === InterviewMode.PANEL_AI ? (
                    <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3 min-h-0">
                        {/* Marcus Johnson */}
                        <ParticipantTile
                            displayName="Marcus"
                            avatarLabel="MJ"
                            avatarGradient="from-blue-600 to-indigo-700"
                            ringColor="ring-blue-500"
                            glowColor="shadow-blue-500/25"
                            barColor="bg-blue-400"
                            pulseColor="bg-blue-500"
                            badgeColor="bg-blue-500/15 text-blue-300 border-blue-500/25"
                            dotColor="bg-blue-400"
                            isSpeaking={isMarcusSpeaking}
                            statusLabel={
                                isMarcusSpeaking
                                    ? "Speaking"
                                    : isConnected
                                    ? "Listening"
                                    : "Connecting…"
                            }
                            avatarIcon={
                                <img
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuBtkhzmd3n507non6jInf7K0NM3nWA_t_08DZe4M_RQrKGeUEy5FGthJz81zQwJIWCpeKnyWEEHorz8Po47joiG6tuevxvZC-oWKc1zy5KcSU0NuKkemYdJ65kj6kiSsY5GR55ErvW3hRiTA5EZBz4xSr_zy5RfrZ6X16-NaMn8h-PWru4G3jX3G05zabAdFDKHuC6V4X1-uC_Sjl-Y6YtuYb2oyVaAl_ILU1qeiBTiT7OGMP79CoUV0hSDbz2dqGe9Rh8vaskDuoc"
                                    className="size-full rounded-full object-cover"
                                    alt="Marcus"
                                />
                            }
                            className="min-h-0"
                        />

                        {/* Sarah Chen */}
                        <ParticipantTile
                            displayName="Sarah"
                            avatarLabel="SC"
                            avatarGradient="from-pink-600 to-rose-700"
                            ringColor="ring-pink-500"
                            glowColor="shadow-pink-500/25"
                            barColor="bg-pink-400"
                            pulseColor="bg-pink-500"
                            badgeColor="bg-pink-500/15 text-pink-300 border-pink-500/25"
                            dotColor="bg-pink-400"
                            isSpeaking={isSarahSpeaking}
                            statusLabel={
                                isSarahSpeaking
                                    ? "Speaking"
                                    : isConnected
                                    ? "Listening"
                                    : "Connecting…"
                            }
                            avatarIcon={
                                <img
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuAV25uqcrWjzm0uyImmy_Hv8judeMlCBAhNV7HbQwaedKzWlTKvYJfbh8cc9qKPY_NQQi0cRl5tWl1T2hjtom3VIztWUieLg60XBCpiyDw0PC1aZak87opH091cpOUys6-4d2EMc07hdlbwUjV_QtiNdKRU8uzHGf9LKKpcXBP7SvLi1EckD017J0cA6hbY0TaElB4HP-YsM4zCiphK2kM4t0lJK4dUMmtPviGrghTEG77OJfgpfEq4Gu0SaWvqxp9Kn1SIJcEn6pk"
                                    className="size-full rounded-full object-cover"
                                    alt="Sarah"
                                />
                            }
                            className="min-h-0"
                        />

                        {/* David Wright */}
                        <ParticipantTile
                            displayName="David"
                            avatarLabel="DW"
                            avatarGradient="from-amber-600 to-orange-700"
                            ringColor="ring-amber-500"
                            glowColor="shadow-amber-500/25"
                            barColor="bg-amber-400"
                            pulseColor="bg-amber-500"
                            badgeColor="bg-amber-500/15 text-amber-300 border-amber-500/25"
                            dotColor="bg-amber-400"
                            isSpeaking={isDavidSpeaking}
                            statusLabel={
                                isDavidSpeaking
                                    ? "Speaking"
                                    : isConnected
                                    ? "Listening"
                                    : "Connecting…"
                            }
                            avatarIcon={
                                <img
                                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuB17zDeUEnok2_UtbAFmM554O2SXBzjMiBm1jQID86EnetT6vTUNfk6LyPJJdIyDcx1xUZJqcXthryBDpWiqO3bFX9irYFfGJDdECbo9NhBkY28nm-knjk4iU-YZiU6HuBFdIIxlfpPocPer_K2g5RuO_lsiWG4RhOJcNemOuYQ_BwGbYm-W-r3BsCy4HF_VtCuFc8ijgQwjQMvmwAFH9gmZC74dOobzax5YFcwm18edgieAPeK9R_ZTcwB-e9wd0StAA1of3gaiBI"
                                    className="size-full rounded-full object-cover"
                                    alt="David"
                                />
                            }
                            className="min-h-0"
                        />

                        {/* Candidate */}
                        <ParticipantTile
                            displayName={candidateName || "You"}
                            avatarLabel="ME"
                            avatarGradient="from-emerald-500 to-teal-600"
                            ringColor="ring-emerald-500"
                            glowColor="shadow-emerald-500/25"
                            barColor="bg-emerald-400"
                            pulseColor="bg-emerald-500"
                            badgeColor="bg-emerald-500/15 text-emerald-300 border-emerald-500/25"
                            dotColor="bg-emerald-400"
                            isSpeaking={isUserSpeaking}
                            isMuted={isMuted}
                            statusLabel={
                                isMuted ? "Muted" : isUserSpeaking ? "Speaking" : "Listening"
                            }
                            avatarIcon={<User className="size-8 text-white" />}
                            className="min-h-0"
                            isLocal
                        />
                    </div>
                ) : (
                    <div className="flex-1 flex flex-col md:flex-row gap-3 min-h-0">
                        {/* AI Interviewer — large dominant tile */}
                        <ParticipantTile
                            displayName="AI Interviewer"
                            avatarLabel="AI"
                            avatarGradient="from-indigo-500 via-violet-500 to-purple-600"
                            ringColor="ring-indigo-500"
                            glowColor="shadow-indigo-500/25"
                            barColor="bg-indigo-400"
                            pulseColor="bg-indigo-500"
                            badgeColor="bg-indigo-500/15 text-indigo-300 border-indigo-500/25"
                            dotColor="bg-indigo-400"
                            isSpeaking={isAgentSpeaking}
                            statusLabel={
                                isAgentSpeaking
                                    ? "Speaking"
                                    : isConnected
                                    ? "Listening"
                                    : "Connecting…"
                            }
                            avatarIcon={<BrainCircuit className="size-10 text-white" />}
                            className="flex-1 min-h-0"
                        />

                        {/* User — smaller tile */}
                        <ParticipantTile
                            displayName={candidateName || "You"}
                            avatarLabel="ME"
                            avatarGradient="from-emerald-500 to-teal-600"
                            ringColor="ring-emerald-500"
                            glowColor="shadow-emerald-500/25"
                            barColor="bg-emerald-400"
                            pulseColor="bg-emerald-500"
                            badgeColor="bg-emerald-500/15 text-emerald-300 border-emerald-500/25"
                            dotColor="bg-emerald-400"
                            isSpeaking={isUserSpeaking}
                            isMuted={isMuted}
                            statusLabel={
                                isMuted ? "Muted" : isUserSpeaking ? "Speaking" : "Listening"
                            }
                            avatarIcon={<User className="size-8 text-white" />}
                            className="flex-1 min-h-0"
                            isLocal
                        />
                    </div>
                )}

                {/* Right panel: live transcript (toggleable) */}
                {showTranscript && (
                    <div className="w-full lg:w-[320px] xl:w-[380px] flex-shrink-0 flex flex-col min-h-0 bg-card rounded-2xl overflow-hidden border border-border shadow-sm">
                        <TranscriptPanel transcript={transcript} />
                    </div>
                )}
            </div>

            {/* ── Bottom control bar ────────────────────────────────────── */}
            <div className="flex items-center justify-center gap-4 py-4 px-6 border-t border-border">
                {/* Mic toggle */}
                <ControlButton
                    onClick={toggleMute}
                    disabled={!isConnected}
                    label={isMuted ? "Unmute" : "Mute"}
                    active={!isMuted}
                    activeClass="bg-primary/10 text-primary hover:bg-primary/20 border border-primary/25"
                    inactiveClass="bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white border border-red-500/20"
                    icon={isMuted ? <MicOff size={18} /> : <Mic size={18} />}
                />

                {/* Transcript toggle */}
                <ControlButton
                    onClick={() => setShowTranscript((v) => !v)}
                    label="Transcript"
                    active={showTranscript}
                    activeClass="bg-primary/10 text-primary hover:bg-primary/20 border border-primary/25"
                    inactiveClass="bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground border border-border"
                    icon={<MessageSquare size={18} />}
                    badge={
                        transcript.length > 0 && !showTranscript
                            ? String(Math.min(transcript.length, 99))
                            : undefined
                    }
                />

                {/* End call */}
                <button
                    onClick={onEndSession}
                    title="End interview"
                    className="flex flex-col items-center flex-shrink-0"
                >
                    <div className="size-11 rounded-full bg-ruby/10 hover:bg-ruby text-ruby hover:text-white flex items-center justify-center border border-ruby/25 transition-all">
                        <PhoneOff size={18} />
                    </div>
                </button>
            </div>
        </div>
    );
};

// ── Participant tile ──────────────────────────────────────────────────────────

interface ParticipantTileProps {
    displayName: string;
    avatarLabel: string;
    avatarGradient: string;
    ringColor: string;
    glowColor: string;
    barColor: string;
    pulseColor: string;
    badgeColor: string;
    dotColor: string;
    isSpeaking: boolean;
    isMuted?: boolean;
    statusLabel: string;
    avatarIcon: React.ReactNode;
    className?: string;
    isLocal?: boolean;
}

const SPEAKING_BAR_HEIGHTS = [40, 65, 90, 75, 55, 85, 45, 70, 60];

const ParticipantTile: React.FC<ParticipantTileProps> = ({
    displayName,
    avatarLabel,
    avatarGradient,
    ringColor,
    glowColor,
    barColor,
    pulseColor,
    badgeColor,
    dotColor,
    isSpeaking,
    isMuted,
    statusLabel,
    avatarIcon,
    className,
    isLocal,
}) => {
    return (
        <div
            className={cn(
                "relative bg-card border border-border rounded-xl overflow-hidden",
                "flex items-center justify-center",
                "transition-all duration-200",
                isSpeaking ? "border-primary ring-1 ring-primary/20 bg-primary/[0.02]" : "border-border/60",
                className
            )}
        >
            {/* Centred content */}
            <div className="relative z-10 flex flex-col items-center gap-3.5">
                {/* Clean Flat Avatar */}
                <div className="relative flex items-center justify-center">
                    <div
                        className={cn(
                            "size-16 rounded-full bg-primary/10 text-primary flex items-center justify-center",
                            "transition-all duration-200 z-10 relative"
                        )}
                    >
                        {avatarIcon}
                    </div>
                </div>

                {/* Extremely subtle speaking indicator */}
                <div className="h-4 flex items-center justify-center">
                    {isSpeaking ? (
                        <div className="flex items-center gap-1">
                            <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Speaking</span>
                            <div className="flex items-end gap-[2px] h-2.5">
                                {[1, 2, 3].map((i) => (
                                    <div
                                        key={i}
                                        className="w-[2px] rounded-full bg-primary speaking-bar"
                                        style={{
                                            height: i === 2 ? "10px" : "6px",
                                            animationDelay: `${i * 0.15}s`,
                                        }}
                                    />
                                ))}
                            </div>
                        </div>
                    ) : (
                        <span className="text-[10px] text-muted-foreground font-medium">
                            {isMuted ? "Muted" : "Silent"}
                        </span>
                    )}
                </div>
            </div>

            {/* Name + role badge — bottom-left */}
            <div className="absolute bottom-3 left-3 flex items-center gap-2">
                <div className="flex items-center gap-1 bg-background/80 backdrop-blur-sm border border-border/40 px-2 py-0.5 rounded-md">
                    <span className="text-[11px] font-semibold text-foreground">{displayName}</span>
                    {isMuted && <MicOff size={10} className="text-red-400 shrink-0" />}
                    {isLocal && !isMuted && (
                        <span className="text-[9px] text-muted-foreground">(You)</span>
                    )}
                </div>
            </div>
        </div>
    );
};

// ── Reusable control button ───────────────────────────────────────────────────

const ControlButton: React.FC<{
    onClick: () => void;
    icon: React.ReactNode;
    label: string;
    active: boolean;
    activeClass: string;
    inactiveClass: string;
    disabled?: boolean;
    badge?: string;
}> = ({ onClick, icon, label, active, activeClass, inactiveClass, disabled, badge }) => (
    <button
        onClick={onClick}
        disabled={disabled}
        title={label}
        className="flex flex-col items-center gap-1.5 group disabled:opacity-40 disabled:cursor-not-allowed"
    >
        <div
            className={cn(
                "size-12 rounded-full flex items-center justify-center transition-all active:scale-95 relative",
                active ? activeClass : inactiveClass
            )}
        >
            {icon}
            {badge && (
                <span className="absolute -top-0.5 -right-0.5 size-4 bg-indigo-500 rounded-full text-[9px] text-white flex items-center justify-center font-bold leading-none">
                    {badge}
                </span>
            )}
        </div>
        <span className="text-[10px] text-gray-500 group-hover:text-gray-400 transition-colors">
            {label}
        </span>
    </button>
);

// ── Live transcript panel ─────────────────────────────────────────────────────

const TranscriptPanel: React.FC<{ transcript: TranscriptLine[] }> = ({
    transcript,
}) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [search, setSearch] = useState("");

    // Auto-scroll to latest line
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [transcript]);

    const filtered = transcript.filter(
        (l) =>
            l.text.toLowerCase().includes(search.toLowerCase()) ||
            l.speaker.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <>
            {/* Header */}
            <div className="px-4 pt-4 pb-3 border-b border-white/5 space-y-2 shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {/* Live recording indicator */}
                        <span className="relative flex size-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex size-2.5 rounded-full bg-red-500" />
                        </span>
                        <span className="text-xs font-bold uppercase tracking-wider text-gray-200">
                            Live Transcript
                        </span>
                    </div>
                    <span className="text-[10px] text-gray-500 bg-white/5 px-2 py-0.5 rounded-full border border-white/5">
                        {transcript.length} {transcript.length === 1 ? "line" : "lines"}
                    </span>
                </div>
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search transcript…"
                    className="w-full bg-white/5 text-xs border border-white/5 focus:border-indigo-500/50 focus:bg-white/[0.08] outline-none rounded-xl px-3.5 py-2 text-gray-200 placeholder:text-gray-500 transition-all duration-200"
                />
            </div>

            {/* Scrollable messages */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar"
            >
                {filtered.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full gap-3 py-12 text-center">
                        <MessageSquare className="size-8 text-gray-600 opacity-50" />
                        <p className="text-xs text-gray-600">
                            {search
                                ? "No matching lines found."
                                : "Transcript will appear here as the conversation unfolds…"}
                        </p>
                    </div>
                ) : (
                    filtered.map((line, idx) => {
                        const isAI = ["Interviewer", "Marcus", "Sarah", "David"].includes(line.speaker);
                        return (
                            <div
                                key={idx}
                                className="flex items-start gap-3 animate-fade-in group"
                            >
                                {/* Speaker avatar */}
                                <div
                                    className={cn(
                                        "size-8 rounded-xl flex items-center justify-center text-[10px] font-bold shrink-0 border transition-transform duration-300 group-hover:scale-105",
                                        isAI
                                            ? "bg-indigo-500/10 border-indigo-500/20 text-indigo-300"
                                            : "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                                    )}
                                >
                                    {isAI ? (line.speaker === "Interviewer" ? "AI" : line.speaker.slice(0, 2).toUpperCase()) : "ME"}
                                </div>

                                {/* Message bubble */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-baseline justify-between mb-1">
                                        <span
                                            className={cn(
                                                "text-xs font-semibold",
                                                isAI ? "text-indigo-400" : "text-emerald-400"
                                            )}
                                        >
                                            {isAI ? line.speaker : "You"}
                                        </span>
                                        <span className="text-[9px] text-gray-500 font-mono">
                                            {line.time}
                                        </span>
                                    </div>
                                    <div
                                        className={cn(
                                            "text-xs text-gray-300 leading-relaxed p-3 rounded-2xl break-words border transition-all duration-200",
                                            isAI
                                                ? "bg-white/[0.02] border-white/5 hover:border-white/10 rounded-tl-none"
                                                : "bg-emerald-500/[0.02] border-emerald-500/10 hover:border-emerald-500/20 rounded-tr-none"
                                        )}
                                    >
                                        {line.text}
                                    </div>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </>
    );
};
