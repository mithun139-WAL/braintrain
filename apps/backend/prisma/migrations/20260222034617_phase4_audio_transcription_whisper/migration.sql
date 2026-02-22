-- CreateEnum
CREATE TYPE "AudioProcessingStatus" AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'SKIPPED');

-- AlterTable
ALTER TABLE "ResponseInstance" ADD COLUMN     "audioDurationSeconds" DOUBLE PRECISION,
ADD COLUMN     "audioProcessingStatus" "AudioProcessingStatus" NOT NULL DEFAULT 'SKIPPED',
ADD COLUMN     "transcribedText" TEXT;

-- CreateIndex
CREATE INDEX "ResponseInstance_audioProcessingStatus_createdAt_idx" ON "ResponseInstance"("audioProcessingStatus", "createdAt");
