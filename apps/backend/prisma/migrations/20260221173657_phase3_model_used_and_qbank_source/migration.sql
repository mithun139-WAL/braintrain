-- AlterTable
ALTER TABLE "EvaluationReport" ADD COLUMN     "modelUsed" TEXT;

-- AlterTable
ALTER TABLE "QuestionBank" ADD COLUMN     "source" TEXT NOT NULL DEFAULT 'HUMAN';
