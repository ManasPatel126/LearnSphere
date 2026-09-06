# Phase 4 — Vector Ingestion Pipeline

Fetches, chunks, embeds, and stores every resource URL from the Phase 3 roadmap into ChromaDB, namespaced by `session_id`. This is what makes the Phase 5 chatbot work.

---

## Files

```
phase4/
├── tasks/
│   └── ingest.py          # RQ task — main entry point
├── utils/
│   ├── fetcher.py         # URL → plain text (YouTube / GitHub / generic)
│   ├── chunker.py         # Plain text → overlapping chunks
│   ├── embedder.py        # Chunks → Gemini text-embedding-004 vectors
│   └── retriever.py       # ChromaDB query helper (used by Phase 5)
├── routes_ingest.py       # Flask blueprint: POST /api/ingest, GET /api/ingest/status
├── tests/
│   └── test_phase4.py     # Full pytest suite (all mocked, no API keys needed)
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set environment variables
```env
GEMINI_API_KEY=your_gemini_key_here
GITHUB_TOKEN=your_github_pat_here     # optional, raises rate limit from 60→5000 req/hr
REDIS_URL=redis://localhost:6379/0
CHROMA_PATH=./chroma_store            # where ChromaDB persists data
```

### 3. Start the RQ worker
```bash
rq worker ingest
```

### 4. Register the blueprint in your Flask app
```python
from routes_ingest import ingest_bp
app.register_blueprint(ingest_bp)
```

---

## API

### `POST /api/ingest`
Kicks off a background ingestion job.

**Request body:**
```json
{
  "session_id": "abc123",
  "roadmap": { "modules": [...] },
  "uploaded_texts": [
    { "filename": "notes.pdf", "text": "extracted text..." }
  ]
}
```

**Response `202`:**
```json
{ "job_id": "rq:job:...", "status": "queued" }
```

---

### `GET /api/ingest/status/<job_id>`
Poll job progress.

**Response (running):** `{ "status": "started", "job_id": "..." }`

**Response (done):**
```json
{
  "status": "finished",
  "result": {
    "session_id": "abc123",
    "chunks_written": 347,
    "urls_processed": 18,
    "urls_failed": 2,
    "collection_name": "session-abc123"
  }
}
```

---

## Testing

```bash
# Run all unit tests (no API keys needed)
pytest tests/test_phase4.py -v

# Smoke test against real Gemini + ChromaDB
GEMINI_API_KEY=... python tests/test_phase4.py
```

---

## How it connects to other phases

| Phase | Dependency |
|-------|-----------|
| Phase 1 | Produces `session_id` — passed into every Phase 4 call |
| Phase 3 | Produces `roadmap` JSON — Phase 4 reads all `.resources[].url` fields |
| Phase 4 | Writes to ChromaDB `session-{session_id}` collection |
| Phase 5 | Reads from that collection via `utils/retriever.py` |

The `utils/retriever.py` file ships with Phase 4 but is consumed exclusively by Phase 5. Drop it into your Phase 5 directory and import it.

---

## ChromaDB namespace strategy

Each session gets its own ChromaDB collection: `session-{session_id}`. This means:

- No cross-session leakage — the Phase 5 chatbot literally cannot retrieve content from another user's course.
- Simple cleanup: `client.delete_collection("session-abc123")` wipes a session's data.
- No `where` filters needed at query time (the collection itself is the filter).

---

## Extending

**Add a new source type** (e.g. arXiv PDFs):
1. Add a branch in `utils/fetcher.py` matching `arxiv.org` URLs.
2. Fetch the PDF, extract text with `pdfminer` or `pypdf2`.
3. Return plain text — the rest of the pipeline is unchanged.

**Change chunk size:**
Edit `CHUNK_TOKENS` and `OVERLAP_TOKENS` in `utils/chunker.py`. 512/64 is the sweet spot for Gemini text-embedding-004.
