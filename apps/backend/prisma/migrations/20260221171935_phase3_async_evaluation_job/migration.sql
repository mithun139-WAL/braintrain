-- CreateEnum
CREATE TYPE "EvaluationJobStatus" AS ENUM ('PENDING', 'PROCESSING', 'FAILED', 'COMPLETED');

-- AlterTable
ALTER TABLE "EvaluationReport" ADD COLUMN     "estimatedCostUsd" DOUBLE PRECISION,
ADD COLUMN     "inputTokens" INTEGER,
ADD COLUMN     "outputTokens" INTEGER,
ADD COLUMN     "promptVersion" TEXT DEFAULT 'stub';

-- AlterTable
ALTER TABLE "ResponseInstance" ADD COLUMN     "pressureScore" DOUBLE PRECISION,
ADD COLUMN     "thinkingDepthScore" DOUBLE PRECISION;

-- CreateTable
CREATE TABLE "EvaluationJob" (
    "id" TEXT NOT NULL,
    "sessionId" TEXT NOT NULL,
    "status" "EvaluationJobStatus" NOT NULL DEFAULT 'PENDING',
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "lastError" TEXT,
    "evaluationStartedAt" TIMESTAMP(3),
    "evaluationCompletedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EvaluationJob_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "EvaluationJob_sessionId_key" ON "EvaluationJob"("sessionId");

-- AddForeignKey
ALTER TABLE "EvaluationJob" ADD CONSTRAINT "EvaluationJob_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "InterviewSession"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
