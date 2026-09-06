/**
 * Phase 5 — LearningPathResult
 * Roadmap display + inline RAG chatbot panel.
 * Extends the existing skeleton with the chat panel alongside.
 */

import { useState, useRef, useEffect } from "react";
import ChatPanel from "./ChatPanel";

export default function LearningPathResult({ roadmap, sessionId }) {
  const [activeWeek, setActiveWeek] = useState(0);
  const [chatOpen, setChatOpen] = useState(false);

  if (!roadmap) return null;

  const { topic, skill_level, modules = [], total_weeks } = roadmap;

  return (
    <div className="result-layout">
      {/* ── Left: Roadmap ────────────────────────────────── */}
      <main className="roadmap-main">
        {/* Header */}
        <header className="roadmap-header">
          <div className="roadmap-meta">
            <span className="badge">{skill_level}</span>
            <span className="dot" />
            <span className="weeks-label">{total_weeks} weeks</span>
          </div>
          <h1 className="roadmap-title">{topic}</h1>
        </header>

        {/* Week tabs */}
        <nav className="week-tabs" aria-label="Weeks">
          {modules.map((mod, i) => (
            <button
              key={i}
              className={`week-tab ${activeWeek === i ? "active" : ""}`}
              onClick={() => setActiveWeek(i)}
            >
              Week {mod.week}
            </button>
          ))}
        </nav>

        {/* Active module */}
        {modules[activeWeek] && (
          <ModuleCard module={modules[activeWeek]} />
        )}
      </main>

      {/* ── Right: Chat toggle ───────────────────────────── */}
      <aside className={`chat-aside ${chatOpen ? "open" : "collapsed"}`}>
        <button
          className="chat-toggle"
          onClick={() => setChatOpen((o) => !o)}
          aria-label={chatOpen ? "Close chat" : "Open course assistant"}
        >
          {chatOpen ? (
            <span>✕ Close</span>
          ) : (
            <span>💬 Ask your course</span>
          )}
        </button>

        {chatOpen && (
          <ChatPanel sessionId={sessionId} roadmapTopic={topic} />
        )}
      </aside>
    </div>
  );
}

/* ── Module Card ─────────────────────────────────────────────────────────── */

function ModuleCard({ module }) {
  const {
    week,
    title,
    concepts = [],
    resources = [],
    project,
    checkpoint,
  } = module;

  return (
    <div className="module-card">
      <div className="module-header">
        <span className="week-number">Week {week}</span>
        <h2 className="module-title">{title}</h2>
      </div>

      {/* Concepts */}
      {concepts.length > 0 && (
        <section className="module-section">
          <h3 className="section-heading">Concepts</h3>
          <ul className="concept-list">
            {concepts.map((c, i) => (
              <li key={i} className="concept-item">
                <span className="concept-dot" />
                {c}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Resources */}
      {resources.length > 0 && (
        <section className="module-section">
          <h3 className="section-heading">Resources</h3>
          <div className="resource-grid">
            {resources.map((r, i) => (
              <ResourceCard key={i} resource={r} />
            ))}
          </div>
        </section>
      )}

      {/* Project */}
      {project && (
        <section className="module-section project-section">
          <h3 className="section-heading">Project</h3>
          <div className="project-card">
            <span className="project-icon">🛠</span>
            <p>{project}</p>
          </div>
        </section>
      )}

      {/* Checkpoint */}
      {checkpoint && (
        <section className="module-section">
          <h3 className="section-heading">Checkpoint</h3>
          <div className="checkpoint-card">
            <span className="checkpoint-icon">✓</span>
            <p>{checkpoint}</p>
          </div>
        </section>
      )}
    </div>
  );
}

function ResourceCard({ resource }) {
  const typeIcon = {
    video: "▶",
    article: "📄",
    github: "⎇",
    book: "📖",
    course: "🎓",
  };

  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="resource-card"
    >
      <span className="resource-type-icon">
        {typeIcon[resource.type] ?? "🔗"}
      </span>
      <div className="resource-info">
        <span className="resource-title">{resource.title}</span>
        {resource.platform && (
          <span className="resource-platform">{resource.platform}</span>
        )}
      </div>
      <span className="resource-arrow">↗</span>
    </a>
  );
}
