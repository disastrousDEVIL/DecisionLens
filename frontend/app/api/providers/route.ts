import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const response = await fetch(`${backendUrl}/api/v1/providers`, { cache: "no-store" });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "DecisionLens API is unavailable" }, { status: 503 });
  }
}
