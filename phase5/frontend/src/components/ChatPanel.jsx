/**
 * Phase 5 — ChatPanel
 * Streaming RAG chatbot. Sends to /chat, receives SSE chunks.
 * Isolated to session_id — the backend filters ChromaDB by it.
 */

import { useState, useRef, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

export default function ChatPanel({ sessionId, roadmapTopic }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Hi! I'm your course assistant for **${roadmapTopic}**. Ask me anything about the material — I can only answer from your curated course content.`,
      sources: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll on new message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setLoading(true);

    // Append user message
    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    // Placeholder for streaming assistant reply
    const placeholderIndex = messages.length + 1;
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", sources: [], streaming: true },
    ]);

    // Build history (exclude streaming placeholder)
    const history = messages
      .filter((m) => !m.streaming)
      .map((m) => ({ role: m.role, content: m.content }));

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text, history }),
      });

      if (!res.ok) throw new Error(`Server error ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accText = "";
      let finalSources = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const payload = JSON.parse(line.slice(6));
            if (payload.error) throw new Error(payload.error);
            if (payload.text) {
              accText += payload.text;
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: accText,
                  sources: [],
                  streaming: true,
                };
                return updated;
              });
            }
            if (payload.done) {
              finalSources = payload.sources ?? [];
            }
          } catch (_) {
            // malformed chunk — skip
          }
        }
      }

      // Finalise
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: accText || "Sorry, I couldn't generate a response.",
          sources: finalSources,
          streaming: false,
        };
        return updated;
      });
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: `Something went wrong: ${err.message}`,
          sources: [],
          streaming: false,
        };
        return updated;
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [input, loading, messages, sessionId]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-panel">
      {/* Message list */}
      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map((msg, i) => (
          <ChatMessage key={i} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          placeholder="Ask about your course material…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={loading}
          aria-label="Chat message"
        />
        <button
          className="chat-send"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          aria-label="Send message"
        >
          {loading ? <Spinner /> : "↑"}
        </button>
      </div>

      <p className="chat-disclaimer">
        Answers are drawn only from your curated course content.
      </p>
    </div>
  );
}

/* ── Message bubble ─────────────────────────────────────────────────────── */

function ChatMessage({ msg }) {
  const isUser = msg.role === "user";

  return (
    <div className={`chat-msg ${isUser ? "chat-msg--user" : "chat-msg--assistant"}`}>
      <div
        className="chat-bubble"
        /* Render markdown-lite: bold and code */
        dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
      />

      {msg.streaming && (
        <span className="streaming-cursor" aria-hidden="true">▌</span>
      )}

      {/* Sources */}
      {!isUser && msg.sources?.length > 0 && (
        <div className="chat-sources">
          <span className="sources-label">Sources</span>
          {msg.sources.map((s, i) => (
            <a
              key={i}
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="source-chip"
              title={`Relevance: ${Math.round(s.relevance * 100)}%`}
            >
              {s.title || s.url}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Helpers ─────────────────────────────────────────────────────────────── */

function Spinner() {
  return (
    <svg className="spin" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="40 20" />
    </svg>
  );
}

/** Very minimal markdown: bold, inline code, code blocks, line breaks. */
function renderMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    // code blocks
    .replace(/```[\w]*\n?([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    // inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // bold
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    // line breaks
    .replace(/\n/g, "<br/>");
}
