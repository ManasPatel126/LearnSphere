/**
 * App — Phase 1 root component.
 * Orchestrates: form → loading → subtopic results.
 */

import React from "react";
import TopicForm    from "./components/TopicForm.jsx";
import SubtopicGrid from "./components/SubtopicGrid.jsx";
import StatusBanner from "./components/StatusBanner.jsx";
import { useSession } from "./hooks/useSession.js";

export default function App() {
  const { phase, session, error, submit, reset } = useSession();

  function handleProceed() {
    // Phase 2 integration point:
    // Navigate to /phase2 or emit session_id to parent app
    alert(
      `Phase 1 complete!\n\nPass this session_id to Phase 2:\n${session.session_id}`
    );
  }

  return (
    <>
      {/* Global spinner keyframe */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      <div style={styles.page}>
        {/* Header ─────────────────────────────────────────────────────────────── */}
        <header style={styles.header}>
          <div style={styles.logo}>LearnPath</div>
          <div style={styles.phase}>Phase 1 — Topic Decomposition</div>
        </header>

        <main style={styles.main}>
          {/* Step 1: Form ─────────────────────────────────────────────────────── */}
          {phase === "idle" && (
            <>
              <h1 style={styles.heading}>What do you want to master?</h1>
              <p style={styles.subheading}>
                Enter a topic and we'll build you a structured, researched
                learning roadmap — powered by Gemini.
              </p>
              <TopicForm onSubmit={submit} loading={false} />
            </>
          )}

          {/* Step 2: Loading ──────────────────────────────────────────────────── */}
          {(phase === "submitting" || phase === "polling") && (
            <>
              <h1 style={styles.heading}>Decomposing your topic…</h1>
              <StatusBanner phase={phase} error={error} />
            </>
          )}

          {/* Step 3: Error ────────────────────────────────────────────────────── */}
          {phase === "error" && (
            <>
              <StatusBanner phase={phase} error={error} />
              <button style={styles.retryBtn} onClick={reset}>
                ← Try again
              </button>
            </>
          )}

          {/* Step 4: Results ──────────────────────────────────────────────────── */}
          {phase === "done" && session && (
            <>
              <SubtopicGrid session={session} onProceed={handleProceed} />
              <button style={styles.retryBtn} onClick={reset}>
                ← New topic
              </button>
            </>
          )}
        </main>
      </div>
    </>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "16px 32px",
    borderBottom: "1px solid #1e1e2a",
  },
  logo: {
    fontSize: 18,
    fontWeight: 700,
    color: "#9d7de8",
    letterSpacing: "-0.02em",
  },
  phase: {
    fontSize: 12,
    color: "#505060",
    fontWeight: 500,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  main: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "48px 24px 80px",
    gap: 24,
  },
  heading: {
    fontSize: 32,
    fontWeight: 700,
    color: "#e8e8f0",
    textAlign: "center",
    margin: 0,
    letterSpacing: "-0.02em",
  },
  subheading: {
    fontSize: 15,
    color: "#606070",
    textAlign: "center",
    maxWidth: 480,
    lineHeight: 1.6,
    margin: 0,
  },
  retryBtn: {
    background: "none",
    border: "1px solid #2a2a3a",
    borderRadius: 8,
    color: "#808090",
    fontSize: 13,
    padding: "8px 16px",
    cursor: "pointer",
    marginTop: 8,
  },
};
