import asyncio
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.knowledge.service import KnowledgeDocumentService
from app.db.models.interview_journey import InterviewJourney

class MockScalarResult:
    def __init__(self, data):
        self._data = data

    def all(self):
        return self._data

    def first(self):
        return self._data[0] if self._data else None

class MockExecuteResult:
    def __init__(self, data):
        self._data = data

    def scalars(self):
        return MockScalarResult(self._data)

class MockAsyncSession:
    def __init__(self, journeys: List[InterviewJourney] = None):
        self.journeys = journeys or []
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def execute(self, stmt):
        # Very basic mock routing for tests
        return MockExecuteResult(self.journeys)

async def run_tests():
    print("=== Running Job Analyzer Service Tests ===")

    # Setup mock data
    journey_id = uuid.uuid4()
    mock_journey = InterviewJourney(
        id=journey_id,
        user_id=uuid.uuid4(),
        role_title="Senior React Developer",
        job_description="We need a Senior React Developer who knows TypeScript and Tailwind CSS.",
        resume_text="Experienced dev.",
        company_name="Acme Inc",
        status="CREATED"
    )

    mock_db = MockAsyncSession([mock_journey])

    # Test 1: Similar journeys lookup
    print("\n[Test 1] Testing get_similar_journeys...")
    similar = await KnowledgeDocumentService.get_similar_journeys(mock_db, "React Developer")
    assert len(similar) >= 1, "Expected to find at least one similar journey"
    assert similar[0].role_title == "Senior React Developer", f"Expected Senior React Developer, got {similar[0].role_title}"
    print("✓ get_similar_journeys passed.")

    # Test 2: Job role analysis (Stub fallback)
    print("\n[Test 2] Testing analyze_job_skills...")
    result = await KnowledgeDocumentService.analyze_job_skills(
        mock_db,
        role_title="Full Stack Python/React Developer",
        job_description="We want someone who knows django, postgres, react, and tailwind css."
    )
    
    assert result["input_role_title"] == "Full Stack Python/React Developer"
    assert "React" in result["common_skills"]
    assert "Python" in result["common_skills"]
    assert "Tailwind CSS" in result["unique_skills"]
    assert len(result["similar_roles_compared"]) == 1
    assert result["similar_roles_compared"][0]["role_title"] == "Senior React Developer"
    print("✓ analyze_job_skills passed.")

    print("\n=== All Job Analyzer Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
