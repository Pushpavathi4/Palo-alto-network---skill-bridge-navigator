"""
Skill-Bridge Career Navigator — Flask Application.
Provides API endpoints and serves the web UI.
"""

import json
import os
from flask import Flask, render_template, request, jsonify

from ai_engine import (
    extract_skills,
    analyze_gap,
    generate_roadmap,
    generate_interview,
    get_skill_category,
)

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_job_descriptions():
    return load_json("job_descriptions.json")


def get_sample_resumes():
    return load_json("sample_resumes.json")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/roles", methods=["GET"])
def list_roles():
    """Return distinct role titles from job descriptions."""
    jds = get_job_descriptions()
    roles = sorted(set(jd["title"] for jd in jds))
    return jsonify({"roles": roles})


@app.route("/api/sample-resumes", methods=["GET"])
def list_sample_resumes():
    """Return sample resumes for quick demo."""
    resumes = get_sample_resumes()
    return jsonify({"resumes": resumes})


@app.route("/api/extract-skills", methods=["POST"])
def api_extract_skills():
    """Extract skills from resume text."""
    data = request.get_json()
    if not data or not data.get("resume_text", "").strip():
        return jsonify({"error": "resume_text is required and cannot be empty."}), 400

    resume_text = data["resume_text"].strip()
    if len(resume_text) < 20:
        return jsonify({"error": "Resume text is too short. Please provide more detail."}), 400

    result = extract_skills(resume_text)
    categorized = {}
    for skill in result["skills"]:
        cat = get_skill_category(skill)
        categorized.setdefault(cat, []).append(skill)

    return jsonify({
        "skills": result["skills"],
        "method": result["method"],
        "categorized": categorized,
    })


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """Run gap analysis: compare user skills against jobs for a target role."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    user_skills = data.get("skills", [])
    target_role = data.get("target_role", "").strip()

    if not user_skills:
        return jsonify({"error": "skills list is required."}), 400
    if not target_role:
        return jsonify({"error": "target_role is required."}), 400

    jds = get_job_descriptions()
    filtered = [jd for jd in jds if jd["title"].lower() == target_role.lower()]

    if not filtered:
        return jsonify({"error": f"No job descriptions found for role: {target_role}"}), 404

    gap_results = analyze_gap(user_skills, filtered)
    return jsonify({"analysis": gap_results, "target_role": target_role})


@app.route("/api/roadmap", methods=["POST"])
def api_roadmap():
    """Generate a learning roadmap for missing skills."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    missing_skills = data.get("missing_skills", [])
    target_role = data.get("target_role", "").strip()

    if not target_role:
        return jsonify({"error": "target_role is required."}), 400
    if not missing_skills:
        return jsonify({"roadmap": [], "method": "none", "message": "No missing skills — you're a perfect match!"})

    result = generate_roadmap(missing_skills, target_role)
    return jsonify(result)


@app.route("/api/search-jobs", methods=["GET"])
def search_jobs():
    """Search/filter job descriptions by title or skill."""
    query = request.args.get("q", "").strip().lower()
    jds = get_job_descriptions()

    if not query:
        return jsonify({"jobs": jds})

    filtered = [
        jd for jd in jds
        if query in jd["title"].lower()
        or query in jd["company"].lower()
        or any(query in s.lower() for s in jd["required_skills"])
        or any(query in s.lower() for s in jd["preferred_skills"])
    ]
    return jsonify({"jobs": filtered, "query": query})


@app.route("/api/mock-interview", methods=["POST"])
def api_mock_interview():
    """Generate mock interview questions based on user skills."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    skills = data.get("skills", [])
    target_role = data.get("target_role", "").strip()
    num_questions = data.get("num_questions", 5)

    if not skills:
        return jsonify({"error": "skills list is required."}), 400
    if not target_role:
        return jsonify({"error": "target_role is required."}), 400

    if not isinstance(num_questions, int) or num_questions < 1:
        num_questions = 5
    num_questions = min(num_questions, 15)

    result = generate_interview(skills, target_role, num_questions)
    return jsonify(result)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.run(debug=True, port=5000)
