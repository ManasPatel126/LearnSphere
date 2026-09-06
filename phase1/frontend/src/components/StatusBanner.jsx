/**
 * StatusBanner — shows a loading spinner or error message.
 * Displayed between form submit and results appearing.
 */

import React from "react";

export default function StatusBanner({ phase, error }) {
  if (phase === "submitting") {
    return (
      <div style={styles.banner}>
        <Spinner />
        <span style={styles.text}>Creating your session…</span>
      </div>
    );
  }

  if (phase === "polling") {
    return (
      <div style={styles.banner}>
        <Spinner />
        <div style={styles.textGroup}>
          <span style={styles.text}>Analysing your topic with Gemini…</span>
          <span style={styles.subtext}>This usually takes 5–15 seconds</span>
        </div>
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div style={{ ...styles.banner, ...styles.errorBanner }}>
        <span style={styles.errorIcon}>⚠</span>
        <div style={styles.textGroup}>
          <span style={styles.errorText}>Something went wrong</span>
          <span style={styles.subtext}>{error}</span>
        </div>
      </div>
    );
  }

  return null;
}

function Spinner() {
  return (
    <div
      style={{
        width: 22,
        height: 22,
        border: "2.5px solid #2a2a3a",
        borderTopColor: "#7c5cbf",
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
        flexShrink: 0,
      }}
    />
  );
}

const styles = {
  banner: {
    display: "flex",
    alignItems: "center",
    gap: 14,
    padding: "16px 20px",
    background: "#1a1a24",
    border: "1px solid #2a2a3a",
    borderRadius: 10,
  },
  errorBanner: {
    borderColor: "#5a2a2a",
    background: "#1a1010",
  },
  textGroup: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  text: {
    fontSize: 14,
    color: "#a8a8c0",
  },
  subtext: {
    fontSize: 12,
    color: "#505060",
  },
  errorIcon: {
    fontSize: 20,
    color: "#e05050",
  },
  errorText: {
    fontSize: 14,
    color: "#e05050",
    fontWeight: 600,
  },
};
