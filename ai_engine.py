"""
AI Engine for Skill-Bridge Career Navigator.
Handles skill extraction, gap analysis, and roadmap generation.
Provides rule-based fallback when AI is unavailable.
"""

import json
import os
import re
from collections import Counter

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

SKILLS_TAXONOMY = {
    "languages": ["Python", "Java", "JavaScript", "TypeScript", "C++", "C", "Go", "Rust", "Ruby", "PHP", "Bash", "R", "Scala", "Kotlin", "Swift", "SQL"],
    "frontend": ["React", "Vue.js", "Angular", "HTML", "CSS", "SASS", "Tailwind CSS", "Next.js", "Nuxt.js", "Webpack", "Responsive Design", "Figma", "Storybook", "Jest", "Cypress"],
    "backend": ["Django", "Flask", "Spring Boot", "Node.js", "Express", "FastAPI", "REST APIs", "GraphQL", "Microservices", "Redis", "Celery", "RabbitMQ", "Kafka", "Maven"],
    "data": ["Pandas", "NumPy", "Matplotlib", "Scikit-learn", "TensorFlow", "PyTorch", "Machine Learning", "Data Visualization", "Statistics", "Data Preprocessing", "Jupyter", "Excel", "Tableau", "Power BI", "ETL", "dbt", "Airflow", "MLflow", "NLP"],
    "cloud_devops": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Git", "Ansible", "Jenkins", "ArgoCD", "Prometheus", "Grafana", "Helm", "CloudFormation", "ARM Templates", "Datadog", "Monitoring", "AWS SageMaker"],
    "security": ["Network Security", "SIEM", "Incident Response", "Firewalls", "Vulnerability Assessment", "TCP/IP", "Log Analysis", "Risk Assessment", "Splunk", "Wireshark", "Penetration Testing", "Cloud Security", "SOAR", "IAM", "Networking"],
    "general": ["Unit Testing", "Git", "MongoDB", "PostgreSQL", "SQL", "Docker", "Linux"]
}

ALL_KNOWN_SKILLS = set()
for skills in SKILLS_TAXONOMY.values():
    ALL_KNOWN_SKILLS.update(s.lower() for s in skills)

