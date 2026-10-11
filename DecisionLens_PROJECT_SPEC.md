# DecisionLens — Product & Technical Specification

**Document type:** Product Requirements + Technical Design + Benchmark Methodology  
**Status:** Implementation-ready v1.0  
**Date:** 2026-10-01  
**Project name:** DecisionLens
**Primary implementer:** Codex / software engineer  

---

## 1. Executive Summary

DecisionLens is a developer-facing benchmarking and analysis platform for **bounded AI decision systems**. It benchmarks and compares Jev, Cloudflare Clef-flash, and OpenAI Decisions API across accuracy, calibration, latency, cost, and robustness. Its first release compares three providers:

1. **TypeSafe Jev**
2. **Cloudflare Clef-flash**
3. **OpenAI Decisions API**

The product is not an agent framework and does not execute downstream actions. It answers one question: **how do different decision systems behave on the same bounded decision problems?**

DecisionLens must compare correctness, probability quality, latency, reliability, robustness, throughput, and cost while preserving full run metadata so results can be reproduced and audited.

The application must support existing external benchmark suites rather than inventing a competing benchmark from scratch. In particular, the existing Hanno Labs DecisionBench should be treated as an ingestible benchmark suite, not as this project's name or proprietary dataset.

---

## 2. Problem Statement

General-purpose LLMs are increasingly being supplemented by systems designed specifically for classification, routing, scoring, verification, moderation, and other bounded decisions. Jev, Cloudflare Clef-flash, and OpenAI Decisions represent different implementations of this idea.

Developers need a fair way to answer questions such as:

- Which system is most accurate for a specific decision shape?
- Are the returned probabilities calibrated enough to support automation thresholds?
- How much does accuracy degrade as the number of candidates grows?
- How stable is a decision under paraphrasing, option reordering, ambiguity, and repeated execution?
- What are the actual end-to-end latency and throughput characteristics?
- What is the cost per decision and cost per correct decision?
- Which provider fails most often or returns incomplete/invalid results?
- Does batching multiple questions materially change performance or economics?

Existing leaderboards are useful but do not provide a single interactive environment for provider-by-provider inspection, stress testing, custom datasets, disagreement analysis, and reproducible experiment tracking.

---

## 3. Product Goals

### 3.1 Primary goals

DecisionLens shall:

- Compare Jev, Cloudflare Clef-flash, and OpenAI Decisions through a common provider abstraction.
- Run the same semantically equivalent decision tasks against every enabled provider.
- Support binary, categorical, ordinal, and multi-label decision workloads.
- Preserve native provider responses while also normalizing them into a common schema.
- Measure accuracy, calibration/probability quality, performance, economics, robustness, and reliability.
- Support both public benchmark suites and user-uploaded labeled datasets.
- Make disagreements and confidently wrong decisions easy to inspect.
- Produce reproducible run artifacts and machine-readable exports.
- Present results in a clean evaluation/observability dashboard rather than a chatbot interface.

### 3.2 Secondary goals

- Make it easy to add future decision providers such as Bosun, Reflex, or other System One-compatible implementations.
- Support provider capability detection so unavailable features do not invalidate a run.
- Make benchmark methodology explicit and visible in the UI.

---

## 4. Non-Goals

The following are explicitly out of scope for v1:

- LangGraph, Google ADK, CrewAI, or any other agent framework.
- Multi-agent orchestration.
- MCP execution.
- RAG pipelines or vector databases.
- Autonomous actions based on decisions.
- Model fine-tuning or training.
- Building a new foundation model.
- Replacing existing public benchmarks with a new leaderboard dataset.
- Multi-tenant SaaS billing/authentication.
- Mobile applications.
- Production-grade decision routing for customer applications.

Do not add these technologies simply to increase stack complexity.

---

## 5. Provider Scope

### 5.1 Jev

Implement a TypeSafe provider using the `/v1/systemone` interface.

Expected native primitives include:

- Noul / yes-no style decision
- Choice
- Score

Preserve returned probability/confidence information and native usage metadata.

### 5.2 Cloudflare Clef-flash

Cloudflare Clef-flash is a hosted decision model available through Cloudflare Workers AI. It accepts typed System One-style questions and returns structured answers with probability information.

