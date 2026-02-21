-- AlterTable
ALTER TABLE "OtpCode" ADD COLUMN     "attemptCount" INTEGER NOT NULL DEFAULT 0;

-- CreateIndex
CREATE INDEX "OtpCode_identifier_idx" ON "OtpCode"("identifier");