LEARNING_RESOURCES = {
    "AWS": {"course": "AWS Cloud Practitioner Essentials (AWS Free)", "url": "https://aws.amazon.com/training/", "hours": 6},
    "Azure": {"course": "Microsoft Azure Fundamentals (Microsoft Learn)", "url": "https://learn.microsoft.com/en-us/training/", "hours": 8},
    "GCP": {"course": "Google Cloud Fundamentals (Coursera)", "url": "https://www.coursera.org/", "hours": 8},
    "Docker": {"course": "Docker for Beginners (Docker Docs)", "url": "https://docs.docker.com/get-started/", "hours": 4},
    "Kubernetes": {"course": "Kubernetes Basics (kubernetes.io)", "url": "https://kubernetes.io/docs/tutorials/", "hours": 10},
    "Terraform": {"course": "HashiCorp Terraform Associate Prep (HashiCorp Learn)", "url": "https://learn.hashicorp.com/terraform", "hours": 12},
    "CI/CD": {"course": "GitHub Actions Tutorial (GitHub Docs)", "url": "https://docs.github.com/en/actions", "hours": 4},
    "Python": {"course": "Python for Everybody (Coursera - Free)", "url": "https://www.coursera.org/", "hours": 20},
    "Java": {"course": "Java Programming MOOC (University of Helsinki)", "url": "https://java-programming.mooc.fi/", "hours": 40},
    "JavaScript": {"course": "The Odin Project - JavaScript", "url": "https://www.theodinproject.com/", "hours": 30},
    "TypeScript": {"course": "TypeScript Handbook (Official Docs)", "url": "https://www.typescriptlang.org/docs/", "hours": 8},
    "React": {"course": "React Official Tutorial", "url": "https://react.dev/learn", "hours": 10},
    "Vue.js": {"course": "Vue.js Official Guide", "url": "https://vuejs.org/guide/", "hours": 8},
    "Django": {"course": "Django Official Tutorial", "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "hours": 8},
    "Flask": {"course": "Flask Mega-Tutorial (Miguel Grinberg)", "url": "https://blog.miguelgrinberg.com/", "hours": 10},
    "Spring Boot": {"course": "Spring Boot Guides (spring.io)", "url": "https://spring.io/guides", "hours": 12},
    "PostgreSQL": {"course": "PostgreSQL Tutorial (postgresqltutorial.com)", "url": "https://www.postgresqltutorial.com/", "hours": 6},
    "SQL": {"course": "SQLBolt Interactive Tutorial", "url": "https://sqlbolt.com/", "hours": 4},
    "REST APIs": {"course": "RESTful API Design (Restful API Tutorial)", "url": "https://restfulapi.net/", "hours": 3},
    "Git": {"course": "Git Branching Interactive (learngitbranching.js.org)", "url": "https://learngitbranching.js.org/", "hours": 3},
    "Linux": {"course": "Linux Journey (linuxjourney.com)", "url": "https://linuxjourney.com/", "hours": 10},
    "Pandas": {"course": "Kaggle Pandas Course (Free)", "url": "https://www.kaggle.com/learn/pandas", "hours": 4},
    "NumPy": {"course": "NumPy Quickstart (numpy.org)", "url": "https://numpy.org/doc/stable/user/quickstart.html", "hours": 3},
    "Machine Learning": {"course": "Andrew Ng ML Course (Coursera)", "url": "https://www.coursera.org/", "hours": 40},
    "TensorFlow": {"course": "TensorFlow Tutorials (tensorflow.org)", "url": "https://www.tensorflow.org/tutorials", "hours": 15},
    "Scikit-learn": {"course": "Scikit-learn Tutorials (Official)", "url": "https://scikit-learn.org/stable/tutorial/", "hours": 8},
    "Statistics": {"course": "Khan Academy Statistics (Free)", "url": "https://www.khanacademy.org/math/statistics-probability", "hours": 15},
    "Data Visualization": {"course": "Kaggle Data Visualization Course", "url": "https://www.kaggle.com/learn/data-visualization", "hours": 4},
    "Tableau": {"course": "Tableau Free Training Videos", "url": "https://www.tableau.com/learn/training", "hours": 8},
    "Network Security": {"course": "Cybersecurity Fundamentals (edX)", "url": "https://www.edx.org/", "hours": 15},
    "SIEM": {"course": "Splunk Fundamentals 1 (Free)", "url": "https://www.splunk.com/en_us/training.html", "hours": 10},
    "Incident Response": {"course": "SANS Incident Response Overview", "url": "https://www.sans.org/", "hours": 8},
    "Firewalls": {"course": "Network Security Basics (Cisco NetAcad)", "url": "https://www.netacad.com/", "hours": 6},
    "Vulnerability Assessment": {"course": "Nessus Essentials Training", "url": "https://www.tenable.com/", "hours": 5},
    "Networking": {"course": "Cisco Networking Basics (NetAcad)", "url": "https://www.netacad.com/", "hours": 12},
    "TCP/IP": {"course": "TCP/IP Fundamentals (Pluralsight)", "url": "https://www.pluralsight.com/", "hours": 6},
    "Monitoring": {"course": "Prometheus & Grafana Tutorial", "url": "https://prometheus.io/docs/", "hours": 6},
    "Unit Testing": {"course": "Python Testing with pytest (Real Python)", "url": "https://realpython.com/pytest-python-testing/", "hours": 4},
    "Microservices": {"course": "Microservices with Spring Boot (Baeldung)", "url": "https://www.baeldung.com/", "hours": 10},
    "Redis": {"course": "Redis University (Free)", "url": "https://university.redis.com/", "hours": 6},
    "Bash": {"course": "Bash Scripting Tutorial (linuxconfig.org)", "url": "https://linuxconfig.org/bash-scripting-tutorial", "hours": 5},
    "HTML": {"course": "MDN HTML Basics", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "hours": 4},
    "CSS": {"course": "MDN CSS Basics", "url": "https://developer.mozilla.org/en-US/docs/Learn/CSS", "hours": 6},
    "Responsive Design": {"course": "freeCodeCamp Responsive Web Design", "url": "https://www.freecodecamp.org/", "hours": 10},
    "Webpack": {"course": "Webpack Official Guides", "url": "https://webpack.js.org/guides/", "hours": 4},
    "IAM": {"course": "AWS IAM Tutorial (AWS Docs)", "url": "https://docs.aws.amazon.com/IAM/", "hours": 4},
    "CloudFormation": {"course": "AWS CloudFormation Workshop", "url": "https://cfn101.solution.builders/", "hours": 6},
    "Log Analysis": {"course": "ELK Stack Tutorial (Elastic)", "url": "https://www.elastic.co/guide/", "hours": 8},
    "Risk Assessment": {"course": "NIST Risk Management Framework Overview", "url": "https://csrc.nist.gov/", "hours": 5},
    "ETL": {"course": "ETL with Python (Real Python)", "url": "https://realpython.com/", "hours": 6},
    "Data Preprocessing": {"course": "Kaggle Data Cleaning Course", "url": "https://www.kaggle.com/learn/data-cleaning", "hours": 4},
    "Jupyter": {"course": "Jupyter Notebook Tutorial (DataCamp)", "url": "https://www.datacamp.com/", "hours": 2},
    "Excel": {"course": "Excel Skills for Business (Coursera)", "url": "https://www.coursera.org/", "hours": 10},
    "MongoDB": {"course": "MongoDB University (Free)", "url": "https://university.mongodb.com/", "hours": 8},
    "Node.js": {"course": "The Odin Project - NodeJS", "url": "https://www.theodinproject.com/", "hours": 20},
    "GraphQL": {"course": "How to GraphQL (howtographql.com)", "url": "https://www.howtographql.com/", "hours": 6},
    "SASS": {"course": "Sass Official Guide", "url": "https://sass-lang.com/guide", "hours": 3},
    "Jest": {"course": "Jest Official Getting Started", "url": "https://jestjs.io/docs/getting-started", "hours": 3},
}


def _get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not GROQ_AVAILABLE:
        return None
    try:
        return Groq(api_key=api_key)
    except Exception:
        return None


def extract_skills_with_ai(resume_text):
    """Use Groq (Llama 3) to extract skills from resume text."""
    client = _get_groq_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a resume parser. Extract technical skills from the resume text. Return ONLY a JSON array of skill strings, nothing else. Example: [\"Python\", \"AWS\", \"Docker\"]"},
                {"role": "user", "content": f"Extract all technical skills from this resume:\n\n{resume_text}"}
            ],
            temperature=0.1,
            max_tokens=500
        )
        content = response.choices[0].message.content.strip()
        skills = json.loads(content)
        if isinstance(skills, list) and all(isinstance(s, str) for s in skills):
            return skills
        return None
    except Exception:
        return None