The adapter must isolate Cloudflare's Workers AI request and response mapping from domain logic and record:

- model identifier (`@cf/cloudflare/clef-flash`)
- Cloudflare endpoint type
- provider-reported usage and request metadata when available

Headline latency comparisons must use **end-to-end client-observed latency**.

### 5.3 OpenAI Decisions API

OpenAI Decisions is in public beta. Its public contract may change.

Therefore:

- implement it behind a provider adapter and configuration flag
- do not hard-code undocumented endpoint details into domain logic
- keep request/response mapping isolated in the provider module
- capability-detect probabilities/confidence, batching, image input, usage, and cost metadata
- if probability distributions are unavailable, probability-dependent metrics must be shown as `N/A`, not approximated
- if OpenAI credentials are unavailable or the provider is disabled, the application must still run with Jev and Cloudflare Clef-flash and expose OpenAI Decisions as `unavailable`

Never fabricate probabilities by asking another LLM to estimate confidence.

---

## 6. Core Benchmark Primitives

The normalized domain model must support the following decision shapes.

### 6.1 Binary decision

Examples:

- allowed / blocked
- relevant / irrelevant
- claim supported / unsupported

Normalized representation:

- two explicit labels
- probability distribution when the provider supplies one
- predicted label
- confidence derived only from provider-native probability/confidence signals

### 6.2 Single-choice categorical decision

Examples:

- billing / account / technical / fraud
- choose one category from N candidates

Required candidate-cardinality test bands:

- 2
- 5
- 10
- 25
- 50
- 100

Optional extension up to provider limits (for example, 255) must be supported when all compared providers can represent the task.

### 6.3 Ordinal score

Examples:

- low / medium / high
- 1–5 relevance
- severity level 0–4

For cross-provider fairness, v1 ordinal tasks are represented as an **ordered finite set**, not unrestricted numeric regression.

### 6.4 Multi-label decision

Represent multi-label classification as multiple independent binary questions over the same state.

Example:

- contains billing issue?
- contains fraud signal?
- requires human review?

### 6.5 Batched independent decisions

Where providers support multiple questions over one state, benchmark this explicitly.

Two modes are required:

- `single_question`: one semantic question per request
- `native_batch`: exploit the provider's native multi-question capability

Results from these modes must not be mixed into one latency/cost headline.

---

## 7. Benchmark Modes

### 7.1 Protocol-Parity Mode — primary/headline

Purpose: maximize fairness.

Rules:

- same source state
- same semantic question
- same allowed labels/options
- same candidate order after deterministic seeded shuffling
- no provider-specific prompt optimization beyond the minimum needed to map to the native API
- same dataset revision
- same evaluation logic

This mode produces the headline cross-provider comparisons.

### 7.2 Native-Optimized Mode — secondary

Purpose: measure realistic best-use performance.

Providers may use native batching or documented provider-specific features.

Results must be clearly labeled and never combined with protocol-parity results.

---

## 8. Dataset Strategy

### 8.1 External benchmark suites

DecisionLens should support benchmark adapters rather than copy datasets into application code.

Initial external suites:

1. **Hanno Labs DecisionBench** — primary external suite where licensing permits. Pin the exact dataset revision/hash.
2. **S1Bench-compatible public tasks** — optional second external suite where licensing and redistribution rules permit.

Dataset adapters must preserve:

- suite name
- suite version/revision
- task ID
- domain
- primitive
- candidate count
- expected answer
- reasoning/metadata fields if present

### 8.2 DecisionLens Stress Suite

Create a small project-owned stress suite focused on behavior not captured well by static leaderboards.

It should include:

- paraphrase invariance
- candidate-order sensitivity
- increasing candidate cardinality
- ambiguous inputs
- out-of-distribution labels
- imbalanced classes
- near-duplicate / minimal-edit pairs
- repeated identical calls
- long vs short state representations
- equivalent text state vs JSON state where supported

Stress-suite cases must be frozen and versioned after creation.

Synthetic or LLM-assisted examples may be used only when labels are deterministically known or manually verified. Do not use another model's unreviewed prediction as ground truth.

### 8.3 User datasets

Support CSV and JSONL upload.

Minimum dataset fields:

```text
id
state
question
primitive
options
expected_answer
```

