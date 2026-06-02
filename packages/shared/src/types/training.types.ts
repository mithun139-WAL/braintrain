// Training plan types — Personalized AI Training Plans module
// All fields camelCase (converted from snake_case by axios interceptor)

export type TrainingTaskType = "DRILL" | "EXERCISE" | "REFLECTION" | "PRACTICE" | "READING";
export type TrainingPlanStatus = "ACTIVE" | "COMPLETED" | "ARCHIVED";
export type TrainingDifficulty = "BEGINNER" | "INTERMEDIATE" | "ADVANCED";

export interface TrainingTask {
    id: string;
    title: string;
    description: string;
    taskType: TrainingTaskType;
    focusArea: string;
    durationMinutes: number;
    difficulty: TrainingDifficulty;
    completed: boolean;
    completedAt?: string;
    instructions: string[];         // step-by-step instructions
    successCriteria: string;        // how to know you've done it well
}

export interface TrainingPlan {
    id: string;
    userId: string;
    status: TrainingPlanStatus;
    focusAreas: string[];
    aiReasoning: string;            // WHY this plan was generated (the insight)
    generatedAt: string;
    expiresAt: string;
    tasks: TrainingTask[];
    completedTaskCount: number;
    totalTaskCount: number;
    completionPercentage: number;
}

export interface GeneratePlanRequest {
    focusAreas?: string[];          // optional override; AI auto-selects from session history
    forceRegenerate?: boolean;
}

export interface CompleteTaskResponse {
    task: TrainingTask;
    plan: TrainingPlan;
    message: string;                // encouragement / next step
}
