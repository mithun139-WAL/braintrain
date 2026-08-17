import { create } from 'zustand';
import { Difficulty, InterviewType, InterviewMode } from '@braintrain/shared';

interface SessionBuilderState {
    step: number;
    topicId: string | null;
    interviewType: InterviewType | null;
    interviewMode: InterviewMode | null;
    difficulty: Difficulty;
    adaptive: boolean;
    durationMinutes: number;
    isVoice: boolean;
    interviewCategory: "GENERAL" | "CODING" | "DSA" | "SYSTEM_DESIGN";

    setTopicId: (id: string) => void;
    setInterviewType: (type: InterviewType) => void;
    setInterviewMode: (mode: InterviewMode) => void;
    setDifficulty: (difficulty: Difficulty) => void;
    setAdaptive: (adaptive: boolean) => void;
    setDurationMinutes: (minutes: number) => void;
    setIsVoice: (isVoice: boolean) => void;
    setInterviewCategory: (category: "GENERAL" | "CODING" | "DSA" | "SYSTEM_DESIGN") => void;
    nextStep: () => void;
    prevStep: () => void;
    reset: () => void;
}

export const useSessionBuilderStore = create<SessionBuilderState>((set) => ({
    step: 1,
    topicId: null,
    interviewType: null,
    interviewMode: null,
    difficulty: Difficulty.MEDIUM,
    adaptive: true,
    durationMinutes: 30,
    isVoice: true,
    interviewCategory: "GENERAL",

    setTopicId: (topicId) => set({ topicId }),
    setInterviewType: (interviewType) => set({ interviewType }),
    setInterviewMode: (interviewMode) => set({ interviewMode }),
    setDifficulty: (difficulty) => set({ difficulty }),
    setAdaptive: (adaptive) => set({ adaptive }),
    setDurationMinutes: (durationMinutes) => set({ durationMinutes }),
    setIsVoice: (isVoice) => set({ isVoice }),
    setInterviewCategory: (interviewCategory) => set({ interviewCategory }),
    nextStep: () => set((state) => ({ step: state.step + 1 })),
    prevStep: () => set((state) => ({ step: Math.max(1, state.step - 1) })),
    reset: () => set({
        step: 1,
        topicId: null,
        interviewType: null,
        interviewMode: null,
        difficulty: Difficulty.MEDIUM,
        adaptive: true,
        durationMinutes: 30,
        isVoice: true,
        interviewCategory: "GENERAL",
    }),
}));