Optional fields:

```text
domain
tags
metadata
ordinal_order
```

Validate the dataset before accepting a benchmark run.

---

## 9. Benchmark Methodology

### 9.1 Reproducibility manifest

Every benchmark run must persist a manifest containing:

- run UUID
- application git commit SHA
- benchmark suite + revision/hash
- random seed
- provider name
- provider model identifier/revision
- provider endpoint type (hosted/local)
- provider configuration
- hardware profile for local models
- serving backend/version for local models
- benchmark mode
- concurrency
- warmup count
- request timeout
- retry policy
- pricing snapshot/version/date
- run start/end timestamps

### 9.2 Candidate ordering

Candidate order can bias classification.

For the primary run:

- shuffle candidate order with a deterministic seed
- use the exact same resulting order for every provider for a given sample

Candidate-order robustness is measured separately by rerunning a frozen subset with multiple deterministic permutations.

### 9.3 Warmup

Before latency measurement, perform configurable provider warmup requests.

Default:

- hosted provider: 5 warmup requests
- Cloudflare Clef-flash: 5 warmup requests

Warmup requests are excluded from benchmark metrics and cost summaries unless the provider charges for them; charged warmup cost may be recorded separately.

### 9.4 Retry policy

Automatically retry only transient infrastructure failures such as:

- HTTP 429
- HTTP 5xx
- connection reset
- timeout where retry is safe

Use capped exponential backoff with jitter.

Never retry merely because the model selected the wrong answer.

Record every retry.

### 9.5 Concurrency profiles

Support:

- 1
- 5
- 20
- 50

Higher values may be configured but should not be default.

Rate-limit responses must be separately reported so provider quotas are not misrepresented as model accuracy failures.

### 9.6 Repeated-run stability

On a configurable stratified subset (default 10%, minimum 100 rows), execute the exact same request five times.

Measure:

- label agreement rate
- probability/confidence standard deviation
- flip rate

### 9.7 Statistical reporting

For headline accuracy/F1/calibration metrics:

- report point estimate
- report 95% bootstrap confidence interval

For paired provider correctness comparisons over the same rows:

- optionally report McNemar's test
- do not hide raw counts behind significance values

Do not produce a single opaque composite score in v1.

---

## 10. Metrics

Metrics must be computed at row level first and then aggregated by:

- provider
- benchmark suite
- task
- primitive
- domain
- candidate-count bucket

### 10.1 Universal metrics

- total rows
- completed rows
- coverage
- top-1 accuracy
- failure rate
- invalid/contract failure rate
- retry count/rate
- p50 latency
- p90 latency
- p95 latency
- p99 latency
- throughput (decisions/sec)
- total cost
- cost per 1,000 decisions
- cost per correct decision

### 10.2 Probability/calibration metrics

Only compute when provider-native probability information is available.

- Expected Calibration Error (ECE)
- Negative Log Likelihood / Log Loss (NLL)
- Brier score
- reliability diagram
- confidence histogram
- risk-coverage curve
- selective accuracy at configured confidence thresholds
- incorrect-above-threshold rate (false-autonomy rate)

Recommended default confidence thresholds:

- 0.50
- 0.70
- 0.80
- 0.90
- 0.95
- 0.99

### 10.3 Binary metrics

- accuracy
- precision
- recall
- F1
- ROC-AUC when probabilities exist and both classes are represented
- PR-AUC for imbalanced datasets
- confusion matrix

### 10.4 Multi-class metrics

- top-1 accuracy
- macro F1
- weighted F1
- per-class precision/recall/F1
- confusion matrix
- NLL when full probabilities exist
- multiclass Brier score when full probabilities exist

If full candidate distributions are available:

- top-3 accuracy
- mean reciprocal rank (optional)

### 10.5 Ordinal metrics

- exact accuracy
- mean absolute ordinal error
- quadratic weighted kappa
- confusion matrix
- ordinal calibration where probabilities are available

### 10.6 Multi-label metrics

- micro F1
- macro F1
- subset/exact-match accuracy
- Hamming loss
- per-label precision/recall

### 10.7 Robustness metrics

