# Phase 1 — Input & Topic Decomposition

This is the first phase of the LearnPath system. It handles:

1. Collecting user input (topic, skill level, goal, optional file uploads)
2. Parsing uploaded PDFs/notes into raw text
3. Calling Gemini to decompose the topic into ordered subtopics
4. Writing the result (with a `session_id`) to Redis for downstream phases

---

## Directory Structure

```
phase1/
├── backend/
│   ├── app.py                    # Flask app factory
│   ├── worker.py                 # RQ worker (run separately)
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   │   ├── schemas.py            # Pydantic models (Session, Subtopic, etc.)
│   │   └── session_store.py      # Redis CRUD helpers
│   ├── routes/
│   │   ├── input_routes.py       # POST /api/sessions
│   │   └── session_routes.py     # GET/DELETE /api/sessions/:id
│   ├── tasks/
│   │   └── decompose_task.py     # RQ background task
│   └── utils/
│       ├── gemini_client.py      # Gemini API wrapper + mock
│       ├── file_parser.py        # PDF/text extractor
│       └── upload_handler.py     # Multipart file save + validation
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx               # Root — orchestrates form → loading → results
│       ├── hooks/
│       │   └── useSession.js     # Polling logic, state machine
│       ├── components/
│       │   ├── TopicForm.jsx     # Input form with drag-drop upload
│       │   ├── SubtopicGrid.jsx  # Results display
│       │   └── StatusBanner.jsx  # Loading / error states
│       └── utils/
│           └── api.js            # Axios API client
└── tests/
    ├── test_schemas.py
    ├── test_routes.py
    └── test_gemini_client.py
```

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis running locally (`brew install redis && brew services start redis`)
- Gemini API key from https://aistudio.google.com/

### Backend

```bash
cd phase1/backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Terminal 1 — Flask dev server
python app.py

# Terminal 2 — RQ worker
python worker.py
```

### Frontend

```bash
cd phase1/frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## API Reference

### `POST /api/sessions`

Creates a session and enqueues the decomposition task.

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `topic` | string | ✅ | The topic to learn |
| `skill_level` | string | ❌ | `beginner` / `intermediate` / `advanced` (default: `beginner`) |
| `goal` | string | ❌ | Learner's stated goal |
| `files[]` | file | ❌ | PDF/txt/md/rst (max 10 MB each) |

**Response 201:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "topic": "Machine Learning",
  "skill_level": "beginner",
  "subtopics": [],
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

---

### `GET /api/sessions/:session_id`

Poll this until `status` is `"done"` or `"failed"`.

**Response 200 (done):**
```json
{
  "session_id": "550e8400-...",
  "status": "done",
  "topic": "Machine Learning",
  "skill_level": "beginner",
  "goal": null,
  "subtopics": [
    {
      "id": "uuid",
      "name": "Linear Algebra",
      "description": "Vectors, matrices, and eigenvalues",
      "order": 0,
      "is_prerequisite": true,
      "estimated_hours": 4.0
    }
  ],
  "uploaded_files": [],
  "error": null,
  "created_at": "...",
  "updated_at": "..."
}
```

---

## Development Tips

### Use the mock Gemini function (no API key needed)

In `tasks/decompose_task.py`, swap the import:

```python
# Comment out:
# from utils.gemini_client import decompose_topic

# Uncomment:
from utils.gemini_client import decompose_topic_mock as decompose_topic
```

This returns hardcoded subtopics instantly so you can build/test the UI.

### Test the API manually with curl

```bash
# Create a session
curl -X POST http://localhost:5000/api/sessions \
  -F "topic=VLSI Design" \
  -F "skill_level=beginner"

# Poll status (replace SESSION_ID)
curl http://localhost:5000/api/sessions/SESSION_ID
```

### Run tests

```bash
cd phase1
pip install pytest fakeredis
pytest tests/ -v
```

---

## The `session_id` — Phase Handoff

The most important output of Phase 1 is the `session_id`. Every downstream phase uses it:

| Phase | What it does with `session_id` |
|---|---|
| Phase 2 | Reads subtopics from Redis key `session:{id}`, writes research results back |
| Phase 3 | Reads Phase 2 results, writes roadmap JSON to `session:{id}` |
| Phase 4 | Reads roadmap URLs, embeds content into ChromaDB namespace `session:{id}` |
| Phase 5 | Filters ChromaDB queries with `where={"session_id": id}` |

**Never lose the `session_id`** — it's the thread tying the whole system together.

---

## What Phase 2 Expects from Phase 1

Phase 2 reads `GET /api/sessions/:session_id` and expects:

```json
{
  "status": "done",
  "topic": "...",
  "skill_level": "...",
  "subtopics": [
    { "name": "...", "description": "...", "order": 0 }
  ]
}
```

It will iterate over `subtopics` and run a parallel research job for each one.
