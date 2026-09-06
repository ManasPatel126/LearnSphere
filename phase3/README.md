# Phase 3 — Roadmap Generator

Takes the scored resources from Phase 2 and produces a validated JSON roadmap via Gemini structured output.

---

## What this phase does

1. Receives `scored_resources[]` (from Phase 2) + `session_id`, `topic`, `skill_level`
2. Picks top-K resources by quality score
3. Sends a strict JSON-schema prompt to Gemini 1.5 Pro (`response_mime_type="application/json"`)
4. Validates the response with Pydantic — retries up to 3× on bad output
5. Converts to `LearningPath` ORM model and caches in Redis under `roadmap:<session_id>`

---

## Setup

```bash
cp .env.example .env   # fill in GEMINI_API_KEY
pip install -r requirements.txt
```

Start a Redis + RQ worker:
```bash
redis-server &
rq worker roadmap
```

Run the Flask dev server:
```bash
flask --app "app:create_app()" run --port 5003
```

---

## API

### `POST /roadmap/generate`
Enqueues the generation task. Returns immediately with `job_id`.

**Body:**
```json
{
  "session_id": "abc123",
  "topic": "Machine Learning",
  "skill_level": "beginner",
  "scored_resources": [
    { "title": "...", "url": "...", "type": "video", "score": 0.91 }
  ],
  "user_notes": "optional extracted PDF text"
}
```

**Response:**
```json
{ "job_id": "rq-job-xxx", "session_id": "abc123" }
```

### `GET /roadmap/status/<job_id>`
Poll until `status` is `finished` or `failed`.

### `GET /roadmap/<session_id>`
Fetch the completed roadmap JSON. This is what Phase 4 and Phase 5 consume.

---

## Testing

```bash
pytest tests/ -v
```

All tests mock the Gemini API — no API key needed.

---

## Key design decisions

| Decision | Why |
|---|---|
| `response_mime_type="application/json"` | Forces Gemini to output valid JSON, fewer fences |
| Pydantic v2 schema with validators | Catches and retries bad output before it reaches the DB |
| `temperature=0.3` | Low temp = more deterministic structure |
| Redis cache with 7-day TTL | Phase 4 + 5 read from here without hitting the DB |
| `session_id` as namespace key | The thread tying all 5 phases together |

---

## Handoff to Phase 4

Phase 4 (vector ingestion) reads the roadmap from Redis:
```python
raw = redis.get(f"roadmap:{session_id}")
roadmap = json.loads(raw)
# then fetch full text from every URL in roadmap["modules"][*]["resources"][*]["url"]
```