def extract_skills_fallback(resume_text):
    """Rule-based fallback: match resume text against known skills taxonomy."""
    text_lower = resume_text.lower()
    found = []
    for category_skills in SKILLS_TAXONOMY.values():
        for skill in category_skills:
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                if skill not in found:
                    found.append(skill)
    return found


def extract_skills(resume_text):
    """Extract skills with AI, falling back to rule-based if AI fails."""
    ai_skills = extract_skills_with_ai(resume_text)
    if ai_skills:
        return {"skills": ai_skills, "method": "ai"}
    fallback_skills = extract_skills_fallback(resume_text)
    return {"skills": fallback_skills, "method": "fallback"}


def analyze_gap(user_skills, job_descriptions):
    """Compare user skills against job descriptions and return gap analysis."""
    user_skills_lower = {s.lower() for s in user_skills}

    results = []
    for jd in job_descriptions:
        required = jd.get("required_skills", [])
        preferred = jd.get("preferred_skills", [])

        matched_required = [s for s in required if s.lower() in user_skills_lower]
        missing_required = [s for s in required if s.lower() not in user_skills_lower]
        matched_preferred = [s for s in preferred if s.lower() in user_skills_lower]
        missing_preferred = [s for s in preferred if s.lower() not in user_skills_lower]

        total = len(required) + len(preferred)
        matched_total = len(matched_required) + len(matched_preferred)
        match_pct = round((matched_total / total * 100) if total > 0 else 0, 1)

        results.append({
            "job_id": jd["id"],
            "title": jd["title"],
            "company": jd["company"],
            "match_percentage": match_pct,
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_preferred": matched_preferred,
            "missing_preferred": missing_preferred,
        })

    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results


