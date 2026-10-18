"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Provider = { slug: string; display_name: string; available: boolean };
type Result = { provider: string; model?: string; latency_ms_e2e: number; answers: Array<{ selected_option?: string; probabilities?: Record<string, number> }>; error?: string };
type ProviderMetrics = { accuracy: number | null; macro_f1: number | null; brier: number | null; expected_calibration_error: number | null; latency_ms: number | null; p50_latency_ms: number | null; p95_latency_ms: number | null; failure_rate: number | null; refusal_rate: number | null; invalid_answer_rate: number | null; cost_per_1000_usd: number | null };
type Benchmark = { id: string; status: string; completed: number; total: number; metrics?: { providers: Record<string, ProviderMetrics>; comparison: { disagreement_rate: number | null; robustness: Record<string, number | null>; robustness_coverage?: Record<string, number | null>; observed_throughput_per_second?: number } } };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "/api";
const labels: Record<string, string> = { jev: "TypeSafe Jev", "clef-flash": "Cloudflare Clef-flash", "openai-decisions": "OpenAI Decisions" };
const providerDescriptions: Record<string, string> = {
  jev: "Built for quick, structured decisions. It returns an answer and how confident it is.",
  "clef-flash": "A small Cloudflare model for fast, lower-cost decisions. Useful when speed matters most.",
  "openai-decisions": "OpenAI's Decisions API returns structured answers. It supports yes/no questions, choices, and scores.",
};
const scorecards = [
  ["Accuracy", "Correct decisions across every benchmark case", "accuracy", "cyan"],
  ["Macro-F1", "Balances performance across answer labels", "macro_f1", "cyan"],
  ["Calibration loss", "Lower is better; confidence versus reality", "brier", "violet"],
  ["Calibration error", "Gap between predicted confidence and actual accuracy", "expected_calibration_error", "violet"],
  ["Normal speed (p50)", "A typical end-to-end response time", "p50_latency_ms", "orange"],
  ["Slow-case speed (p95)", "The slower end of the response-time range", "p95_latency_ms", "orange"],
  ["Provider refusals", "The provider declined to answer", "refusal_rate", "green"],
  ["Invalid answers", "Responses that arrived but could not be scored", "invalid_answer_rate", "green"],
  ["API request failures", "Timeouts, provider errors, or unavailable requests", "failure_rate", "green"],
  ["Cost per 1,000", "Estimated from recorded usage; unavailable where pricing is unmapped", "cost_per_1000_usd", "violet"],
];

type MetricName = keyof ProviderMetrics;

function confidence(result: Result) {
  const values = Object.values(result.answers[0]?.probabilities ?? {});
  return values.length ? `${Math.max(...values) * 100}%` : "—";
}

function selectedAnswer(result: Result) {
  const answer = result.answers[0];
  if (answer?.selected_option) return answer.selected_option;
  const probabilities = answer?.probabilities ?? {};
  return Object.entries(probabilities).sort(([, left], [, right]) => right - left)[0]?.[0] ?? "—";
}