- paraphrase consistency rate
- candidate-order consistency rate
- repeated-call agreement rate
- decision flip rate
- confidence variance
- accuracy vs candidate count
- latency vs candidate count
- cost vs candidate count

---

## 11. Fairness Rules for Provider Comparison

These rules are mandatory.

1. Compare all providers using end-to-end client-observed latency in headline charts.
2. Never synthesize missing confidence/probabilities.
3. Never silently exclude provider failures from accuracy. Report both:
   - accuracy over all benchmark rows (failure counts as miss)
   - accuracy over successfully completed rows
4. Keep benchmark dataset revisions pinned.
5. Preserve all raw provider responses.
6. Record provider model/version identifiers whenever exposed.
7. Separate protocol-parity and native-optimized results.
8. Price calculations must use a dated pricing snapshot.
9. Record the provider model identifier and endpoint type for every provider run.
10. Do not claim vendor benchmark results as independently reproduced unless DecisionLens actually ran them.

---

## 12. System Architecture

```text
Browser / Next.js
        |
        v
FastAPI API
        |
        +-------------------+
        |                   |
        v                   v
 Benchmark Service       Dataset Service
        |
        v
 Durable Job Queue (Redis + Celery)
        |
        v
 Benchmark Worker
        |
        +----------------+----------------+
        |                |                |
        v                v                v
 Jev Provider   Cloudflare Clef-flash   OpenAI Decisions
        |                |                |
        +----------------+----------------+
                         |
                         v
               Normalization Layer
                         |
                         v
                  Metrics Engine
                         |
                         v
                    PostgreSQL
```

No agent orchestration layer is permitted in the core architecture.

---

## 13. Technology Stack

### 13.1 Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16+
- Redis 7+
- Celery 5.x for durable benchmark jobs
- HTTPX for asynchronous provider calls
- NumPy
- pandas
- scikit-learn
- SciPy
- `uv` for Python dependency/environment management

### 13.2 Backend quality tooling

- pytest
- pytest-asyncio
- respx for HTTP mocking
- Hypothesis for metric/schema property tests where useful
- Ruff
- mypy
- pre-commit

### 13.3 Frontend

- Next.js (current stable)
- TypeScript with strict mode
- Tailwind CSS
- shadcn/ui
- TanStack Query
- TanStack Table
- Recharts for standard charts
- a matrix/heatmap library only if Recharts is insufficient for confusion matrices
- SSE for benchmark progress updates

### 13.4 Frontend testing

- Vitest
- React Testing Library
- Playwright for end-to-end tests

### 13.5 Infrastructure

- Docker
- Docker Compose
- GitHub Actions

Do not introduce Kubernetes for v1.

---

## 14. Provider Abstraction

Define a capability-aware interface.

```python
class DecisionProvider(Protocol):
    name: str

    async def capabilities(self) -> ProviderCapabilities:
        ...

    async def decide(self, request: NormalizedDecisionRequest) -> ProviderDecisionResponse:
        ...
```

### 14.1 ProviderCapabilities

```text
supports_binary
supports_choice
supports_ordinal
supports_multi_question
supports_full_probabilities
supports_confidence
supports_usage
supports_cost_metadata
supports_json_state
supports_image_state
max_candidates
max_questions_per_request
```

### 14.2 Normalized request

```text
NormalizedDecisionRequest
- request_id
- state: string | JSON object
- questions[]
- metadata
```

Question:

```text
- id
- primitive: binary | choice | ordinal
- instructions
- options[]
- ordered: bool
```

### 14.3 Normalized response

```text
ProviderDecisionResponse
- provider
- model
- request_id
- answers[]
- latency_ms_e2e
- provider_latency_ms (optional)
- usage (optional)
- estimated_cost_usd (optional)
- raw_response
- retries
- error (optional)
```

Answer:

```text
- question_id
- selected_option
- probabilities: map[string, float] | null
- confidence: float | null
- ordinal_expected_value: float | null
```

The raw response must always be stored separately from the normalized representation.

---

## 15. Database Model

Use UUID primary keys and UTC timestamps.

### 15.1 Core tables

`providers`

- id
- slug
- display_name
- enabled
- capability_snapshot JSONB

`datasets`

- id
- name
- source
- revision
- content_hash
- license_metadata JSONB
- row_count

`dataset_samples`

