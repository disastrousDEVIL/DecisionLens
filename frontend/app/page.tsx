"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Provider = { slug: string; display_name: string; available: boolean };
type Result = { provider: string; model?: string; latency_ms_e2e: number; answers: Array<{ selected_option?: string; probabilities?: Record<string, number> }>; error?: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const labels: Record<string, string> = { jev: "TypeSafe Jev", "clef-flash": "Cloudflare Clef-flash", "openai-decisions": "OpenAI Decisions" };
const scorecards = [
  ["Accuracy", "Correct decisions against labeled ground truth", "cyan"],
  ["Calibration", "How well confidence matches reality", "violet"],
  ["Robustness", "Stability under wording and noise changes", "orange"],
  ["Cost / 1k", "Estimated cost per thousand decisions", "green"],
];

function confidence(result: Result) {
  const values = Object.values(result.answers[0]?.probabilities ?? {});
  return values.length ? `${Math.max(...values) * 100}%` : "—";
}

export default function Home() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [scenario, setScenario] = useState("Mochi is curled up in a sunny spot, purring softly with relaxed ears and half-closed eyes.");
  const [results, setResults] = useState<Result[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/v1/providers`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("API unavailable")))
      .then(setProviders)
      .catch(() => setError("Dashboard is offline. Start the API to run comparisons."));
  }, []);
  const available = useMemo(() => providers.filter((provider) => provider.available), [providers]);
  const apiConnected = !error && providers.length > 0;

  async function runComparison(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!available.length) return;
    setRunning(true); setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/compare`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ providers: available.map((provider) => provider.slug), decision: { state: scenario, questions: [{ id: "decision", primitive: "binary", instructions: "Is this a positive situation?" }] } }) });
      if (!response.ok) throw new Error("Comparison failed");
      setResults((await response.json()).results);
    } catch { setError("The comparison could not finish. Check provider credentials and the API service."); }
    finally { setRunning(false); }
  }

  const cards = providers.length ? providers : Object.entries(labels).map(([slug, display_name]) => ({ slug, display_name, available: false }));
  return <main>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">D</span><span>DecisionLens</span></div><nav aria-label="Dashboard sections"><a className="active" href="#overview">Overview</a><a href="#compare">Compare live</a><a href="#quality">Quality metrics</a><a href="#method">Benchmark method</a></nav><div className="sidebar-note"><span className="pulse" /> {available.length}/3 providers live</div></aside>
    <section className="content">
      <header id="overview" className="topbar"><div><p className="eyebrow">Decision intelligence workspace</p><h1>See the trade-offs behind every answer.</h1><p className="lede">Evaluate bounded decisions across accuracy, calibration, speed, cost, and resilience—not a single opaque score.</p></div><div className="run-state"><span className={apiConnected ? "pulse" : "dot"} /> {apiConnected ? "API connected" : "API unavailable"}<br /><strong>{available.length} providers ready</strong></div></header>
      <section className="provider-row" aria-label="Provider connections">{cards.map((provider) => <article className="provider-card" key={provider.slug}><div className="provider-heading"><span className={provider.available ? "dot ready" : "dot"} />{provider.available ? "Connected" : "Checking"}</div><h2>{provider.display_name}</h2><p>{provider.slug === "jev" ? "System One decision engine" : provider.slug === "clef-flash" ? "Fast hosted decision model" : "Structured decision API"}</p></article>)}</section>
      <section id="quality" className="section-heading"><div><p className="eyebrow">Benchmark scorecard</p><h2>Quality you can defend</h2></div><span className="data-badge">Run a labeled dataset to populate</span></section>
      <section className="score-grid">{scorecards.map(([name, description, accent]) => <article className={`score-card ${accent}`} key={name}><p>{name}</p><strong>—</strong><small>{description}</small></article>)}</section>
      <section id="compare" className="workbench"><div className="workbench-intro"><p className="eyebrow">Live comparison</p><h2>Decision workbench</h2><p>Send the same bounded question to every connected provider. Inspect disagreement before you create a benchmark.</p></div><form onSubmit={runComparison}><label htmlFor="scenario">Scenario</label><textarea id="scenario" value={scenario} onChange={(event) => setScenario(event.target.value)} /><div className="question-row"><span>Question</span><strong>Is this a positive situation?</strong><span className="binary">Binary</span></div><button disabled={running || !available.length} type="submit">{running ? "Comparing…" : `Compare ${available.length || ""} providers`}</button></form>{error && <p className="error" role="alert">{error}</p>}<div className="live-results" aria-live="polite">{results.length ? results.map((result) => <article key={result.provider} className="result-card"><div><p>{labels[result.provider] ?? result.provider}</p><small>{result.model ?? "Decision response"}</small></div><strong>{result.error ?? result.answers[0]?.selected_option ?? "—"}</strong><div><span>Confidence</span><b>{confidence(result)}</b></div><div><span>Latency</span><b>{Math.round(result.latency_ms_e2e)} ms</b></div></article>) : <p className="empty-state">Your first live comparison will appear here.</p>}</div></section>
      <section id="method" className="method-grid"><article><span>01</span><h3>Correctness</h3><p>Accuracy, macro-F1, and error slices by task, domain, and candidate count.</p></article><article><span>02</span><h3>Confidence</h3><p>Brier score, expected calibration error, and reliability curves—not self-reported certainty.</p></article><article><span>03</span><h3>Operations</h3><p>p50/p95 latency, per-decision cost, failures, and performance under perturbation.</p></article></section>
    </section>
  </main>;
}
