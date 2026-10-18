"""In-memory dataset upload and benchmark execution for the local MVP."""

import asyncio
import json
import math
import uuid
from pathlib import Path
from time import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.providers.registry import get_providers
from app.schemas.decisions import DecisionQuestion, NormalizedDecisionRequest

router = APIRouter()
datasets_router = APIRouter()
fixture_path = Path(__file__).parents[5] / "fixtures/datasets/decisionlens-starter-v1.jsonl"
datasets: dict[str, list[dict[str, Any]]] = {
    "starter-v1": [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
}
runs: dict[str, dict[str, Any]] = {}


class StartBenchmark(BaseModel):
    dataset_id: str = "starter-v1"
    providers: list[str] = Field(min_length=1)


def metadata(dataset_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"id": dataset_id, "name": "DecisionLens starter suite v1" if dataset_id == "starter-v1" else dataset_id, "samples": len(rows), "primitives": sorted({row["primitive"] for row in rows})}


@datasets_router.get("")
async def list_datasets() -> list[dict[str, Any]]:
    return [metadata(dataset_id, rows) for dataset_id, rows in datasets.items()]


@datasets_router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)) -> dict[str, Any]:  # noqa: B008
    if not file.filename or not file.filename.endswith(".jsonl"):
        raise HTTPException(422, "Upload a .jsonl file with labeled DecisionLens cases")
    try:
        rows = [json.loads(line) for line in (await file.read()).decode("utf-8").splitlines() if line.strip()]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(422, "Dataset must be valid UTF-8 JSONL") from exc
    required = {"id", "state", "question", "primitive", "options", "expected_answer"}
    if not rows or any(not required <= row.keys() or row["expected_answer"] not in row["options"] for row in rows):
        raise HTTPException(422, "Every row needs id, state, question, primitive, options, and expected_answer")
    dataset_id = f"upload-{uuid.uuid4().hex[:8]}"
    datasets[dataset_id] = rows
    return metadata(dataset_id, rows)


@router.post("/run")
async def start_benchmark(request: StartBenchmark, tasks: BackgroundTasks) -> dict[str, Any]:
    rows = datasets.get(request.dataset_id)
    if rows is None:
        raise HTTPException(404, "Dataset not found")
    providers = get_providers()
    unknown = sorted(set(request.providers) - providers.keys())
    if unknown:
        raise HTTPException(422, f"Unknown provider(s): {', '.join(unknown)}")
    run_id = uuid.uuid4().hex
    runs[run_id] = {"id": run_id, "status": "queued", "dataset": metadata(request.dataset_id, rows), "providers": request.providers, "completed": 0, "total": len(rows) * len(request.providers), "results": [], "started_at": time()}
    tasks.add_task(execute, run_id, rows, request.providers)
    return runs[run_id]


@router.get("/{run_id}")
async def get_benchmark(run_id: str) -> dict[str, Any]:
    if run_id not in runs:
        raise HTTPException(404, "Benchmark run not found")
    return runs[run_id]


async def execute(run_id: str, rows: list[dict[str, Any]], provider_slugs: list[str]) -> None:
    run = runs[run_id]
    run["status"] = "running"
    providers = get_providers()
    for row in rows:
        question = DecisionQuestion(id=row["id"], primitive=row["primitive"], instructions=row["question"], options=row["options"])
        request = NormalizedDecisionRequest(state=row["state"], questions=[question])
        results = await asyncio.gather(*(providers[slug].decide(request) for slug in provider_slugs))
        for result in results:
            answer = result.answers[0] if result.answers else None
            probabilities = answer.probabilities if answer else None
            selected = answer.selected_option if answer else None
            if not selected and probabilities:
                selected = max(probabilities, key=probabilities.get)
            if not selected and row["primitive"] == "ordinal" and answer and answer.ordinal_expected_value is not None:
                index = min(max(round(answer.ordinal_expected_value), 0), len(row["options"]) - 1)
                selected = row["options"][index]
            run["results"].append(
                {
                    "provider": result.provider,
                    "expected": row["expected_answer"],
                    "selected": selected,
                    "probabilities": probabilities,
                    "latency_ms": result.latency_ms_e2e,
                    "error": result.error,
                    "tags": row.get("tags", []),
                    "domain": row.get("domain", "unspecified"),
                    "primitive": row["primitive"],
                    "candidate_count": len(row["options"]),
                }
            )
            run["results"][-1].update({"case_id": row["id"], "options": row["options"], "metadata": row.get("metadata", {}), "usage": result.usage})
            run["completed"] += 1
            run["metrics"] = metrics(run["results"], provider_slugs)
            add_run_rate(run)
    run["status"] = "completed"
    run["metrics"] = metrics(run["results"], provider_slugs)
    add_run_rate(run)


def add_run_rate(run: dict[str, Any]) -> None:
    """Record observed end-to-end throughput for this normal benchmark mode."""
    elapsed_seconds = max(time() - run["started_at"], 0.001)
    run["metrics"]["comparison"]["observed_throughput_per_second"] = run["completed"] / elapsed_seconds