- id
- dataset_id
- external_id
- primitive
- state JSONB/text
- question
- options JSONB
- expected_answer JSONB/text
- metadata JSONB

`benchmark_runs`

- id
- name
- status
- benchmark_mode
- dataset_id
- manifest JSONB
- random_seed
- started_at
- finished_at

`benchmark_provider_runs`

- id
- benchmark_run_id
- provider_id
- provider_model
- configuration JSONB
- hardware_profile JSONB
- status

`predictions`

- id
- benchmark_provider_run_id
- dataset_sample_id
- selected_answer
- probabilities JSONB nullable
- confidence nullable
- correct nullable
- latency_ms_e2e
- provider_latency_ms nullable
- usage JSONB nullable
- estimated_cost_usd nullable
- retry_count
- raw_request JSONB
- raw_response JSONB nullable
- error_type nullable
- error_message nullable

`metric_snapshots`

- id
- benchmark_provider_run_id
- scope_type
- scope_key
- metrics JSONB
- calculated_at

`pricing_snapshots`

- id
- provider
- model
- effective_date
- pricing JSONB
- source_note

### 15.2 Indexes

At minimum index:

- benchmark_run_id
- provider_id
- dataset_sample_id
- primitive
- status
- correct
- created timestamp

---

## 16. API Surface

Prefix all endpoints with `/api/v1`.

### Provider endpoints

```text
GET  /providers
```

The provider list includes each provider's availability and capability snapshot. A
provider-specific health check is deferred until an administration/settings area is
needed.

### Dataset endpoints

```text
GET  /datasets
POST /datasets/upload
GET  /datasets/{id}/samples
```

Dataset upload validates the file before it is accepted and returns its validation
summary. Dataset metadata and validation status are included in the dataset list;
a separate validation endpoint is deferred until datasets can be edited in place.

### Playground

```text
POST /compare
```

Request selects one or more providers and one normalized decision case.

Response returns provider results side by side without persisting a full benchmark run unless requested.

### Benchmark endpoints

```text
POST /benchmarks
GET  /benchmarks
GET  /benchmarks/{id}
POST /benchmarks/{id}/cancel
GET  /benchmarks/{id}/events       # SSE
GET  /benchmarks/{id}/predictions
GET  /benchmarks/{id}/export?format=json|csv
```

The benchmark detail response includes summary metrics and run progress.
Disagreements are retrieved from the predictions endpoint using filters rather than
a separate endpoint.

Filtering for predictions must support:

- provider
- primitive
- task/domain
- correct/incorrect
- confidence range
- candidate count
- error status
- agreement/disagreement state

---

## 17. Benchmark Worker Behavior

The worker must:

1. Load the immutable run manifest.
2. Resolve the dataset revision.
3. Produce deterministic candidate ordering.
4. Execute provider calls with configured concurrency.
5. Respect provider-specific rate limits.
6. Record every request, response, failure, retry, latency, and cost input.
7. Incrementally persist results rather than holding an entire run in memory.
8. Publish progress events.
9. Calculate metrics after provider completion.
10. Mark partial runs explicitly when cancelled or interrupted.

A restart must not duplicate completed sample/provider pairs.

Use an idempotency key derived from:

```text
run_id + provider_run_id + dataset_sample_id + repeat_index + permutation_index
```

---

## 18. Frontend Product Design

### 18.1 Design direction

The UI should look like an **evaluation/observability product**, not an AI chat application.

Characteristics:

- desktop-first
- dense but readable data presentation
- neutral professional styling
- strong typography and spacing
- minimal decorative gradients
- cards only where they communicate a metric
- tables for raw evidence
- charts for distributions/tradeoffs
- every aggregate must be drillable to row-level predictions

Think closer to a model-evaluation dashboard than a chatbot.

### 18.2 Main navigation

```text
Overview
Playground
Benchmarks
Datasets
Compare Runs
Settings
```

### 18.3 Playground page

Purpose: instantly understand the product.

Inputs:

- state/context editor (text or JSON)
- primitive selector
- question/instructions
- options editor
- provider toggles

Output cards side by side:

