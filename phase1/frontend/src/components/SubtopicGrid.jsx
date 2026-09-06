/**
 * SubtopicGrid — renders the Gemini-generated subtopics after decomposition.
 * This is the "Phase 1 output" screen. Phase 2 is triggered from here.
 */

import React from "react";

export default function SubtopicGrid({ session, onProceed }) {
  const total = session.subtopics.reduce(
    (acc, st) => acc + (st.estimated_hours ?? 0),
    0
  );

  return (
    <div style={styles.container}>
      {/* Header ──────────────────────────────────────────────────────────────── */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>{session.topic}</h2>
          <p style={styles.meta}>
            {session.skill_level} · {session.subtopics.length} subtopics
            {total > 0 && ` · ~${total}h total`}
          </p>
        </div>
        <button style={styles.proceedBtn} onClick={onProceed}>
          Start research → Phase 2
        </button>
      </div>

      {/* Session ID badge ────────────────────────────────────────────────────── */}
      <div style={styles.sessionBadge}>
        <span style={styles.sessionLabel}>Session ID</span>
        <code style={styles.sessionCode}>{session.session_id}</code>
        <span style={styles.sessionHint}>
          (pass this to Phase 2 to continue)
        </span>
      </div>

      {/* Subtopic cards ──────────────────────────────────────────────────────── */}
      <div style={styles.grid}>
        {session.subtopics.map((st, idx) => (
          <SubtopicCard key={st.id} subtopic={st} index={idx + 1} />
        ))}
      </div>
    </div>
  );
}

function SubtopicCard({ subtopic, index }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <span style={styles.cardIndex}>{index}</span>
        {subtopic.is_prerequisite && (
          <span style={styles.prereqBadge}>prerequisite</span>
        )}
        {subtopic.estimated_hours && (
          <span style={styles.hoursBadge}>{subtopic.estimated_hours}h</span>
        )}
      </div>
      <h3 style={styles.cardTitle}>{subtopic.name}</h3>
      <p style={styles.cardDesc}>{subtopic.description}</p>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    gap: 28,
    width: "100%",
    maxWidth: 860,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 16,
    flexWrap: "wrap",
  },
  title: {
    fontSize: 26,
    fontWeight: 700,
    color: "#e8e8f0",
    margin: 0,
  },
  meta: {
    fontSize: 14,
    color: "#606070",
    marginTop: 4,
  },
  proceedBtn: {
    padding: "12px 22px",
    background: "linear-gradient(135deg, #3a8a5c, #276040)",
    border: "none",
    borderRadius: 10,
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  sessionBadge: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 16px",
    background: "#1a1a24",
    border: "1px solid #2a2a3a",
    borderRadius: 8,
    flexWrap: "wrap",
  },
  sessionLabel: {
    fontSize: 12,
    color: "#606070",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  sessionCode: {
    fontSize: 13,
    color: "#9d7de8",
    fontFamily: "monospace",
    background: "#12121a",
    padding: "2px 8px",
    borderRadius: 4,
  },
  sessionHint: {
    fontSize: 12,
    color: "#505060",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    gap: 14,
  },
  card: {
    padding: "18px 20px",
    background: "#1a1a24",
    border: "1.5px solid #2a2a3a",
    borderRadius: 12,
    display: "flex",
    flexDirection: "column",
    gap: 8,
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  cardIndex: {
    width: 24,
    height: 24,
    background: "#2a2a3a",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 12,
    fontWeight: 700,
    color: "#9d7de8",
    flexShrink: 0,
  },
  prereqBadge: {
    fontSize: 10,
    fontWeight: 600,
    color: "#e8a030",
    background: "#2a1f0a",
    border: "1px solid #3a2a0a",
    borderRadius: 4,
    padding: "2px 6px",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  hoursBadge: {
    fontSize: 11,
    color: "#506070",
    marginLeft: "auto",
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: "#d8d8f0",
    margin: 0,
  },
  cardDesc: {
    fontSize: 13,
    color: "#606070",
    lineHeight: 1.5,
    margin: 0,
  },
};
