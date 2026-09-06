/**
 * TopicForm — collects topic, skill level, goal, and optional files.
 * Calls onSubmit({ topic, skillLevel, goal, files }) when ready.
 */

import React, { useState, useRef } from "react";

const SKILL_LEVELS = [
  { value: "beginner",     label: "Beginner",     desc: "Starting from scratch" },
  { value: "intermediate", label: "Intermediate", desc: "Know the basics" },
  { value: "advanced",     label: "Advanced",      desc: "Deep expertise" },
];

export default function TopicForm({ onSubmit, loading }) {
  const [topic,      setTopic]      = useState("");
  const [skillLevel, setSkillLevel] = useState("beginner");
  const [goal,       setGoal]       = useState("");
  const [files,      setFiles]      = useState([]);
  const [dragOver,   setDragOver]   = useState(false);
  const fileRef = useRef();

  function handleFiles(incoming) {
    const valid = Array.from(incoming).filter((f) => {
      const ext = f.name.split(".").pop().toLowerCase();
      return ["pdf", "txt", "md", "rst"].includes(ext);
    });
    setFiles((prev) => [...prev, ...valid]);
  }

  function removeFile(idx) {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!topic.trim()) return;
    onSubmit({ topic: topic.trim(), skillLevel, goal: goal.trim() || undefined, files });
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      {/* Topic ──────────────────────────────────────────────────────────────── */}
      <label style={styles.label}>
        What do you want to learn?
        <input
          style={styles.input}
          type="text"
          placeholder="e.g. VLSI Design, Machine Learning, Rust programming..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          required
          disabled={loading}
        />
      </label>

      {/* Skill level ─────────────────────────────────────────────────────────── */}
      <fieldset style={styles.fieldset}>
        <legend style={styles.legend}>Your skill level</legend>
        <div style={styles.skillGrid}>
          {SKILL_LEVELS.map(({ value, label, desc }) => (
            <label
              key={value}
              style={{
                ...styles.skillCard,
                ...(skillLevel === value ? styles.skillCardActive : {}),
              }}
            >
              <input
                type="radio"
                name="skillLevel"
                value={value}
                checked={skillLevel === value}
                onChange={() => setSkillLevel(value)}
                style={{ display: "none" }}
                disabled={loading}
              />
              <span style={styles.skillLabel}>{label}</span>
              <span style={styles.skillDesc}>{desc}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Goal ───────────────────────────────────────────────────────────────── */}
      <label style={styles.label}>
        Your goal <span style={styles.optional}>(optional)</span>
        <textarea
          style={{ ...styles.input, height: 72, resize: "vertical" }}
          placeholder="e.g. Get a job as a chip designer, pass the AWS exam..."
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          disabled={loading}
        />
      </label>

      {/* File upload ─────────────────────────────────────────────────────────── */}
      <div style={styles.label}>
        Upload notes / PDFs <span style={styles.optional}>(optional)</span>
        <div
          style={{
            ...styles.dropzone,
            ...(dragOver ? styles.dropzoneActive : {}),
          }}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
        >
          <span style={styles.dropzoneText}>
            {dragOver ? "Drop it!" : "Click or drag files here"}
          </span>
          <span style={styles.dropzoneHint}>.pdf · .txt · .md · .rst · max 10 MB</span>
          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".pdf,.txt,.md,.rst"
            style={{ display: "none" }}
            onChange={(e) => handleFiles(e.target.files)}
            disabled={loading}
          />
        </div>

        {files.length > 0 && (
          <ul style={styles.fileList}>
            {files.map((f, i) => (
              <li key={i} style={styles.fileItem}>
                <span style={styles.fileName}>{f.name}</span>
                <span style={styles.fileSize}>
                  {(f.size / 1024).toFixed(0)} KB
                </span>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  style={styles.removeBtn}
                  disabled={loading}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Submit ──────────────────────────────────────────────────────────────── */}
      <button type="submit" style={styles.submit} disabled={loading || !topic.trim()}>
        {loading ? "Building your roadmap…" : "Generate roadmap →"}
      </button>
    </form>
  );
}

/* ── Inline styles (no CSS file dependency) ───────────────────────────────── */
const styles = {
  form: {
    display: "flex",
    flexDirection: "column",
    gap: 24,
    width: "100%",
    maxWidth: 620,
  },
  label: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    fontSize: 14,
    fontWeight: 600,
    color: "#a8a8c0",
    letterSpacing: "0.02em",
  },
  optional: {
    fontWeight: 400,
    color: "#606070",
    marginLeft: 4,
  },
  input: {
    background: "#1a1a24",
    border: "1.5px solid #2a2a3a",
    borderRadius: 10,
    padding: "12px 16px",
    color: "#e8e8f0",
    fontSize: 15,
    outline: "none",
    transition: "border-color 0.15s",
    fontFamily: "inherit",
  },
  fieldset: {
    border: "none",
    padding: 0,
  },
  legend: {
    fontSize: 14,
    fontWeight: 600,
    color: "#a8a8c0",
    marginBottom: 10,
  },
  skillGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 10,
  },
  skillCard: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    padding: "12px 14px",
    background: "#1a1a24",
    border: "1.5px solid #2a2a3a",
    borderRadius: 10,
    cursor: "pointer",
    transition: "border-color 0.15s, background 0.15s",
  },
  skillCardActive: {
    borderColor: "#7c5cbf",
    background: "#1e1730",
  },
  skillLabel: {
    fontSize: 14,
    fontWeight: 600,
    color: "#e8e8f0",
  },
  skillDesc: {
    fontSize: 12,
    color: "#606070",
  },
  dropzone: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    padding: "28px 20px",
    background: "#1a1a24",
    border: "1.5px dashed #2a2a3a",
    borderRadius: 10,
    cursor: "pointer",
    transition: "border-color 0.15s, background 0.15s",
  },
  dropzoneActive: {
    borderColor: "#7c5cbf",
    background: "#1e1730",
  },
  dropzoneText: {
    fontSize: 14,
    color: "#a8a8c0",
  },
  dropzoneHint: {
    fontSize: 12,
    color: "#505060",
  },
  fileList: {
    listStyle: "none",
    display: "flex",
    flexDirection: "column",
    gap: 6,
    marginTop: 8,
  },
  fileItem: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "8px 12px",
    background: "#1a1a24",
    borderRadius: 8,
    border: "1px solid #2a2a3a",
  },
  fileName: {
    flex: 1,
    fontSize: 13,
    color: "#c8c8e0",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  fileSize: {
    fontSize: 11,
    color: "#505060",
    whiteSpace: "nowrap",
  },
  removeBtn: {
    background: "none",
    border: "none",
    color: "#606070",
    fontSize: 18,
    cursor: "pointer",
    lineHeight: 1,
    padding: "0 4px",
  },
  submit: {
    padding: "14px 28px",
    background: "linear-gradient(135deg, #7c5cbf, #4e3d8a)",
    border: "none",
    borderRadius: 10,
    color: "#fff",
    fontSize: 15,
    fontWeight: 600,
    cursor: "pointer",
    transition: "opacity 0.15s",
    alignSelf: "flex-start",
  },
};
