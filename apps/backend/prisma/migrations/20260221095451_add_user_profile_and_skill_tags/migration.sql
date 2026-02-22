-- AlterTable
ALTER TABLE "User" ADD COLUMN     "avatarUrl" TEXT,
ADD COLUMN     "bio" TEXT,
ADD COLUMN     "displayName" TEXT;

-- CreateTable
CREATE TABLE "SkillTag" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "isGlobal" BOOLEAN NOT NULL DEFAULT false,
    "createdByUserId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SkillTag_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "UserSkillPreference" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "skillTagId" TEXT NOT NULL,
    "level" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "UserSkillPreference_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "SkillTag_name_key" ON "SkillTag"("name");

-- CreateIndex
CREATE UNIQUE INDEX "UserSkillPreference_userId_skillTagId_key" ON "UserSkillPreference"("userId", "skillTagId");

-- AddForeignKey
ALTER TABLE "UserSkillPreference" ADD CONSTRAINT "UserSkillPreference_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "UserSkillPreference" ADD CONSTRAINT "UserSkillPreference_skillTagId_fkey" FOREIGN KEY ("skillTagId") REFERENCES "SkillTag"("id") ON DELETE CASCADE ON UPDATE CASCADE;
