const providers = [
  { name: "TypeSafe Jev", detail: "System One" },
  { name: "Cloudflare Clef-flash", detail: "Hosted decision model" },
  { name: "OpenAI Decisions", detail: "GPT-6 Luna" },
];

export default function Home() {
  return (
    <main>
      <header>
        <p className="eyebrow">Decision system evaluation</p>
        <h1>DecisionLens</h1>
        <p className="lede">Benchmark bounded AI decisions with evidence—not a single opaque score.</p>
      </header>
      <section className="provider-grid" aria-label="Configured providers">
        {providers.map((provider) => (
          <article key={provider.name}>
            <span className="status">Ready to configure</span>
            <h2>{provider.name}</h2>
            <p>{provider.detail}</p>
          </article>
        ))}
      </section>
      <section className="next-step">
        <h2>Foundation in progress</h2>
        <p>Connect provider credentials, upload a labeled dataset, then run the same decision cases across every enabled provider.</p>
      </section>
    </main>
  );
}