export default function Home() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [scenario, setScenario] = useState("Mochi is curled up in a sunny spot, purring softly with relaxed ears and half-closed eyes.");
  const [results, setResults] = useState<Result[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [apiHealthy, setApiHealthy] = useState(false);
  const [benchmark, setBenchmark] = useState<Benchmark | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/providers`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error("API unavailable")))
      .then(setProviders)
      .catch(() => setError("Dashboard is offline. Start the API to run comparisons."));
  }, []);
  useEffect(() => {
    async function checkHealth() {
      try {
        const response = await fetch(`${API_URL}/health`, { cache: "no-store" });
        const data = await response.json();
        setApiHealthy(response.ok && data.status === "ok");
      } catch {
        setApiHealthy(false);
      }
    }
    void checkHealth();
    const interval = window.setInterval(checkHealth, 15_000);
    return () => window.clearInterval(interval);
  }, []);
  const available = useMemo(() => providers.filter((provider) => provider.available), [providers]);
  const apiConnected = apiHealthy;

  useEffect(() => {
    if (!benchmark || benchmark.status === "completed") return;
    const interval = window.setInterval(async () => {
      const response = await fetch(`${API_URL}/benchmarks/${benchmark.id}`);
      if (response.ok) setBenchmark(await response.json());
    }, 2_000);
    return () => window.clearInterval(interval);
  }, [benchmark]);

  async function startBenchmark() {
    setError("");
    const response = await fetch(`${API_URL}/benchmarks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ dataset_id: "starter-v1", providers: available.map((provider) => provider.slug) }) });
    if (!response.ok) { setError("Could not start the benchmark."); return; }
    setBenchmark(await response.json());
  }

  function metricRows(metric: MetricName) {
    if (!benchmark?.metrics?.providers) return [];
    const values = Object.entries(benchmark.metrics.providers).map(([slug, result]) => ({ slug, value: result[metric] }));
    const ceiling = Math.max(...values.map((item) => item.value ?? 0), 1);
    const percentMetric = ["accuracy", "brier", "failure_rate", "refusal_rate", "invalid_answer_rate"].includes(metric);
    return values.map((item) => ({ ...item, width: typeof item.value !== "number" ? 0 : percentMetric ? Math.min(item.value * 100, 100) : (item.value / ceiling) * 100 }));
  }

  function formatMetric(metric: MetricName, value: number | null | undefined) {
    if (typeof value !== "number") return "—";
    if (metric === "p50_latency_ms" || metric === "p95_latency_ms" || metric === "latency_ms") return `${Math.round(value)} ms`;
    if (metric === "cost_per_1000_usd") return `$${value.toFixed(3)}`;
    return `${(value * 100).toFixed(1)}%`;
  }

  async function runComparison(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!available.length) return;
    setRunning(true); setError("");
    try {
      const response = await fetch(`${API_URL}/compare`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ providers: available.map((provider) => provider.slug), decision: { state: scenario, questions: [{ id: "decision", primitive: "binary", instructions: "Is this a positive situation?" }] } }) });
      if (!response.ok) throw new Error("Comparison failed");
      setResults((await response.json()).results);
    } catch { setError("The comparison could not finish. Check provider credentials and the API service."); }
    finally { setRunning(false); }
  }

  const cards = providers.length ? providers : Object.entries(labels).map(([slug, display_name]) => ({ slug, display_name, available: false }));
  return <main>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">D</span><span>DecisionLens</span></div><nav aria-label="Dashboard sections"><a className="active" href="#overview">Overview</a><a href="#compare">Compare live</a><a href="#quality">Quality metrics</a><a href="#method">Benchmark method</a></nav></aside>
    <section className="content">
      <header id="overview" className="topbar"><div><p className="eyebrow">Decision intelligence workspace</p><h1>See the trade-offs behind every answer.</h1><p className="lede">Evaluate bounded decisions across accuracy, calibration, speed, cost, and resilience—not a single opaque score.</p></div><div className="run-state"><span className={apiConnected ? "pulse" : "dot"} /> {apiConnected ? "API connected" : "API unavailable"}<br /><strong>{available.length} providers ready</strong></div></header>
      <section className="provider-row" aria-label="Decision providers">{cards.map((provider) => <article className="provider-card" key={provider.slug} style={{ minHeight: "112px" }}><h2 style={{ margin: "0 0 10px" }}>{provider.display_name}</h2><p>{providerDescriptions[provider.slug]}</p></article>)}</section>
      <section id="quality" className="section-heading"><div><p className="eyebrow">Benchmark scorecard</p><h2>Quality you can defend</h2></div><button disabled={!available.length || benchmark?.status === "running"} onClick={startBenchmark}>{benchmark?.status === "running" ? `Running ${benchmark.completed}/${benchmark.total}` : "Run 100-case starter suite"}</button></section>
      {benchmark?.metrics && <section className="comparison-strip" aria-label="Cross-provider benchmark metrics"><article><span>Provider disagreement</span><b>{benchmark.metrics.comparison.disagreement_rate === null ? "—" : `${(benchmark.metrics.comparison.disagreement_rate * 100).toFixed(1)}%`}</b><small>Cases where completed providers chose different answers.</small></article><article><span>Wording robustness</span><div>{Object.entries(benchmark.metrics.comparison.robustness).map(([slug, value]) => <b key={slug}>{labels[slug]}: {value === null ? "—" : `${(value * 100).toFixed(1)}%`} <small>({benchmark.metrics?.comparison.robustness_coverage?.[slug] === null || benchmark.metrics?.comparison.robustness_coverage?.[slug] === undefined ? "—" : `${(benchmark.metrics.comparison.robustness_coverage[slug] * 100).toFixed(0)}% coverage`})</small></b>)}</div><small>Same answer across every paired equivalent wording; refusals reduce coverage.</small></article><article><span>Observed throughput</span><b>{benchmark.metrics.comparison.observed_throughput_per_second?.toFixed(2) ?? "—"} decisions/sec</b><small>Actual completed provider decisions in this standard run.</small></article></section>}
      <section className="score-grid">{scorecards.map(([name, description, metricName, accent]) => <article className={`score-card ${accent}`} key={name}><p>{name}</p>{metricRows(metricName as MetricName).length ? <div className="metric-list">{metricRows(metricName as MetricName).map((item) => <div className="metric-row" key={item.slug}><span>{labels[item.slug]}</span><b>{formatMetric(metricName as MetricName, item.value)}</b><i><em style={{ width: `${item.width}%` }} /></i></div>)}</div> : <strong className="metric-value">—</strong>}<small>{description}</small></article>)}</section>
      <section id="compare" className="workbench"><div className="workbench-intro"><p className="eyebrow">Live comparison</p><h2>Decision workbench</h2><p>Send the same bounded question to every connected provider. Inspect disagreement before you create a benchmark.</p></div><form onSubmit={runComparison}><label htmlFor="scenario">Scenario</label><textarea id="scenario" value={scenario} onChange={(event) => setScenario(event.target.value)} /><div className="question-row"><span>Question</span><strong>Is this a positive situation?</strong><span className="binary">Binary</span></div><button disabled={running || !available.length} type="submit">{running ? "Comparing…" : `Compare ${available.length || ""} providers`}</button></form>{error && <p className="error" role="alert">{error}</p>}<div className="live-results" aria-live="polite">{results.length ? results.map((result) => <article key={result.provider} className="result-card"><div><p>{labels[result.provider] ?? result.provider}</p><small>{result.model ?? "Decision response"}</small></div><strong>{result.error ?? selectedAnswer(result)}</strong><div><span>Confidence</span><b>{confidence(result)}</b></div><div><span>Latency</span><b>{Math.round(result.latency_ms_e2e)} ms</b></div></article>) : <p className="empty-state">Your first live comparison will appear here.</p>}</div></section>
      <section id="method" className="method-grid"><article><span>01</span><h3>Correctness</h3><p>Accuracy, macro-F1, and error slices by task, domain, and candidate count.</p></article><article><span>02</span><h3>Confidence</h3><p>Brier score, expected calibration error, and reliability curves—not self-reported certainty.</p></article><article><span>03</span><h3>Operations</h3><p>p50/p95 latency, per-decision cost, failures, and performance under perturbation.</p></article></section>
    </section>
  </main>;
}
