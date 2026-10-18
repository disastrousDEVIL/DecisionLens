# DecisionLens

Benchmark and compare TypeSafe Jev, Cloudflare Clef-flash, and OpenAI Decisions across accuracy, calibration, latency, cost, and robustness.

DecisionLens is independent and not affiliated with TypeSafe, Cloudflare, or OpenAI.

## System One and typed decisions

DecisionLens evaluates systems that turn shared evidence into a bounded, machine-readable decision rather than open-ended generated text. A request supplies evidence plus a typed question, then receives a probability for a predicate, a selection from fixed choices, or a score against ordered levels.

“System One Model” is TypeSafe’s term for models optimized for fast, structured, probabilistic decisions in software. It is not a general label for every provider in this repository. [TypeSafe’s Jev announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

## Providers in this benchmark

### TypeSafe Jev

Jev is TypeSafe’s public System One Model. Its `/v1/systemone` API accepts shared state and named typed questions, then returns decisions for yes/no predicates, fixed choices, and ordered scores, together with token usage. [Jev API reference](https://api.typesafe.ai/redoc)

### Cloudflare Clef-flash

Clef-flash is Cloudflare’s hosted 9B multimodal decision model. It accepts text, structured JSON, images, or video and returns typed answers with probabilities for the permitted options. DecisionLens uses its Workers AI REST endpoint. [Cloudflare model documentation](https://developers.cloudflare.com/ai/models/%40cf/cloudflare/clef-flash/)

### OpenAI Decisions

OpenAI Decisions is a dedicated API for typed predicate, choice, and score answers over text and image input. It currently uses `gpt-6-luna` and is documented as a public beta API. [OpenAI Decisions guide](https://developers.openai.com/api/docs/guides/decisions)

## Product preview

### Benchmark scorecard

![DecisionLens benchmark scorecard](media/benchmark-scorecard.png)

### Live provider comparison

![DecisionLens live provider comparison workbench](media/live-comparison-workbench.png)

## Current foundation

- FastAPI API with provider availability reporting and `POST /api/v1/compare`.
- Isolated adapters for Jev, Clef-flash, and OpenAI Decisions.
- Safe server-side environment configuration; credentials never reach the browser.
- Next.js dashboard with a live comparison workbench and benchmark scorecards.
- A 100-case starter suite across binary, choice, ordinal, ambiguity, invariance, and paired wording tests.
- In-memory benchmark jobs with accuracy, macro-F1, categorical Brier loss, expected calibration error, p50/p95 latency, invalid and API-failure rates, cost estimates, disagreement, robustness, and observed throughput.
- Provider and API validation tests that do not make paid external calls.

Dataset upload is available at `POST /api/v1/datasets/upload`. Benchmark jobs are intentionally in memory for this local MVP: restarting the backend removes prior runs. Persistent jobs and a detailed result explorer remain future work.

## Configure providers

Copy the example file, then supply only the providers you want to use:

```bash
cp .env.example .env
```

| Provider | Required configuration |
| --- | --- |
| TypeSafe Jev | `TYPESAFE_API_KEY` |
| Cloudflare Clef-flash | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` |
| OpenAI Decisions | `OPENAI_API_KEY`, `OPENAI_DECISIONS_ENABLED=true` |

## Run locally

```bash
cd backend
uv sync --group dev
uv run uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. API documentation is available at `http://localhost:8000/docs`.

## Verify

```bash
make api-test
make api-lint
```

## API available now

```text
GET  /health
GET  /api/v1/providers
POST /api/v1/compare
GET  /api/v1/datasets
POST /api/v1/datasets/upload
POST /api/v1/benchmarks/run
GET  /api/v1/benchmarks/{run_id}
```

## License

This project is licensed under the [MIT License](LICENSE).

You are free to use, modify, and distribute this software under the terms of
the license. Keep the license and copyright notice with substantial copies of
the project.

## Author

Krish Batra

- Website: [vybecode.in](https://vybecode.in)
- Email: [krishbatra3@gmail.com](mailto:krishbatra3@gmail.com)
- LinkedIn: krish-batra

