/*
  Warnings:

  - You are about to drop the column `knowledgeScore` on the `EvaluationReport` table. All the data in the column will be lost.
  - You are about to drop the column `structuredAnswerScore` on the `EvaluationReport` table. All the data in the column will be lost.
  - Added the required column `communicationScore` to the `EvaluationReport` table without a default value. This is not possible if the table is not empty.
  - Added the required column `depthScore` to the `EvaluationReport` table without a default value. This is not possible if the table is not empty.
  - Added the required column `hesitationScore` to the `EvaluationReport` table without a default value. This is not possible if the table is not empty.
  - Added the required column `structureScore` to the `EvaluationReport` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "EvaluationReport" DROP COLUMN "knowledgeScore",
DROP COLUMN "structuredAnswerScore",
ADD COLUMN     "communicationScore" DOUBLE PRECISION NOT NULL,
ADD COLUMN     "depthScore" DOUBLE PRECISION NOT NULL,
ADD COLUMN     "hesitationScore" DOUBLE PRECISION NOT NULL,
ADD COLUMN     "structureScore" DOUBLE PRECISION NOT NULL,
ADD COLUMN     "technicalScore" DOUBLE PRECISION;

-- AlterTable
ALTER TABLE "ResponseInstance" ADD COLUMN     "clarityScore" DOUBLE PRECISION,
ADD COLUMN     "communicationScore" DOUBLE PRECISION,
ADD COLUMN     "confidenceScore" DOUBLE PRECISION,
ADD COLUMN     "depthScore" DOUBLE PRECISION,
ADD COLUMN     "evaluationExplanation" TEXT,
ADD COLUMN     "overallScore" DOUBLE PRECISION,
ADD COLUMN     "structureScore" DOUBLE PRECISION,
ADD COLUMN     "technicalScore" DOUBLE PRECISION,
ALTER COLUMN "hesitationScore" DROP NOT NULL;
