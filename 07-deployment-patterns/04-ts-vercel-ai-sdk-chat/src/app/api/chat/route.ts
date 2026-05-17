import { NextRequest } from "next/server";

export const runtime = "edge";

/**
 * Streams Server-Sent Events from the Python FastAPI agent backend
 * (leaf 00) straight through to the client. The backend already speaks
 * SSE — we just proxy it so the browser sees a same-origin stream
 * (avoids CORS + cookie pain on Vercel).
 */
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { question, threadId } = body as { question: string; threadId: string };

  const backend = process.env.AGENT_BACKEND_URL ?? "http://localhost:8000";
  const url = `${backend}/agent/stream?question=${encodeURIComponent(question)}&thread_id=${encodeURIComponent(threadId)}`;

  const upstream = await fetch(url, {
    method: "GET",
    headers: { Accept: "text/event-stream" },
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(
      JSON.stringify({ error: `upstream ${upstream.status}` }),
      { status: 502, headers: { "content-type": "application/json" } }
    );
  }

  return new Response(upstream.body, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache, no-transform",
      connection: "keep-alive",
    },
  });
}
