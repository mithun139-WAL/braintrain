-- CreateEnum
CREATE TYPE "InterviewLevel" AS ENUM ('SCREENING', 'TECHNICAL_L1', 'TECHNICAL_L2', 'HR', 'SYSTEM_DESIGN');

-- AlterTable
ALTER TABLE "EvaluationReport" ADD COLUMN     "pressureScore" DOUBLE PRECISION,
ADD COLUMN     "thinkingDepthScore" DOUBLE PRECISION;

-- AlterTable
ALTER TABLE "InterviewSession" ADD COLUMN     "interviewLevel" "InterviewLevel";

-- CreateTable
CREATE TABLE "QuestionBank" (
    "id" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "topicId" TEXT NOT NULL,
    "difficulty" "DifficultyLevel" NOT NULL,
    "questionType" TEXT NOT NULL,
    "isGlobal" BOOLEAN NOT NULL DEFAULT false,
    "createdByUserId" TEXT,
    "usageCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "QuestionBank_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "QuestionBank_topicId_difficulty_idx" ON "QuestionBank"("topicId", "difficulty");

-- AddForeignKey
ALTER TABLE "QuestionBank" ADD CONSTRAINT "QuestionBank_topicId_fkey" FOREIGN KEY ("topicId") REFERENCES "Topic"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "QuestionBank" ADD CONSTRAINT "QuestionBank_createdByUserId_fkey" FOREIGN KEY ("createdByUserId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;