```text
Jev          Cloudflare Clef-flash     OpenAI Decisions
selected answer    selected answer   selected answer
confidence          confidence/N/A    confidence/N/A
probabilities       probabilities     probabilities/N/A
latency             latency           latency
cost                cost              cost/N/A
raw response link   raw response      raw response
```

Do not declare a winner automatically.

### 18.4 New Benchmark page

Fields:

- dataset
- providers
- benchmark mode
- concurrency
- repetitions
- candidate-order permutations
- confidence thresholds
- optional row limit
- random seed

Before starting, display the estimated number of provider calls.

### 18.5 Running Benchmark page

Show:

- overall progress
- per-provider progress
- successful calls
- errors/retries
- current throughput
- elapsed runtime
- partial cost where available

Use SSE, not repeated aggressive polling.

### 18.6 Results Overview

Top summary must show each provider in parallel with:

- all-row accuracy
- completed-row accuracy
- macro F1 where applicable
- ECE or N/A
- NLL or N/A
- p50/p95 latency
- cost per 1K
- cost per correct decision
- coverage
- failure rate

Then show:

1. accuracy by primitive
2. accuracy vs candidate count
3. latency distribution
4. cost vs accuracy scatter
5. calibration/reliability diagram
6. risk-coverage curve
7. failure breakdown

### 18.7 Disagreement Explorer

Filters:

- all disagree
- exactly one provider differs
- provider A correct / provider B wrong
- confidently wrong
- low-confidence cases
- label-flip cases

Each row must display:

- state
- question/options
- expected answer
- each provider's answer
- each provider's probability/confidence
- correctness
- latency
- expandable raw request/response

### 18.8 Calibration page

Show:

- reliability curve
- ECE
- NLL
- Brier score
- confidence histogram
- accuracy by confidence bin
- risk-coverage curve
- threshold table

Threshold table example:

```text
Threshold | Coverage | Accuracy | Incorrect accepted
0.70      | ...      | ...      | ...
0.80      | ...      | ...      | ...
0.90      | ...      | ...      | ...
0.95      | ...      | ...      | ...
```

### 18.9 Robustness page

Sections:

- paraphrase consistency
- option-order sensitivity
- repeated-call stability
- candidate-cardinality degradation

Charts must make it possible to see whether a provider is accurate but unstable.

### 18.10 Dataset page

Show:

- revision/hash
- source/license
- row count
- primitive distribution
- class distribution
- candidate-count distribution
- domains/tasks
- validation errors

---

## 19. Cost Accounting

Cost must be stored as a reproducible estimate, not dynamically recalculated using today's pricing for old runs.

For every run:

- snapshot pricing before execution
- store pricing source note/date
- use provider-reported token/credit usage when available
- otherwise calculate from documented billing units
- return `N/A` when pricing is unknown

Metrics:

```text
cost_per_1k = total_cost / completed_decisions * 1000
cost_per_correct = total_cost / correct_decisions
```

Use the dated Cloudflare Workers AI pricing snapshot for Clef-flash. Do not infer costs when provider usage or pricing data is unavailable.

---

## 20. Security and Privacy

### 20.1 Secrets

Provider API keys must:

- exist only on the backend/worker
- load from environment variables or a server-side secret store
- never be returned through APIs
- never appear in logs
- never be shipped to the browser

Expected environment variables:

```text
DATABASE_URL
REDIS_URL
TYPESAFE_API_KEY
TYPESAFE_BASE_URL
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_API_TOKEN
OPENAI_API_KEY
OPENAI_DECISIONS_ENABLED
```

### 20.2 Data handling

- do not log complete benchmark states in ordinary application logs
- raw benchmark inputs/responses belong in the database/artifact store only
- cap upload size
- validate CSV/JSONL content types
- allow deletion of user-uploaded datasets and associated runs
- display a warning before sending uploaded private data to hosted providers

### 20.3 Error handling

Sanitize upstream errors before returning them to clients while preserving full technical diagnostics server-side without secrets.

---

## 21. Observability

Use structured JSON logs.

Every provider call should include correlation fields:

```text
request_id
run_id
provider_run_id
sample_id
provider
attempt
```

Add OpenTelemetry instrumentation for:

- API requests
- worker jobs
- provider calls
- database operations

OpenTelemetry must be optional and must not be required for local development.

Expose a lightweight health endpoint and optional Prometheus-compatible metrics endpoint.

