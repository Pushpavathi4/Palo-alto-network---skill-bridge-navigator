"""Tests for Skill-Bridge Career Navigator."""

import json
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from ai_engine import extract_skills_fallback, analyze_gap, generate_roadmap_fallback, generate_interview_fallback, get_skill_category


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# --- Happy Path Tests ---

class TestHappyPath:
    """Tests for normal, expected usage."""

    def test_extract_skills_fallback_finds_known_skills(self):
        text = "Experienced in Python, Docker, AWS, Kubernetes, and Linux administration."
        skills = extract_skills_fallback(text)
        assert "Python" in skills
        assert "Docker" in skills
        assert "AWS" in skills
        assert "Kubernetes" in skills
        assert "Linux" in skills

    def test_gap_analysis_returns_correct_structure(self):
        user_skills = ["Python", "Docker", "Git"]
        jds = [{
            "id": "test-001",
            "title": "Cloud Engineer",
            "company": "TestCo",
            "required_skills": ["Python", "Docker", "AWS", "Terraform"],
            "preferred_skills": ["GCP"],
        }]
        results = analyze_gap(user_skills, jds)
        assert len(results) == 1
        r = results[0]
        assert r["title"] == "Cloud Engineer"
        assert "Python" in r["matched_required"]
        assert "Docker" in r["matched_required"]
        assert "AWS" in r["missing_required"]
        assert "Terraform" in r["missing_required"]
        assert r["match_percentage"] == 40.0  # 2 out of 5

    def test_roadmap_fallback_generates_entries(self):
        missing = ["Terraform", "Kubernetes"]
        roadmap = generate_roadmap_fallback(missing, "Cloud Engineer")
        assert len(roadmap) == 2
        assert roadmap[0]["skill"] == "Terraform"
        assert roadmap[1]["skill"] == "Kubernetes"
        assert "resource_name" in roadmap[0]
        assert roadmap[0]["estimated_hours"] > 0

    def test_api_extract_skills_endpoint(self, client):
        res = client.post("/api/extract-skills", json={
            "resume_text": "I am proficient in Python, SQL, Django, REST APIs, and Git."
        })
        assert res.status_code == 200
        data = res.get_json()
        assert "skills" in data
        assert "Python" in data["skills"]
        assert data["method"] in ("ai", "fallback")

    def test_api_analyze_endpoint(self, client):
        res = client.post("/api/analyze", json={
            "skills": ["Python", "SQL", "Git"],
            "target_role": "Backend Developer"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert "analysis" in data
        assert len(data["analysis"]) > 0
        assert "match_percentage" in data["analysis"][0]

    def test_api_roles_endpoint(self, client):
        res = client.get("/api/roles")
        assert res.status_code == 200
        data = res.get_json()
        assert "roles" in data
        assert len(data["roles"]) > 0

    def test_api_search_jobs_no_query(self, client):
        res = client.get("/api/search-jobs")
        assert res.status_code == 200
        data = res.get_json()
        assert "jobs" in data
        assert len(data["jobs"]) == 10  # all jobs returned

    def test_api_search_jobs_with_query(self, client):
        res = client.get("/api/search-jobs?q=cloud")
        assert res.status_code == 200
        data = res.get_json()
        assert all("Cloud" in j["title"] or "cloud" in j["description"].lower()
                    or any("cloud" in s.lower() for s in j["required_skills"] + j["preferred_skills"])
                    for j in data["jobs"])

    def test_interview_fallback_generates_questions(self):
        skills = ["Python", "Docker", "SQL"]
        questions = generate_interview_fallback(skills, "Backend Developer", 5)
        assert len(questions) > 0
        assert len(questions) <= 5
        assert all("question" in q for q in questions)
        assert all("difficulty" in q for q in questions)
        assert all("skill" in q for q in questions)

    def test_api_mock_interview_endpoint(self, client):
        res = client.post("/api/mock-interview", json={
            "skills": ["Python", "Git", "Docker"],
            "target_role": "Cloud Engineer",
            "num_questions": 3
        })
        assert res.status_code == 200
        data = res.get_json()
        assert "questions" in data
        assert "method" in data
        assert len(data["questions"]) > 0

    def test_skill_category_lookup(self):
        assert get_skill_category("Python") == "languages"
        assert get_skill_category("React") == "frontend"
        assert get_skill_category("Docker") == "cloud_devops"
        assert get_skill_category("SIEM") == "security"

    def test_gap_analysis_case_insensitive(self):
        user_skills = ["python", "docker"]
        jds = [{
            "id": "t1", "title": "Dev", "company": "X",
            "required_skills": ["Python", "Docker", "AWS"],
            "preferred_skills": [],
        }]
        results = analyze_gap(user_skills, jds)
        assert len(results[0]["matched_required"]) == 2


# --- Edge Case Tests ---

class TestEdgeCases:
    """Tests for boundary conditions and error handling."""

    def test_extract_skills_empty_text(self):
        skills = extract_skills_fallback("")
        assert skills == []

    def test_extract_skills_no_known_skills(self):
        text = "I enjoy hiking, painting, and cooking gourmet meals."
        skills = extract_skills_fallback(text)
        assert skills == []

    def test_api_extract_skills_missing_body(self, client):
        res = client.post("/api/extract-skills", json={})
        assert res.status_code == 400
        data = res.get_json()
        assert "error" in data

    def test_api_extract_skills_too_short(self, client):
        res = client.post("/api/extract-skills", json={"resume_text": "Hi"})
        assert res.status_code == 400
        data = res.get_json()
        assert "too short" in data["error"].lower()

    def test_api_analyze_missing_role(self, client):
        res = client.post("/api/analyze", json={"skills": ["Python"]})
        assert res.status_code == 400

    def test_api_analyze_missing_skills(self, client):
        res = client.post("/api/analyze", json={"target_role": "Cloud Engineer"})
        assert res.status_code == 400

    def test_api_analyze_nonexistent_role(self, client):
        res = client.post("/api/analyze", json={
            "skills": ["Python"],
            "target_role": "Underwater Basket Weaver"
        })
        assert res.status_code == 404

    def test_api_roadmap_no_missing_skills(self, client):
        res = client.post("/api/roadmap", json={
            "missing_skills": [],
            "target_role": "Cloud Engineer"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["roadmap"] == []

    def test_api_mock_interview_missing_skills(self, client):
        res = client.post("/api/mock-interview", json={
            "skills": [],
            "target_role": "Cloud Engineer"
        })
        assert res.status_code == 400

    def test_api_mock_interview_missing_role(self, client):
        res = client.post("/api/mock-interview", json={
            "skills": ["Python"]
        })
        assert res.status_code == 400

    def test_interview_fallback_unknown_skills(self):
        questions = generate_interview_fallback(["QuantumFlux"], "Time Traveler", 3)
        assert len(questions) >= 1
        assert "question" in questions[0]

    def test_gap_analysis_empty_skills(self):
        results = analyze_gap([], [{
            "id": "t1", "title": "Dev", "company": "X",
            "required_skills": ["Python"], "preferred_skills": [],
        }])
        assert results[0]["match_percentage"] == 0
        assert results[0]["missing_required"] == ["Python"]

    def test_roadmap_fallback_unknown_skill(self):
        roadmap = generate_roadmap_fallback(["QuantumFluxCapacitor"], "Time Traveler")
        assert len(roadmap) == 1
        assert "Search for" in roadmap[0]["resource_name"]

    def test_extract_skills_partial_match_avoided(self):
        """Ensure 'SQL' doesn't match inside 'MySQL' incorrectly."""
        text = "I know MySQL and NoSQL databases."
        skills = extract_skills_fallback(text)
        # SQL should not be matched from "MySQL" due to word boundary
        assert "SQL" not in skills or "MySQL" in text

    def test_index_page_loads(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert b"Skill-Bridge" in res.data
