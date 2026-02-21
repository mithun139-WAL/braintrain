/*
  Warnings:

  - A unique constraint covering the columns `[questionId]` on the table `ResponseInstance` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "ResponseInstance_questionId_key" ON "ResponseInstance"("questionId");
