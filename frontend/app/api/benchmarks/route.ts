import { NextRequest, NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const response = await fetch(`${backendUrl}/api/v1/benchmarks/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: await request.text() });
  return NextResponse.json(await response.json(), { status: response.status });
}
