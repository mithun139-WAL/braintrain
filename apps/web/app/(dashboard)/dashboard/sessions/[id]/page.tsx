"use client";

import { useState } from "react";
// import { useSession } from "@/lib/hooks/useSession";
// import QuestionCard from "@/components/session/QuestionCard";
// import AnswerInput from "@/components/session/AnswerInput";
// import Timer from "@/components/session/Timer";

export default function ActiveSessionPage({ params }: { params: { id: string } }) {
    // Client-side hooks example
    // const { session, submitAnswer, status } = useSession(params.id);
    const [currentQuestion, setCurrentQuestion] = useState(1);
    const [isRecording, setIsRecording] = useState(false);

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold">Interview Session</h1>
                {/* <Timer isActive={status === 'ACTIVE'} /> */}
                <div className="text-sm border p-2 rounded bg-muted/50 font-mono">
                    Client Component: Timer Placeholder
                </div>
            </div>

            <div className="border rounded-xl p-6 bg-card">
                {/* <QuestionCard question={session.questions[currentQuestion]} /> */}
                <div className="space-y-4">
                    <h3 className="text-lg font-medium text-muted-foreground">Question {currentQuestion}</h3>
                    <p className="text-xl">Describe a time when you had to make a difficult technical decision under pressure.</p>
                </div>
            </div>

            <div className="border rounded-xl p-6 bg-muted/30">
                {/* <AnswerInput 
             onRecordStart={() => setIsRecording(true)}
             onRecordStop={(audio) => submitAnswer(audio)}
             isRecording={isRecording} 
        /> */}
                <div className="flex flex-col items-center justify-center h-48 space-y-4 text-center border-2 border-dashed rounded-xl">
                    <p className="text-muted-foreground text-sm">Client Component: Answer Input Placeholder</p>
                    <button
                        className={`px-4 py-2 text-primary-foreground text-sm rounded-full ${isRecording ? 'bg-red-500 animate-pulse' : 'bg-primary'}`}
                        onClick={() => setIsRecording(!isRecording)}
                    >
                        {isRecording ? "Stop Recording" : "Start Recording"}
                    </button>
                </div>
            </div>
        </div>
    );
}
