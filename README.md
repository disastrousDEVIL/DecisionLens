# DecisionLens

Benchmark and compare TypeSafe Jev, Cloudflare Clef-flash, and OpenAI Decisions across accuracy, calibration, latency, cost, and robustness.

DecisionLens is independent and not affiliated with TypeSafe, Cloudflare, or OpenAI.

## Current foundation

- FastAPI API with provider availability reporting and `POST /api/v1/compare`.
- Isolated adapters for Jev, Clef-flash, and OpenAI Decisions.
- Safe server-side environment configuration; credentials never reach the browser.
- Next.js dashboard shell.
- Provider and API validation tests that do not make paid external calls.

Dataset upload, persistent benchmark jobs, metrics, and the result explorer are the next implementation phases.

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
```