def generate_roadmap_with_ai(missing_skills, target_role, skill_demand):
    """Use Groq (Llama 3) to generate a prioritized learning roadmap."""
    client = _get_groq_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "You are a senior career advisor. Given missing skills for a target role, generate a prioritized learning roadmap. "
                    "Prioritize skills that are REQUIRED over PREFERRED, and skills demanded by MORE job postings over fewer. "
                    "Return ONLY a JSON array of objects with keys: "
                    "skill, priority (1=highest), urgency (critical/important/nice-to-have), "
                    "reason (explain WHY this priority — e.g. 'Required by 2/2 job postings and is a core skill for this role'), "
                    "resource_name, resource_url, estimated_hours. Order by priority (1 first)."
                )},
                {"role": "user", "content": (
                    f"Target role: {target_role}\n"
                    f"Missing skills with demand data: {json.dumps(skill_demand)}\n\n"
                    f"Generate a learning roadmap."
                )}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        roadmap = json.loads(content)
        if isinstance(roadmap, list):
            return roadmap
        return None
    except Exception:
        return None


def generate_roadmap_fallback(missing_skills, target_role, skill_demand=None):
    """Rule-based fallback: build roadmap from predefined resources, sorted by importance."""
    if skill_demand is None:
        skill_demand = {s: {"required_count": 0, "preferred_count": 0, "total_jds": 1} for s in missing_skills}

    scored = []
    for skill in missing_skills:
        demand = skill_demand.get(skill, {"required_count": 0, "preferred_count": 0, "total_jds": 1})
        req_count = demand.get("required_count", 0)
        pref_count = demand.get("preferred_count", 0)
        total_jds = demand.get("total_jds", 1)

        # Score: required skills weighted 3x, preferred 1x, multiplied by frequency
        score = (req_count * 3) + (pref_count * 1)

        if req_count > 0:
            urgency = "critical"
            if req_count >= total_jds:
                reason = f"Required by ALL {total_jds} {target_role} job postings — this is a must-have skill. Learn this first."
            else:
                reason = f"Required by {req_count}/{total_jds} {target_role} postings — highly important for this role."
        elif pref_count > 0:
            if pref_count >= total_jds:
                urgency = "important"
                reason = f"Preferred by ALL {total_jds} {target_role} postings — will make you stand out from other candidates."
            else:
                urgency = "nice-to-have"
                reason = f"Preferred by {pref_count}/{total_jds} {target_role} postings — a bonus that strengthens your profile."
        else:
            urgency = "nice-to-have"
            reason = f"Listed in {target_role} job descriptions — good to have for a well-rounded profile."
            score = 0

        scored.append({
            "skill": skill,
            "score": score,
            "urgency": urgency,
            "reason": reason,
            "req_count": req_count,
            "pref_count": pref_count,
        })

    # Sort: critical first, then important, then nice-to-have; within same urgency, by score desc
    urgency_order = {"critical": 0, "important": 1, "nice-to-have": 2}
    scored.sort(key=lambda x: (urgency_order.get(x["urgency"], 3), -x["score"]))

    roadmap = []
    for i, item in enumerate(scored):
        resource = LEARNING_RESOURCES.get(item["skill"])
        if resource:
            roadmap.append({
                "skill": item["skill"],
                "priority": i + 1,
                "urgency": item["urgency"],
                "reason": item["reason"],
                "resource_name": resource["course"],
                "resource_url": resource["url"],
                "estimated_hours": resource["hours"]
            })
        else:
            roadmap.append({
                "skill": item["skill"],
                "priority": i + 1,
                "urgency": item["urgency"],
                "reason": item["reason"],
                "resource_name": f"Search for '{item['skill']} tutorial' on YouTube or Coursera",
                "resource_url": "https://www.coursera.org/",
                "estimated_hours": 8
            })
    return roadmap


