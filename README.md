# 🌉 Skill-Bridge Career Navigator

**Candidate Name:** [Your Name]
**Scenario Chosen:** 2 — Skill-Bridge Career Navigator
**Estimated Time Spent:** ~5 hours

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Run Commands
```bash
# 1. Clone the repo and cd into it
cd skill-bridge

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up Groq API key for AI-powered features
copy .env.example .env
# Edit .env and add your GROQ_API_KEY (free at https://console.groq.com/keys)
# NOTE: The app works fully WITHOUT an API key using rule-based fallback

# 5. Run the app
python app.py

# 6. Open http://localhost:5000 in your browser
```

### Test Commands
```bash
pytest tests/ -v
```

---

## How It Works

1. **Paste your resume** (or pick a sample) → skills are extracted
2. **Choose a target role** (Cloud Engineer, Backend Developer, etc.)
3. **View gap analysis** — see matched vs. missing skills per job description
4. **Get a learning roadmap** — prioritized courses to fill your gaps
5. **Practice mock interviews** — AI-generated questions based on your skills
6. **Search jobs** — filter by role, company, or skill keyword

### AI Integration + Fallback

| Feature | AI Mode (Groq / Llama 3.3 70B) | Fallback Mode (Rule-based) |
|---|---|---|
| Skill Extraction | Llama 3.3 70B parses resume text | Regex matching against 100+ skill taxonomy |
| Roadmap Generation | Llama 3.3 70B prioritizes and recommends | Predefined resource database with 50+ courses |
| Mock Interview | Llama 3.3 70B generates role-specific questions | Curated bank of 57+ questions across 19 skills |
| Gap Analysis | Always rule-based (deterministic) | Same |

The UI clearly shows which mode is active with a badge: 🤖 AI or 🔧 Fallback.

---

## Video Presentation

[Link to 5-7 minute video] *(Upload to YouTube/Vimeo and paste link here)*

---

## AI Disclosure

- **Did you use an AI assistant?** Yes — Amazon Q Developer for code scaffolding and iteration.
- **How did you verify suggestions?** Manually reviewed all generated code, ran tests, and tested the full flow in browser.
- **Example of a rejected suggestion:** AI suggested using a complex React frontend; I rejected this in favor of vanilla JS to stay within the timebox and reduce complexity.

---

## Tradeoffs & Prioritization

### What I cut to stay within 4–6 hours:
- No user authentication or persistent database (data is in-memory from JSON files)
- No resume file upload (PDF parsing) — text paste only
- Minimal UI polish — functional but not production-grade

### What I'd build next with more time:
- PDF resume upload with text extraction
- Persistent user profiles with progress tracking
- Integration with real job board APIs (with proper rate limiting)
- User accounts and saved roadmaps
- Export roadmap/interview questions as PDF

### Known limitations:
- Skill extraction fallback relies on exact keyword matching — compound skills like "Machine Learning" work, but unusual phrasings may be missed
- The synthetic dataset has 10 job descriptions across 7 roles — a production system would need thousands
- Groq free tier has rate limits; the app defaults to fallback mode if rate-limited or key is missing
