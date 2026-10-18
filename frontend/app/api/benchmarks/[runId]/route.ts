import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export async function GET(_: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const response = await fetch(`${backendUrl}/api/v1/benchmarks/${runId}`, { cache: "no-store" });
  return NextResponse.json(await response.json(), { status: response.status });
}
