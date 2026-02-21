/*
  Warnings:

  - A unique constraint covering the columns `[name,isGlobal]` on the table `Topic` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "Topic_name_isGlobal_key" ON "Topic"("name", "isGlobal");
