/**
 * Centralised API client for Phase 1.
 * All fetch logic lives here — components stay clean.
 */

import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 30_000,
});

/**
 * Create a new session (with optional file uploads).
 *
 * @param {{ topic: string, skillLevel: string, goal?: string, files?: File[] }} params
 * @returns {Promise<{ session_id: string, status: string }>}
 */
export async function createSession({ topic, skillLevel, goal, files = [] }) {
  const form = new FormData();
  form.append("topic", topic);
  form.append("skill_level", skillLevel);
  if (goal) form.append("goal", goal);
  for (const file of files) {
    form.append("files[]", file);
  }

  const { data } = await client.post("/sessions", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Poll session status.
 *
 * @param {string} sessionId
 * @returns {Promise<SessionData>}
 */
export async function getSession(sessionId) {
  const { data } = await client.get(`/sessions/${sessionId}`);
  return data;
}

/**
 * List all sessions (dev/debug).
 */
export async function listSessions() {
  const { data } = await client.get("/sessions");
  return data;
}
