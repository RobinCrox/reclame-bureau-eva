import { useState } from "react";

const API_URL = "http://localhost:8000/campaign";

export default function App() {
  const [productDescription, setProductDescription] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleGenerate() {
    if (!productDescription.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_description: productDescription }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      setResult(await res.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <h1 style={s.title}>Campaign Generator</h1>
        <p style={s.subtitle}>Describe your product and get a full marketing campaign in seconds.</p>
      </div>

      {/* Input card */}
      <div style={s.card}>
        <label style={s.label}>Product Description</label>
        <textarea
          style={s.textarea}
          rows={5}
          placeholder="e.g. EcoBrews — a subscription coffee brand that sources beans exclusively from regenerative farms..."
          value={productDescription}
          onChange={(e) => setProductDescription(e.target.value)}
        />
        <button
          style={{ ...s.button, ...(loading || !productDescription.trim() ? s.buttonDisabled : {}) }}
          onClick={handleGenerate}
          disabled={loading || !productDescription.trim()}
        >
          {loading ? "Running agents…" : "Generate Campaign"}
        </button>
        {loading && (
          <p style={s.loadingNote}>
            ⏳ This takes 60–90 seconds — Agents 1 → 2 → 3 → (4 + 5 + 6 in parallel) → 7
          </p>
        )}
        {error && <p style={s.error}>⚠️ {error}</p>}
      </div>

      {/* Results */}
      {result && (
        <div style={s.results}>

          <Section title="Audience Profile" icon="👥">
            <Grid>
              <Stat label="Age" value={result.audience_profile.target_demographic.age} />
              <Stat label="Gender" value={result.audience_profile.target_demographic.gender} />
              <Stat label="Location" value={result.audience_profile.target_demographic.location} />
            </Grid>
            <Stat label="Lifestyle" value={result.audience_profile.lifestyle} />
            <Row>
              <BulletList label="Pain Points" items={result.audience_profile.pain_points} />
              <BulletList label="Motivations" items={result.audience_profile.motivations} />
            </Row>
            <BulletList label="Where They Spend Time Online" items={result.audience_profile.online_presence} horizontal />
          </Section>

          <Section title="Positioning Strategy" icon="🎯">
            <Stat label="Campaign Tone" value={result.positioning_strategy.campaign_tone} />
            <Stat label="Campaign Angle" value={result.positioning_strategy.campaign_angle} />
            <Highlight label="Unique Selling Point" value={result.positioning_strategy.unique_selling_point} />
            <BulletList label="Key Messages" items={result.positioning_strategy.key_messages} />
          </Section>

          <Section title="Campaign Brief" icon="📋">
            <Highlight label="Objective" value={result.campaign_brief.campaign_objective} />
            <Stat label="Target Audience" value={result.campaign_brief.target_audience_summary} />
            <Stat label="Tone of Voice" value={result.campaign_brief.tone_of_voice} />
            <Row>
              <BulletList label="Key Messages" items={result.campaign_brief.key_messages} />
              <BulletList label="Success Metrics" items={result.campaign_brief.success_metrics} />
            </Row>
            <BulletList label="Deliverables" items={result.campaign_brief.deliverables} />
          </Section>

          <Section title="Taglines" icon="✍️">
            <div style={s.taglineGrid}>
              {result.taglines.taglines.map((t, i) => (
                <div key={i} style={s.taglineCard}>
                  <p style={s.taglineText}>"{t.tagline}"</p>
                  <p style={s.taglineExpl}>{t.explanation}</p>
                </div>
              ))}
            </div>
          </Section>

          <Section title="Instagram Post" icon="📸">
            <Row>
              <div style={{ flex: 2 }}>
                <Stat label="Caption" value={result.instagram_post.caption} />
              </div>
              <div style={{ flex: 1 }}>
                <p style={s.fieldLabel}>Hashtags</p>
                <div style={s.hashtagWrap}>
                  {result.instagram_post.hashtags.map((h, i) => (
                    <span key={i} style={s.hashtag}>{h}</span>
                  ))}
                </div>
              </div>
            </Row>
          </Section>

          <Section title="Email Copy" icon="📧">
            <div style={s.emailSubject}>
              <span style={s.fieldLabel}>Subject line</span>
              <p style={s.subjectText}>{result.email_copy.subject_line}</p>
            </div>
            <Stat label="Body" value={result.email_copy.body} />
          </Section>

          <Section title="Quality Check Report" icon="🔍">
            <div style={s.assessmentBox}>
              <p style={s.fieldLabel}>Overall Assessment</p>
              <p style={s.assessmentText}>{result.review_report.overall_assessment}</p>
            </div>
            {result.review_report.issues.length === 0 ? (
              <p style={s.noIssues}>✅ No issues flagged.</p>
            ) : (
              <div>
                <p style={s.fieldLabel}>{result.review_report.issues.length} issue{result.review_report.issues.length > 1 ? "s" : ""} flagged</p>
                {result.review_report.issues.map((issue, i) => (
                  <div key={i} style={s.issueCard}>
                    <p style={s.issueAsset}>{issue.asset}</p>
                    <p style={s.issueSmallLabel}>Issue</p>
                    <p style={s.issueBody}>{issue.issue}</p>
                    <p style={s.issueSmallLabel}>Suggested Fix</p>
                    <p style={s.issueBody}>{issue.suggested_fix}</p>
                  </div>
                ))}
              </div>
            )}
          </Section>

        </div>
      )}
    </div>
  );
}

// ── Layout components ──────────────────────────────────────────────

function Section({ title, icon, children }) {
  return (
    <div style={s.section}>
      <div style={s.sectionHeader}>
        <span style={s.sectionIcon}>{icon}</span>
        <h2 style={s.sectionTitle}>{title}</h2>
      </div>
      <div style={s.sectionBody}>{children}</div>
    </div>
  );
}

function Grid({ children }) {
  return <div style={s.grid}>{children}</div>;
}

function Row({ children }) {
  return <div style={s.row}>{children}</div>;
}

function Stat({ label, value }) {
  return (
    <div style={s.statBlock}>
      <p style={s.fieldLabel}>{label}</p>
      <p style={s.fieldValue}>{value}</p>
    </div>
  );
}

function Highlight({ label, value }) {
  return (
    <div style={s.highlightBlock}>
      <p style={s.fieldLabel}>{label}</p>
      <p style={s.highlightValue}>{value}</p>
    </div>
  );
}

function BulletList({ label, items, horizontal }) {
  return (
    <div style={s.statBlock}>
      <p style={s.fieldLabel}>{label}</p>
      {horizontal ? (
        <div style={s.pillRow}>
          {items.map((item, i) => <span key={i} style={s.pill}>{item}</span>)}
        </div>
      ) : (
        <ul style={s.list}>
          {items.map((item, i) => <li key={i} style={s.listItem}>{item}</li>)}
        </ul>
      )}
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────

const s = {
  page: {
    maxWidth: 900,
    margin: "0 auto",
    padding: "48px 24px 80px",
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: 700,
    color: "#111",
    letterSpacing: "-0.5px",
  },
  subtitle: {
    marginTop: 6,
    color: "#666",
    fontSize: 16,
  },
  card: {
    background: "#fff",
    border: "1px solid #e5e5e5",
    borderRadius: 12,
    padding: 24,
    marginBottom: 40,
  },
  label: {
    display: "block",
    fontWeight: 600,
    fontSize: 14,
    color: "#444",
    marginBottom: 8,
  },
  textarea: {
    width: "100%",
    padding: "12px 14px",
    fontSize: 15,
    color: "#1a1a1a",
    background: "#fafafa",
    border: "1px solid #ddd",
    borderRadius: 8,
    resize: "vertical",
    outline: "none",
    lineHeight: 1.6,
  },
  button: {
    marginTop: 14,
    padding: "11px 28px",
    fontSize: 15,
    fontWeight: 600,
    background: "#111",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    transition: "opacity 0.15s",
  },
  buttonDisabled: {
    opacity: 0.45,
    cursor: "not-allowed",
  },
  loadingNote: {
    marginTop: 12,
    fontSize: 13,
    color: "#888",
  },
  error: {
    marginTop: 12,
    color: "#c0392b",
    fontSize: 14,
  },
  results: {
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  section: {
    background: "#fff",
    border: "1px solid #e5e5e5",
    borderRadius: 12,
    overflow: "hidden",
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "16px 24px",
    borderBottom: "1px solid #f0f0f0",
    background: "#fafafa",
  },
  sectionIcon: {
    fontSize: 18,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: 700,
    color: "#111",
  },
  sectionBody: {
    padding: 24,
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 16,
  },
  row: {
    display: "flex",
    gap: 24,
    flexWrap: "wrap",
  },
  statBlock: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  highlightBlock: {
    background: "#f7f6f3",
    border: "1px solid #e8e8e4",
    borderRadius: 8,
    padding: "14px 16px",
  },
  fieldLabel: {
    fontSize: 11,
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    color: "#999",
    marginBottom: 4,
  },
  fieldValue: {
    fontSize: 15,
    color: "#222",
    lineHeight: 1.65,
    whiteSpace: "pre-wrap",
  },
  highlightValue: {
    fontSize: 15,
    color: "#111",
    fontWeight: 500,
    lineHeight: 1.65,
  },
  list: {
    paddingLeft: 18,
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  listItem: {
    fontSize: 15,
    color: "#333",
    lineHeight: 1.6,
  },
  pillRow: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 4,
  },
  pill: {
    background: "#f0f0f0",
    borderRadius: 20,
    padding: "4px 12px",
    fontSize: 13,
    color: "#444",
  },
  taglineGrid: {
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  taglineCard: {
    borderLeft: "3px solid #111",
    paddingLeft: 16,
  },
  taglineText: {
    fontSize: 17,
    fontWeight: 600,
    fontStyle: "italic",
    color: "#111",
    marginBottom: 6,
  },
  taglineExpl: {
    fontSize: 14,
    color: "#555",
    lineHeight: 1.65,
  },
  hashtagWrap: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 4,
  },
  hashtag: {
    background: "#e8f0fe",
    color: "#1a56db",
    borderRadius: 20,
    padding: "4px 12px",
    fontSize: 13,
    fontWeight: 500,
  },
  emailSubject: {
    background: "#f7f6f3",
    border: "1px solid #e8e8e4",
    borderRadius: 8,
    padding: "14px 16px",
  },
  subjectText: {
    fontSize: 16,
    fontWeight: 600,
    color: "#111",
  },
  assessmentBox: {
    background: "#f7f6f3",
    borderRadius: 8,
    padding: "14px 16px",
  },
  assessmentText: {
    fontSize: 15,
    color: "#333",
    lineHeight: 1.7,
  },
  noIssues: {
    color: "#27ae60",
    fontWeight: 600,
    fontSize: 15,
  },
  issueCard: {
    border: "1px solid #f5c518",
    background: "#fffdf0",
    borderRadius: 8,
    padding: 16,
    marginTop: 12,
  },
  issueAsset: {
    fontWeight: 700,
    fontSize: 14,
    color: "#111",
    marginBottom: 10,
  },
  issueSmallLabel: {
    fontSize: 11,
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    color: "#aaa",
    margin: "10px 0 4px",
  },
  issueBody: {
    fontSize: 14,
    color: "#444",
    lineHeight: 1.65,
  },
};
