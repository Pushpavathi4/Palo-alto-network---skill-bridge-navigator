# Design Documentation — Skill-Bridge Career Navigator

## 1. Problem Statement

Students and early-career professionals face a "skills gap" between their academic knowledge and job market demands. Information is scattered across job boards, certification sites, and course platforms, making it hard to see a clear path from current skills to a target role.

**Skill-Bridge** solves this by providing a single tool that:
- Extracts skills from a resume
- Compares them against real job requirements
- Generates a prioritized, actionable learning roadmap
- Provides mock interview practice tailored to the user's skill profile

## 2. Architecture

```
┌─────────────┐     HTTP      ┌──────────────┐     ┌─────────────┐
│  Browser UI  │ ◄──────────► │  Flask App   │ ◄──►│ Synthetic   │
│  (HTML/JS)   │              │  (app.py)    │     │ Data (JSON) │
└─────────────┘              └──────┬───────┘     └─────────────┘
                                    │
                              ┌─────▼──────┐
                              │ AI Engine  │
                              │(ai_engine) │
                              └─────┬──────┘
                                    │
                         ┌──────────┼──────────┐
                         ▼                     ▼
                  ┌─────────────┐     ┌──────────────┐
                  │  Groq API   │     │  Rule-Based  │
                  │  (optional) │     │  Fallback    │
                  └─────────────┘     └──────────────┘
```

### Key Design Decisions

1. **Flask over Django**: Lighter weight, faster to scaffold, sufficient for a prototype with no ORM needs.

2. **Vanilla JS over React/Vue**: Eliminates build tooling overhead. The UI is a single page with 5 progressive steps — no routing needed.

3. **JSON files over SQLite**: For a prototype with synthetic data, file-based storage is simpler and makes the dataset easily inspectable/editable.

4. **Dual-mode AI (AI + Fallback)**: The app is fully functional without an API key. This is a deliberate design choice — the fallback isn't a degraded experience, it's a complete alternative path.

## 3. Technical Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python 3.10+, Flask | Lightweight, fast iteration |
| Frontend | HTML, CSS, Vanilla JS | No build step, minimal complexity |
| AI | Groq API (Llama 3.3 70B) | Free tier, fast inference |
| Fallback | Regex + predefined taxonomy | Deterministic, no external dependency |
| Data | JSON files | Portable, human-readable |
| Testing | pytest | Standard Python testing |
| Config | python-dotenv | Secure API key management |

## 4. AI Integration Details

### Skill Extraction
- **AI mode**: Sends resume text to Llama 3.3 70B (via Groq) with a system prompt constraining output to a JSON array of skill strings. Temperature set to 0.1 for consistency.
- **Fallback mode**: Iterates through a taxonomy of 100+ skills across 7 categories, using word-boundary regex to avoid partial matches (e.g., "SQL" won't match inside "MySQL").

### Roadmap Generation
- **AI mode**: Sends missing skills + target role to Llama 3.3 70B (via Groq), requesting a prioritized JSON array with skill, priority, reason, resource, and estimated hours.
- **Fallback mode**: Looks up each missing skill in a curated database of 50+ free/low-cost learning resources with estimated completion times.

### Mock Interview Generation
- **AI mode**: Sends user skills + target role to Llama 3.3 70B, requesting role-specific technical questions with difficulty levels and hints. Temperature set to 0.5 for variety.
- **Fallback mode**: Selects from a curated bank of 57+ questions across 19 skill categories, each with difficulty rating and topic classification.

### Why this approach is responsible:
- AI output is always validated (must be parseable JSON with expected structure)
- Users see which mode generated their results (transparency badge)
- The fallback ensures the app never fails silently — users always get actionable output
- No real personal data is processed; all examples use synthetic resumes

## 5. Data Safety

- All resumes and job descriptions are synthetic — no real personal data
- Sample data is included in `data/` directory as JSON files
- No web scraping or live API calls for data collection
- API keys are managed via `.env` (excluded from git via `.gitignore`)

## 6. Testing Strategy

- **Happy path tests**: Verify core flows work correctly (skill extraction, gap analysis, roadmap generation, mock interview, API endpoints)
- **Edge case tests**: Empty inputs, missing fields, nonexistent roles, unknown skills, very short text
- **27 total tests** covering both unit logic and API integration

## 7. Future Enhancements

1. **PDF Resume Upload**: Use `pdfplumber` or `PyPDF2` to extract text from uploaded resumes
2. **Persistent Profiles**: SQLite or PostgreSQL for user accounts and saved progress
3. **Real Job Data Integration**: Connect to job board APIs with caching and rate limiting
4. **Progress Tracking**: Mark skills as "learning" or "completed" and watch match percentages improve
5. **Collaborative Features**: Mentors can review mentee profiles and suggest priorities
6. **Export**: Download roadmap and interview questions as PDF or share via link