def _compute_skill_demand(missing_skills, target_role):
    """Count how many JDs require/prefer each missing skill."""
    import os as _os
    data_dir = _os.path.join(_os.path.dirname(__file__), "data")
    jd_path = _os.path.join(data_dir, "job_descriptions.json")
    try:
        with open(jd_path, "r", encoding="utf-8") as f:
            all_jds = json.load(f)
    except Exception:
        all_jds = []

    role_jds = [jd for jd in all_jds if jd["title"].lower() == target_role.lower()]
    total_jds = len(role_jds) or 1

    demand = {}
    for skill in missing_skills:
        skill_lower = skill.lower()
        req_count = sum(1 for jd in role_jds if skill_lower in [s.lower() for s in jd.get("required_skills", [])])
        pref_count = sum(1 for jd in role_jds if skill_lower in [s.lower() for s in jd.get("preferred_skills", [])])
        demand[skill] = {
            "required_count": req_count,
            "preferred_count": pref_count,
            "total_jds": total_jds,
        }
    return demand


def generate_roadmap(missing_skills, target_role):
    """Generate roadmap with AI, falling back to rule-based. Skills are prioritized by demand."""
    if not missing_skills:
        return {"roadmap": [], "method": "none"}

    skill_demand = _compute_skill_demand(missing_skills, target_role)

    ai_roadmap = generate_roadmap_with_ai(missing_skills, target_role, skill_demand)
    if ai_roadmap:
        return {"roadmap": ai_roadmap, "method": "ai"}

    fallback_roadmap = generate_roadmap_fallback(missing_skills, target_role, skill_demand)
    return {"roadmap": fallback_roadmap, "method": "fallback"}


# --- Mock Interview Questions ---

