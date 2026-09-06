# Phase 5 — Chatbot + Result UI

This phase delivers the two user-visible outputs:
1. **Roadmap display** — week-by-week curriculum view
2. **RAG chatbot** — isolated to this session's curated content

---

## Files

```
phase5/
├── backend/
│   ├── chat.py        → POST /chat  (SSE streaming, ChromaDB RAG)
│   └── result.py      → GET /result/<session_id>  (load roadmap from Redis)
└── frontend/src/
    ├── components/
    │   ├── LearningPathResult.jsx  → roadmap week view + chat toggle
    │   ├── ChatPanel.jsx           → streaming chat UI
    │   └── phase5.css              → all styles
    └── pages/
        └── ResultPage.jsx          → route wrapper
```

---

## Backend wiring

Register blueprints in your main `app.py`:

```python
from phase5.backend.chat import chat_bp
from phase5.backend.result import result_bp

app.register_blueprint(chat_bp)
app.register_blueprint(result_bp)
```

Required env vars (add to `.env`):
```
GEMINI_API_KEY=...
REDIS_HOST=localhost
REDIS_PORT=6379
CHROMA_HOST=localhost   # ChromaDB HTTP server (Phase 4 writes here)
```

---

## Frontend wiring

Add the result route in your router (`App.jsx` or equivalent):

```jsx
import ResultPage from "./pages/ResultPage";

// inside <Routes>
<Route path="/result/:sessionId" element={<ResultPage />} />
```

Import the styles globally or in `ResultPage.jsx`:
```js
import "./components/phase5.css";
```

---

## How the chatbot isolation works

1. Phase 4 writes chunks to ChromaDB with `metadata = { "session_id": "xyz", ... }`.
2. `chat.py` embeds the user query and queries ChromaDB with `where={"session_id": "xyz"}`.
3. Only chunks from that session are returned — no cross-contamination.
4. Gemini gets those chunks as system context and streams the answer.

---

## Roadmap JSON schema expected

`GET /result/<session_id>` returns:

```json
{
  "session_id": "abc123",
  "roadmap": {
    "topic": "Machine Learning",
    "skill_level": "beginner",
    "total_weeks": 8,
    "modules": [
      {
        "week": 1,
        "title": "Python & Math Foundations",
        "concepts": ["NumPy", "Pandas", "Linear Algebra basics"],
        "resources": [
          {
            "title": "Python NumPy Tutorial",
            "url": "https://...",
            "type": "video",
            "platform": "YouTube"
          }
        ],
        "project": "Build a data cleaning script for a CSV dataset",
        "checkpoint": "Can explain broadcasting and slicing in NumPy"
      }
    ]
  }
}
```

---

## Testing

**Backend — chat endpoint:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"abc123","message":"What is backpropagation?","history":[]}'
```

**Backend — sources check:**
```bash
curl -X POST http://localhost:5000/chat/sources \
  -H "Content-Type: application/json" \
  -d '{"session_id":"abc123","query":"backpropagation"}'
```

**Frontend:**
Navigate to `/result/<session_id>` — the roadmap loads, click "💬 Ask your course" to open the chat panel.

---

## Dependency on previous phases

| Depends on | Why |
|---|---|
| Phase 1 | `session_id` is created here |
| Phase 3 | Roadmap JSON saved to Redis under `roadmap:<session_id>` |
| Phase 4 | ChromaDB populated with `session_id`-namespaced chunks |

Phase 5 has no dependency on Phase 2 directly — it only needs the output artefacts of 3 and 4.
