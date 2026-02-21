-- CreateIndex
CREATE INDEX "EvaluationJob_status_nextRetryAt_createdAt_idx" ON "EvaluationJob"("status", "nextRetryAt", "createdAt");

-- CreateIndex
CREATE INDEX "EvaluationJob_status_evaluationStartedAt_idx" ON "EvaluationJob"("status", "evaluationStartedAt");

-- CreateIndex
CREATE INDEX "EvaluationReport_createdAt_idx" ON "EvaluationReport"("createdAt");

-- CreateIndex
CREATE INDEX "EvaluationReport_modelUsed_createdAt_idx" ON "EvaluationReport"("modelUsed", "createdAt");

-- CreateIndex
CREATE INDEX "InterviewSession_userId_status_deletedAt_idx" ON "InterviewSession"("userId", "status", "deletedAt");

-- CreateIndex
CREATE INDEX "InterviewSession_userId_createdAt_idx" ON "InterviewSession"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "InterviewSession_topicId_userId_idx" ON "InterviewSession"("topicId", "userId");

-- CreateIndex
CREATE INDEX "OtpCode_identifier_isUsed_expiresAt_idx" ON "OtpCode"("identifier", "isUsed", "expiresAt");

-- CreateIndex
CREATE INDEX "QuestionBank_topicId_difficulty_deletedAt_idx" ON "QuestionBank"("topicId", "difficulty", "deletedAt");

-- CreateIndex
CREATE INDEX "QuestionBank_source_topicId_idx" ON "QuestionBank"("source", "topicId");

-- CreateIndex
CREATE INDEX "QuestionInstance_sessionId_sequenceOrder_deletedAt_idx" ON "QuestionInstance"("sessionId", "sequenceOrder", "deletedAt");

-- CreateIndex
CREATE INDEX "ResponseInstance_questionId_overallScore_idx" ON "ResponseInstance"("questionId", "overallScore");

-- CreateIndex
CREATE INDEX "Topic_isGlobal_deletedAt_idx" ON "Topic"("isGlobal", "deletedAt");

-- CreateIndex
CREATE INDEX "Topic_createdByUserId_deletedAt_idx" ON "Topic"("createdByUserId", "deletedAt");

-- CreateIndex
CREATE INDEX "User_deletedAt_idx" ON "User"("deletedAt");

-- CreateIndex
CREATE INDEX "UserContextInput_userId_createdAt_idx" ON "UserContextInput"("userId", "createdAt");
