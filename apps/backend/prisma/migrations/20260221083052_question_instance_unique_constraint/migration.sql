/*
  Warnings:

  - A unique constraint covering the columns `[sessionId,sequenceOrder]` on the table `QuestionInstance` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "QuestionInstance_sessionId_sequenceOrder_key" ON "QuestionInstance"("sessionId", "sequenceOrder");