INTERVIEW_QUESTIONS_BANK = {
    "Python": [
        {"question": "What is the difference between a list and a tuple in Python?", "difficulty": "easy", "topic": "Data Structures"},
        {"question": "Explain how Python's garbage collector works.", "difficulty": "medium", "topic": "Memory Management"},
        {"question": "What are decorators in Python and when would you use them?", "difficulty": "medium", "topic": "Language Features"},
    ],
    "Java": [
        {"question": "What is the difference between an abstract class and an interface in Java?", "difficulty": "easy", "topic": "OOP"},
        {"question": "Explain the Java Memory Model and how garbage collection works.", "difficulty": "medium", "topic": "Memory Management"},
        {"question": "What are the differences between HashMap and ConcurrentHashMap?", "difficulty": "medium", "topic": "Collections"},
    ],
    "JavaScript": [
        {"question": "Explain the difference between var, let, and const.", "difficulty": "easy", "topic": "Language Basics"},
        {"question": "What is the event loop in JavaScript and how does it work?", "difficulty": "medium", "topic": "Async Programming"},
        {"question": "Explain closures in JavaScript with an example.", "difficulty": "medium", "topic": "Language Features"},
    ],
    "SQL": [
        {"question": "What is the difference between INNER JOIN and LEFT JOIN?", "difficulty": "easy", "topic": "Joins"},
        {"question": "How would you optimize a slow-running SQL query?", "difficulty": "medium", "topic": "Performance"},
        {"question": "Explain the difference between WHERE and HAVING clauses.", "difficulty": "easy", "topic": "Filtering"},
    ],
    "Docker": [
        {"question": "What is the difference between a Docker image and a container?", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "How would you reduce the size of a Docker image?", "difficulty": "medium", "topic": "Optimization"},
        {"question": "Explain multi-stage builds in Docker and why they are useful.", "difficulty": "medium", "topic": "Best Practices"},
    ],
    "Kubernetes": [
        {"question": "What is a Pod in Kubernetes and how does it differ from a container?", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "Explain the difference between a Deployment and a StatefulSet.", "difficulty": "medium", "topic": "Workloads"},
        {"question": "How does Kubernetes handle service discovery and load balancing?", "difficulty": "medium", "topic": "Networking"},
    ],
    "AWS": [
        {"question": "What is the difference between S3 and EBS storage?", "difficulty": "easy", "topic": "Storage"},
        {"question": "Explain the shared responsibility model in AWS.", "difficulty": "easy", "topic": "Security"},
        {"question": "How would you design a highly available architecture on AWS?", "difficulty": "hard", "topic": "Architecture"},
    ],
    "React": [
        {"question": "What is the Virtual DOM and how does React use it?", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "Explain the difference between useState and useReducer hooks.", "difficulty": "medium", "topic": "State Management"},
        {"question": "How would you optimize a React app that is rendering slowly?", "difficulty": "medium", "topic": "Performance"},
    ],
    "Git": [
        {"question": "What is the difference between git merge and git rebase?", "difficulty": "easy", "topic": "Branching"},
        {"question": "How would you revert a commit that has already been pushed?", "difficulty": "medium", "topic": "Undo Changes"},
        {"question": "Explain the difference between git reset and git revert.", "difficulty": "medium", "topic": "Undo Changes"},
    ],
    "REST APIs": [
        {"question": "What are the main HTTP methods and when would you use each?", "difficulty": "easy", "topic": "HTTP"},
        {"question": "How would you handle API versioning?", "difficulty": "medium", "topic": "Design"},
        {"question": "Explain the difference between authentication and authorization in APIs.", "difficulty": "easy", "topic": "Security"},
    ],
    "Linux": [
        {"question": "What is the difference between a process and a thread in Linux?", "difficulty": "easy", "topic": "OS Fundamentals"},
        {"question": "How would you find and kill a process using a specific port?", "difficulty": "medium", "topic": "Administration"},
        {"question": "Explain Linux file permissions and how chmod works.", "difficulty": "easy", "topic": "File System"},
    ],
    "Django": [
        {"question": "What is the Django ORM and how does it differ from raw SQL?", "difficulty": "easy", "topic": "Database"},
        {"question": "Explain the Django request-response lifecycle.", "difficulty": "medium", "topic": "Architecture"},
        {"question": "How would you implement caching in a Django application?", "difficulty": "medium", "topic": "Performance"},
    ],
    "PostgreSQL": [
        {"question": "What are indexes in PostgreSQL and when should you use them?", "difficulty": "easy", "topic": "Performance"},
        {"question": "Explain the difference between ACID properties in PostgreSQL.", "difficulty": "medium", "topic": "Transactions"},
        {"question": "How would you handle database migrations in a production environment?", "difficulty": "medium", "topic": "Operations"},
    ],
    "CI/CD": [
        {"question": "What is the difference between Continuous Integration and Continuous Deployment?", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "How would you design a CI/CD pipeline for a microservices application?", "difficulty": "hard", "topic": "Architecture"},
        {"question": "What strategies would you use for zero-downtime deployments?", "difficulty": "medium", "topic": "Deployment"},
    ],
    "Terraform": [
        {"question": "What is Infrastructure as Code and why is Terraform useful?", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "Explain the difference between Terraform state and plan.", "difficulty": "medium", "topic": "Core Concepts"},
        {"question": "How do you manage Terraform state in a team environment?", "difficulty": "medium", "topic": "Collaboration"},
    ],
    "Networking": [
        {"question": "Explain the OSI model and its seven layers.", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "What is the difference between TCP and UDP?", "difficulty": "easy", "topic": "Protocols"},
        {"question": "How does DNS resolution work step by step?", "difficulty": "medium", "topic": "DNS"},
    ],
    "Machine Learning": [
        {"question": "What is the difference between supervised and unsupervised learning?", "difficulty": "easy", "topic": "Fundamentals"},
        {"question": "Explain the bias-variance tradeoff.", "difficulty": "medium", "topic": "Model Evaluation"},
        {"question": "How would you handle an imbalanced dataset?", "difficulty": "medium", "topic": "Data Preprocessing"},
    ],
    "Pandas": [
        {"question": "What is the difference between a Series and a DataFrame in Pandas?", "difficulty": "easy", "topic": "Data Structures"},
        {"question": "How would you handle missing values in a large dataset?", "difficulty": "medium", "topic": "Data Cleaning"},
        {"question": "Explain the difference between merge, join, and concat in Pandas.", "difficulty": "medium", "topic": "Data Manipulation"},
    ],
    "Network Security": [
        {"question": "What is the difference between symmetric and asymmetric encryption?", "difficulty": "easy", "topic": "Cryptography"},
        {"question": "Explain how a firewall works and the difference between stateful and stateless firewalls.", "difficulty": "medium", "topic": "Firewalls"},
        {"question": "What steps would you take to respond to a security incident?", "difficulty": "medium", "topic": "Incident Response"},
    ],
    "Unit Testing": [
        {"question": "What is the difference between unit tests, integration tests, and end-to-end tests?", "difficulty": "easy", "topic": "Testing Types"},
        {"question": "What is mocking and when would you use it in tests?", "difficulty": "medium", "topic": "Test Techniques"},
        {"question": "How do you decide what to test and what not to test?", "difficulty": "medium", "topic": "Strategy"},
    ],
}