Do not add LangSmith; this project is not an agent/LLM trace product.

---

## 22. Testing Strategy

### 22.1 Unit tests

Required for:

- provider normalization
- metric calculations
- candidate permutation logic
- pricing calculations
- dataset validation
- idempotency-key generation
- confidence threshold calculations

Use fixed known vectors to verify ECE, NLL, Brier, F1, and ordinal metrics.

### 22.2 Contract tests

Maintain recorded/mocked fixtures for each provider adapter.

Test:

- valid response
- missing optional probability fields
- rate limit
- timeout
- 5xx
- malformed upstream response
- provider capability changes

Live-provider tests must be opt-in through environment flags so CI does not incur external cost.

### 22.3 Integration tests

Test:

- benchmark creation -> queue -> worker -> persisted predictions -> metrics
- interrupted job resume/idempotency
- dataset upload and validation
- CSV/JSON exports

### 22.4 Frontend tests

Test:

- benchmark creation form
- running-progress state
- missing metric shown as `N/A`
- disagreement filtering
- row-level drilldown
- calibration chart data transformation

### 22.5 End-to-end

Playwright smoke flow:

```text
load seeded dataset
-> run mocked 3-provider benchmark
-> watch progress
-> view results
-> open disagreement
-> export JSON
```

### 22.6 Coverage target

Target at least 85% test coverage for backend domain logic and metric/provider normalization modules. Do not chase coverage in generated/configuration code.

---

## 23. Code Quality and CI

GitHub Actions pipeline:

```text
backend lint
backend type check
backend tests
frontend lint/type check
frontend unit tests
build frontend
Playwright smoke test
Docker build
```

A pull request cannot merge if any required stage fails.

Use Conventional Commits where practical.

---

## 24. Repository Structure

```text
decisionlens/
├── README.md
├── PROJECT_SPEC.md
├── ARCHITECTURE.md
├── BENCHMARK_METHODOLOGY.md
├── DATASETS.md
├── PROVIDERS.md
├── SECURITY.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── typesafe_jev.py
│   │   │   ├── cloudflare_clef_flash.py
│   │   │   └── openai_decisions.py
│   │   ├── datasets/
│   │   ├── benchmarks/
│   │   │   ├── runner.py
│   │   │   ├── manifest.py
│   │   │   ├── permutations.py
│   │   │   └── statistics.py
│   │   ├── metrics/
│   │   │   ├── classification.py
│   │   │   ├── calibration.py
│   │   │   ├── ordinal.py
│   │   │   ├── multilabel.py
│   │   │   ├── robustness.py
│   │   │   └── economics.py
│   │   ├── workers/
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── features/
│   ├── lib/
│   └── tests/
└── fixtures/
    ├── providers/
    └── datasets/
```

---

## 25. Local Development

A new developer should be able to start core services with:

```bash
cp .env.example .env
docker compose up --build
```

Required services:

- frontend
- API
- worker
- PostgreSQL
- Redis

Cloudflare credentials are optional for local development. When absent, Clef-flash must report as unavailable without preventing startup.

Jev/OpenAI unavailable credentials must not prevent application startup. Providers should simply report unavailable status.

Seed the application with a tiny fixture dataset and mocked provider mode so the entire UI is testable without paid API keys.

---

## 26. Implementation Phases

### Phase 1 — Foundation

- repository scaffolding
- Docker Compose
- PostgreSQL/Alembic
- provider interface
- run manifest model
- health endpoints
- mocked provider

### Phase 2 — Provider adapters

- Jev
- Cloudflare Clef-flash
- OpenAI Decisions adapter with configuration-based enablement
- capability detection
- raw + normalized result persistence

### Phase 3 — Benchmark engine

- durable jobs
- deterministic ordering
- retries/rate limits
- idempotency
- progress SSE
- cancellation

### Phase 4 — Datasets

- user CSV/JSONL
- Hanno DecisionBench adapter
- frozen stress-suite fixtures
- dataset validation and hashing

### Phase 5 — Metrics

- classification
- calibration
- ordinal
- multi-label
- latency/throughput
- economics
- confidence intervals

### Phase 6 — Frontend

