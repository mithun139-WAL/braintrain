import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.knowledge.service_optimizer import CareerOptimizerService
from app.db.models.career_profile import CareerProfile

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
    def __init__(self, profiles: list = None):
        self.profiles = profiles or []
        self.added = []
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass

    async def execute(self, stmt):
        return MockExecuteResult(self.profiles)

async def run_tests():
    print("=== Running Career Optimizer Service Tests ===")

    # Test 1: Test Target Role Intelligence (standard roles)
    print("\n[Test 1] Testing target role profiles...")
    profile = await CareerOptimizerService._get_target_role_profile("Applied AI Engineer")
    assert "FastAPI" in profile["required"], "Expected FastAPI in required list for Applied AI Engineer"
    assert "Vector DB" in profile["required"], "Expected Vector DB in required list for Applied AI Engineer"
    assert "AI Agents" in profile["preferred"], "Expected AI Agents in preferred list for Applied AI Engineer"
    print("✓ target role profile mapping passed.")

    # Test 2: Hybrid Evaluation (Rule Engine + Stub fallback)
    print("\n[Test 2] Testing hybrid evaluation...")
    extracted_data = {
        "experience": [{"title": "Software Engineer", "company": "BrainTrain", "details": ["Built features scaling users by 40%"]}],
        "skills": ["Python", "FastAPI"],
        "projects": [{"name": "AI App", "details": ["Used RAG"]}],
        "education": [{"text": "B.Tech"}],
        "certifications": [],
        "headlines": ["Software Engineer"],
        "summaries": ["Developer transition to AI"],
        "technologies": ["Python", "FastAPI"],
        "career_progression": "Developer"
    }
    
    target_profile = {
        "required": ["Python", "FastAPI", "RAG"],
        "preferred": ["Vector DB"]
    }
    
    evaluation = await CareerOptimizerService._evaluate_profile_hybrid(
        current_role="Software Engineer",
        target_role="Applied AI Engineer",
        extracted=extracted_data,
        target_profile=target_profile
    )
    
    assert "scores" in evaluation
    assert evaluation["scores"]["career_score"] > 0
    assert evaluation["scores"]["role_alignment_score"] > 0
    assert "gap_analysis" in evaluation
    assert "roadmap" in evaluation
    assert "generated_content" in evaluation
    
    # Check that missing required skills are detected
    assert "RAG" in evaluation["generated_content"]["skills_suggestions"]["missing_skills"]
    print("✓ hybrid evaluation passed.")

    # Test 3: optimize_profile integration with mock DB
    print("\n[Test 3] Testing optimize_profile integration...")
    mock_db = MockAsyncSession()
    user_id = uuid.uuid4()
    
    result = await CareerOptimizerService.optimize_profile(
        db=mock_db,
        user_id=user_id,
        current_role="Software Engineer",
        target_role="Applied AI Engineer",
        resume_bytes=b"Resume content text with Python and FastAPI skills.",
        resume_filename="resume.pdf"
    )
    
    assert len(mock_db.added) == 1
    profile_record = mock_db.added[0]
    assert isinstance(profile_record, CareerProfile)
    assert profile_record.user_id == user_id
    assert profile_record.current_role == "Software Engineer"
    assert profile_record.target_role == "Applied AI Engineer"
    assert profile_record.resume_filename == "resume.pdf"
    assert profile_record.resume_content is not None
    print("✓ optimize_profile integration passed.")

    print("\n=== All Career Optimizer Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
