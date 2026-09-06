/**
 * Phase 5 — ResultPage
 * Fetches roadmap by session_id from URL params, renders LearningPathResult.
 */

import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import LearningPathResult from "../components/LearningPathResult";
import "../components/phase5.css";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

export default function ResultPage() {
  const { sessionId } = useParams();
  const [roadmap, setRoadmap] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;

    fetch(`${API_BASE}/result/${sessionId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Server returned ${r.status}`);
        return r.json();
      })
      .then((data) => setRoadmap(data.roadmap))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen message={error} />;
  if (!roadmap) return <ErrorScreen message="Roadmap not found." />;

  return <LearningPathResult roadmap={roadmap} sessionId={sessionId} />;
}

function LoadingScreen() {
  return (
    <div className="status-screen">
      <div className="status-spinner" aria-label="Loading" />
      <p>Building your roadmap…</p>
    </div>
  );
}

function ErrorScreen({ message }) {
  return (
    <div className="status-screen">
      <p className="status-error">⚠ {message}</p>
      <a href="/" className="status-link">Start over</a>
    </div>
  );
}
