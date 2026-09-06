# Phase 2 — Web Research Engine

Runs once per subtopic, **fully parallelised**. Produces a scored JSON array of resources per subtopic, saved to Redis keyed by `session_id`.

This phase has **zero dependency on Phase 3 or 4** — build and test it completely independently using a hardcoded subtopic list.

---

## What it does

| Source | API Used | What it fetches |
|---|---|---|
| YouTube | YouTube Data API v3 + `youtube-transcript-api` | Top videos + full transcripts |
| GitHub | GitHub REST API | Top-starred repos + READMEs |
| Reddit | PRAW | Top upvoted posts + top comments |
| Articles | Perplexity sonar / NewsAPI | Curated articles, docs, tutorials |

After fetching, **Gemini Flash scores each resource 0–1** for relevance and quality. The final score blends Gemini's semantic score (70%) with hard signals like star count and upvotes (30%).

---

## Output shape

```json
{
  "session_id": "abc123",
  "subtopics": ["Neural Networks", "Backpropagation"],
  "resources": {
    "Neural Networks": [
      {
        "title": "Neural Networks from Scratch",
        "url": "https://youtube.com/watch?v=...",
        "source": "youtube",
        "subtopic": "Neural Networks",
        "content_preview": "...",
        "quality_score": 0.91,
        "gemini_score": 0.93,
        "signal_score": 0.85,
        "score_reason": "High-quality tutorial with full transcript covering fundamentals"
      }
    ]
  }
}
```

This JSON is exactly what Phase 3 (Roadmap Generator) consumes.

---

## Setup

```bash
cd phase2
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

Start a Redis server (or use your existing one):
```bash
redis-server
```

Start an RQ worker:
```bash
rq worker research
```

---

## Testing independently (no Phase 1 needed)

```bash
# Unit tests only (no API keys needed):
pytest tests/ -v

# Full pipeline test with real APIs:
GEMINI_API_KEY=your_key pytest tests/ -v -k "integration"

# Run the standalone script and inspect output JSON:
python tests/test_phase2.py
# → Prints top 3 resources per subtopic
# → Saves full output to phase2_sample_output.json
```

---

## Integration with your Flask app

```python
# In app.py:
from phase2.routes import research_bp
app.register_blueprint(research_bp)
```

**Endpoints:**

| Method | URL | Purpose |
|---|---|---|
| `POST` | `/api/research/start` | Enqueue research job |
| `GET` | `/api/research/status/<job_id>` | Poll job status |
| `GET` | `/api/research/<session_id>` | Retrieve cached results |

**Enqueue from Phase 1:**
```python
import requests
resp = requests.post("/api/research/start", json={
    "session_id": "abc123",
    "subtopics": ["Neural Networks", "Backpropagation", "CNNs"]
})
job_id = resp.json()["job_id"]
```

**Phase 3 reads results:**
```python
from research_engine.orchestrator import load_research_results
results = load_research_results(session_id)
resources_by_subtopic = results["resources"]
```

---

## File structure

```
phase2/
├── research_engine/
│   ├── __init__.py
│   ├── youtube_fetcher.py   # YouTube search + transcript fetch
│   ├── github_fetcher.py    # GitHub repo search + README fetch
│   ├── reddit_fetcher.py    # Reddit post search via PRAW
│   ├── articles_fetcher.py  # Perplexity / NewsAPI article fetch
│   ├── quality_scorer.py    # Gemini Flash scoring + signal blending
│   ├── orchestrator.py      # Parallel runner + Redis persistence
│   └── tasks.py             # RQ task wrapper
├── routes.py                # Flask blueprint
├── tests/
│   └── test_phase2.py       # Unit + integration tests
├── requirements.txt
├── .env.example
└── README.md
```

---

## Handoff to Phase 3

Phase 3 needs exactly one thing from Phase 2:

```python
load_research_results(session_id)["resources"]
# → dict mapping subtopic → list of scored resource dicts
```

The top-K resources per subtopic (by `quality_score`) go into the Phase 3 Gemini prompt as the source material for roadmap generation.