- playground
- create benchmark
- run progress
- result dashboard
- disagreement explorer
- calibration
- robustness
- dataset viewer

### Phase 7 — Hardening

- full test suite
- E2E tests
- observability
- export formats
- documentation
- CI
- accessibility and responsive cleanup

---

## 27. Acceptance Criteria — v1

DecisionLens v1 is complete only when all of the following are true:

1. Jev and Cloudflare Clef-flash can both execute real benchmark requests through provider adapters.
2. OpenAI Decisions is implemented behind a configuration flag and does not block the rest of the application when disabled.
3. At least one external decision benchmark suite is ingestible by revision/hash.
4. CSV/JSONL user datasets can be validated and benchmarked.
5. Binary, categorical, ordinal, and multi-label workloads are supported.
6. A benchmark can run asynchronously and survive page refreshes.
7. Results persist row-level raw responses and normalized predictions.
8. Accuracy, F1, ECE, NLL, Brier, latency, failure, cost, and robustness metrics are implemented where applicable.
9. Metrics unavailable because a provider lacks probabilities are displayed as `N/A`.
10. Candidate-cardinality analysis works from 2 through at least 100 options when supported.
11. Disagreement Explorer can identify confidently wrong and provider-divergent cases.
12. Calibration and risk-coverage visualizations work from real stored predictions.
13. Every run has a reproducibility manifest.
14. JSON and CSV exports are available.
15. API secrets never reach the frontend or logs.
16. Core domain/provider/metric tests meet the agreed coverage target.
17. `docker compose up --build` launches a functional local system.
18. CI passes linting, typing, tests, frontend build, E2E smoke, and Docker build.
19. The README clearly states that DecisionLens is independent and is not affiliated with TypeSafe, InterfazeAI, Hanno Labs, or OpenAI.
20. No agent framework, RAG layer, MCP runtime, or unrelated AI feature is included in v1.

---

## 28. Required Documentation Produced by the Implementation

Codex should create and maintain:

### `README.md`

- project purpose
- screenshots when available
- quickstart
- supported providers
- limitations
- example benchmark

### `ARCHITECTURE.md`

- component diagram
- execution flow
- persistence strategy
- provider abstraction
- job lifecycle

### `BENCHMARK_METHODOLOGY.md`

- fairness rules
- metric definitions
- latency methodology
- cost methodology
- confidence intervals
- retry/failure treatment

### `PROVIDERS.md`

For every provider:

- supported capabilities
- configuration
- known limitations
- native API mapping
- version/revision behavior

### `DATASETS.md`

- source
- revision
- license
- normalization mapping
- known caveats

### `SECURITY.md`

- secrets handling
- vulnerability reporting
- data/privacy considerations

---

## 29. Coding Instructions for Codex

1. Treat this document as the source of truth for v1 scope.
2. Prefer simple, typed modules over abstractions that are not yet required.
3. Keep provider-specific logic inside provider adapters.
4. Do not assume all providers return probabilities or usage metadata.
5. Never create fake provider data in production code; mock data belongs only in dev/test fixtures.
6. Preserve raw upstream responses for auditability.
7. Prefer deterministic, reproducible benchmark behavior.
8. Do not add agent frameworks.
9. Do not add vector databases.
10. Do not add authentication/multi-tenancy unless explicitly requested later.
11. Build backend contracts first; the frontend should consume those contracts rather than duplicate benchmark logic.
12. Any deviation from benchmark fairness rules must be explicit in code and surfaced in the run manifest.
13. Do not silently change benchmark datasets or metric formulas after results have been recorded; version them.
14. Use `N/A` rather than invented estimates when a provider lacks a capability.
15. Keep the project extensible enough to add a fourth provider without schema rewrites.

---

## 30. Final Product Definition

DecisionLens v1 is successful if a developer can open the application, select a pinned decision benchmark or upload a labeled dataset, run Jev/Cloudflare Clef-flash/OpenAI Decisions under a reproducible configuration, and then answer from evidence:

- which systems were correct
- where they disagreed
- how trustworthy their probabilities were
- how stable they were
- how performance changed with decision shape/cardinality
- how long they took
- how much they cost
- where they failed

The product should provide the evidence needed to choose a decision system for a workload. It must not hide tradeoffs behind a single leaderboard score.
