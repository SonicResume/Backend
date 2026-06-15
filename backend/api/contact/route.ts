// app/api/contact/route.ts
import { NextRequest, NextResponse } from "next/server";

const ipHits = new Map<string, { count: number; ts: number }>();
const WINDOW_MS = 60_000; // 1 minute
const MAX_HITS = 10;      // max requests/min per IP

export async function POST(req: NextRequest) {
  const ip = req.headers.get("x-forwarded-for") || "local";
  const now = Date.now();
  const hit = ipHits.get(ip) || { count: 0, ts: now };
  if (now - hit.ts > WINDOW_MS) { hit.count = 0; hit.ts = now; }
  hit.count += 1; ipHits.set(ip, hit);
  if (hit.count > MAX_HITS) {
    return NextResponse.json({ ok: false, error: "Too many requests" }, { status: 429 });
  }

  const body = await req.json().catch(() => ({}));
  // simple honeypot: field must be empty on legit submissions
  if (typeof body.hp === "string" && body.hp.trim().length > 0) {
    return NextResponse.json({ ok: true }); // silently accept & drop
  }

  // TODO: handle your normal send (email/DB/etc.)
  return NextResponse.json({ ok: true, message: "Thanks — we’ll reply within 3 days." });
}