def generate_interview_with_ai(skills, target_role, num_questions=5):
    """Use Groq (Llama 3) to generate mock interview questions."""
    client = _get_groq_client()
    if not client:
        return None

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "You are a technical interviewer. Generate mock interview questions based on the candidate's skills and target role. "
                    f"Return ONLY a JSON array of exactly {num_questions} objects with keys: question, skill (which skill it tests), "
                    "difficulty (easy/medium/hard), topic (sub-topic area), hint (a brief hint to guide the answer). "
                    "Mix difficulties. Make questions specific and practical, not generic."
                )},
                {"role": "user", "content": f"Target role: {target_role}\nCandidate skills: {json.dumps(skills)}\n\nGenerate {num_questions} interview questions."}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()
        questions = json.loads(content)
        if isinstance(questions, list) and len(questions) > 0:
            return questions
        return None
    except Exception:
        return None


def generate_interview_fallback(skills, target_role, num_questions=5):
    """Rule-based fallback: pick questions from the predefined bank."""
    questions = []
    for skill in skills:
        bank = INTERVIEW_QUESTIONS_BANK.get(skill, [])
        for q in bank:
            entry = {**q, "skill": skill, "hint": f"Think about core concepts of {skill} as used in {target_role} roles."}
            if entry not in questions:
                questions.append(entry)

    if not questions:
        return [{
            "question": f"Describe a project where you applied your technical skills relevant to a {target_role} position.",
            "skill": "General",
            "difficulty": "medium",
            "topic": "Behavioral",
            "hint": "Use the STAR method: Situation, Task, Action, Result."
        }]

    selected = questions[:num_questions]
    return selected


def generate_interview(skills, target_role, num_questions=5):
    """Generate mock interview questions with AI, falling back to question bank."""
    if not skills:
        return {"questions": [], "method": "none"}

    ai_questions = generate_interview_with_ai(skills, target_role, num_questions)
    if ai_questions:
        return {"questions": ai_questions, "method": "ai"}

    fallback_questions = generate_interview_fallback(skills, target_role, num_questions)
    return {"questions": fallback_questions, "method": "fallback"}


def get_skill_category(skill):
    """Return the category a skill belongs to."""
    skill_lower = skill.lower()
    for category, skills in SKILLS_TAXONOMY.items():
        if skill_lower in [s.lower() for s in skills]:
            return category
    return "other"