def percentile(values: list[float], fraction: float) -> float | None:
    """Return nearest-rank percentile, suitable for small local benchmark samples."""
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def metrics(results: list[dict[str, Any]], providers: list[str]) -> dict[str, Any]:
    output: dict[str, dict[str, float | None]] = {}
    reliability: dict[str, list[dict[str, float | int]]] = {}
    slices: dict[str, dict[str, dict[str, dict[str, float | int | None]]]] = {}
    for provider in providers:
        rows = [row for row in results if row["provider"] == provider]
        scored = [row for row in rows if row["selected"] is not None]
        correct = [row for row in scored if row["selected"] == row["expected"]]
        probability_rows = [row for row in scored if valid_probabilities(row)]
        brier = [
            sum((row["probabilities"].get(option, 0.0) - float(option == row["expected"])) ** 2 for option in row["options"])
            / len(row["options"])
            for row in probability_rows
        ]
        invalid = [row for row in rows if not row["error"] and not valid_answer(row)]
        usage = [row.get("usage") or {} for row in rows]
        input_tokens = sum(item.get("input_tokens", 0) for item in usage)
        output_tokens = sum(item.get("output_tokens", 0) for item in usage)
        # USD per million tokens. Jev bills input only; output is currently free.
        rates = {
            "jev": (0.042, 0.0),
            "clef-flash": (0.038, 0.0),
            "openai-decisions": (0.10, 0.0),
        }
        price = rates.get(provider)
        estimated_cost = None if price is None or not rows else ((input_tokens * price[0] + output_tokens * price[1]) / 1_000_000) / len(rows) * 1000
        output[provider] = {
            "accuracy": len(correct) / len(rows) if rows else None,
            "macro_f1": macro_f1(rows),
            "brier": sum(brier) / len(brier) if brier else None,
            "expected_calibration_error": expected_calibration_error(probability_rows),
            "latency_ms": sum(row["latency_ms"] for row in rows) / len(rows) if rows else None,
            "p50_latency_ms": percentile([row["latency_ms"] for row in rows], 0.50),
            "p95_latency_ms": percentile([row["latency_ms"] for row in rows], 0.95),
            "failure_rate": sum(bool(row["error"]) for row in rows) / len(rows) if rows else None,
            "invalid_answer_rate": len(invalid) / len(rows) if rows else None,
            "cost_per_1000_usd": estimated_cost,
        }
        reliability[provider] = reliability_bins(probability_rows)
        slices[provider] = {
            "domain": slice_metrics(rows, "domain"),
            "primitive": slice_metrics(rows, "primitive"),
            "candidate_count": slice_metrics(rows, "candidate_count"),
        }
    complete_cases = {row["case_id"] for row in results if not row["error"] and row["selected"] is not None}
    comparable = [case_id for case_id in complete_cases if len({row["provider"] for row in results if row["case_id"] == case_id and row["selected"] is not None}) == len(providers)]
    disagreements = sum(len({row["selected"] for row in results if row["case_id"] == case_id}) > 1 for case_id in comparable)
    robustness: dict[str, float | None] = {}
    for provider in providers:
        pairs: dict[str, list[str]] = {}
        for row in results:
            pair_id = row.get("metadata", {}).get("pair_id")
            if row["provider"] == provider and pair_id and row["selected"]:
                pairs.setdefault(pair_id, []).append(row["selected"])
        valid_pairs = [answers for answers in pairs.values() if len(answers) == 2]
        robustness[provider] = sum(len(set(answers)) == 1 for answers in valid_pairs) / len(valid_pairs) if valid_pairs else None
    return {
        "providers": output,
        "comparison": {"disagreement_rate": disagreements / len(comparable) if comparable else None, "robustness": robustness},
        "reliability": reliability,
        "slices": slices,
    }


def valid_probabilities(row: dict[str, Any]) -> bool:
    probabilities = row.get("probabilities")
    return bool(
        probabilities
        and set(probabilities) == set(row["options"])
        and all(0 <= probability <= 1 for probability in probabilities.values())
        and math.isclose(sum(probabilities.values()), 1.0, abs_tol=0.01)
    )


def valid_answer(row: dict[str, Any]) -> bool:
    return row.get("selected") in row["options"] and (not row.get("probabilities") or valid_probabilities(row))


def macro_f1(rows: list[dict[str, Any]]) -> float | None:
    labels = sorted({row["expected"] for row in rows})
    if not labels:
        return None
    scores = []
    for label in labels:
        true_positive = sum(row["selected"] == label and row["expected"] == label for row in rows)
        false_positive = sum(row["selected"] == label and row["expected"] != label for row in rows)
        false_negative = sum(row["selected"] != label and row["expected"] == label for row in rows)
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append((2 * true_positive) / denominator if denominator else 0.0)
    return sum(scores) / len(scores)


def expected_calibration_error(rows: list[dict[str, Any]], bins: int = 10) -> float | None:
    if not rows:
        return None
    error = 0.0
    for bucket in reliability_bins(rows, bins):
        if bucket["count"]:
            error += abs(float(bucket["accuracy"]) - float(bucket["confidence"])) * int(bucket["count"]) / len(rows)
    return error


def reliability_bins(rows: list[dict[str, Any]], bins: int = 10) -> list[dict[str, float | int]]:
    buckets: list[list[dict[str, Any]]] = [[] for _ in range(bins)]
    for row in rows:
        confidence = max(row["probabilities"].values())
        buckets[min(int(confidence * bins), bins - 1)].append(row)
    return [
        {
            "lower": index / bins,
            "upper": (index + 1) / bins,
            "count": len(bucket),
            "confidence": sum(max(row["probabilities"].values()) for row in bucket) / len(bucket) if bucket else 0.0,
            "accuracy": sum(row["selected"] == row["expected"] for row in bucket) / len(bucket) if bucket else 0.0,
        }
        for index, bucket in enumerate(buckets)
    ]


def slice_metrics(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, float | int | None]]:
    groups = sorted({str(row.get(field, "unspecified")) for row in rows})
    return {
        group: {
            "cases": len(group_rows := [row for row in rows if str(row.get(field, "unspecified")) == group]),
            "accuracy": sum(row["selected"] == row["expected"] for row in group_rows) / len(group_rows) if group_rows else None,
        }
        for group in groups
    }
