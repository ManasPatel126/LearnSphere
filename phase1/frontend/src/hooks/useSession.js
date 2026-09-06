/**
 * useSession — manages a session lifecycle:
 *   idle → submitting → polling → done | error
 *
 * Polls GET /api/sessions/:id every POLL_INTERVAL ms until status is terminal.
 */

import { useState, useRef, useCallback } from "react";
import { createSession, getSession } from "../utils/api.js";

const POLL_INTERVAL = 2000;   // ms

const TERMINAL = new Set(["done", "failed"]);

export function useSession() {
  const [state, setState] = useState({
    phase:     "idle",          // idle | submitting | polling | done | error
    sessionId: null,
    session:   null,
    error:     null,
  });

  const intervalRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const startPolling = useCallback(
    (sessionId) => {
      intervalRef.current = setInterval(async () => {
        try {
          const data = await getSession(sessionId);

          setState((prev) => ({
            ...prev,
            session: data,
            phase: TERMINAL.has(data.status)
              ? data.status === "done"
                ? "done"
                : "error"
              : "polling",
            error: data.status === "failed" ? (data.error ?? "Decomposition failed") : null,
          }));

          if (TERMINAL.has(data.status)) {
            stopPolling();
          }
        } catch (err) {
          stopPolling();
          setState((prev) => ({
            ...prev,
            phase: "error",
            error: err.response?.data?.detail ?? err.message,
          }));
        }
      }, POLL_INTERVAL);
    },
    [stopPolling]
  );

  const submit = useCallback(
    async ({ topic, skillLevel, goal, files }) => {
      stopPolling();
      setState({ phase: "submitting", sessionId: null, session: null, error: null });

      try {
        const data = await createSession({ topic, skillLevel, goal, files });
        setState((prev) => ({
          ...prev,
          phase:     "polling",
          sessionId: data.session_id,
          session:   data,
        }));
        startPolling(data.session_id);
      } catch (err) {
        setState({
          phase:     "error",
          sessionId: null,
          session:   null,
          error:     err.response?.data?.detail ?? err.message,
        });
      }
    },
    [startPolling, stopPolling]
  );

  const reset = useCallback(() => {
    stopPolling();
    setState({ phase: "idle", sessionId: null, session: null, error: null });
  }, [stopPolling]);

  return { ...state, submit, reset };
}
