"use client";

import { useState, useCallback, useEffect, useRef } from "react";

type Frame = { event: string; node?: string; payload?: unknown };

/**
 * Minimal chat surface that drives the `/api/chat` SSE proxy.
 *
 * We deliberately don't pull in `useChat` from `ai/react` — that hook expects
 * an OpenAI-shaped completion stream. Our backend emits structured graph
 * events (`node_complete`, `interrupt`, ...) so a tiny hand-rolled reader
 * keeps the contract honest.
 */
export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [frames, setFrames] = useState<Frame[]>([]);
  const [pendingInterrupt, setPendingInterrupt] = useState<Frame | null>(null);
  const [busy, setBusy] = useState(false);
  const threadIdRef = useRef<string>(crypto.randomUUID());

  const sendDecision = useCallback(async (decision: "approve" | "deny") => {
    const backend = process.env.NEXT_PUBLIC_AGENT_BACKEND_URL ?? "http://localhost:8000";
    await fetch(`${backend}/agent/resume`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ thread_id: threadIdRef.current, decision }),
    });
    setPendingInterrupt(null);
  }, []);

  const submit = useCallback(async () => {
    if (!question.trim()) return;
    setBusy(true);
    setFrames([]);
    setPendingInterrupt(null);

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, threadId: threadIdRef.current }),
    });
    if (!res.body) {
      setBusy(false);
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split("\n\n");
      buf = parts.pop() ?? "";
      for (const part of parts) {
        const dataLine = part.split("\n").find((l) => l.startsWith("data:"));
        if (!dataLine) continue;
        try {
          const frame = JSON.parse(dataLine.slice(5).trim()) as Frame;
          setFrames((f) => [...f, frame]);
          if (frame.event === "interrupt") setPendingInterrupt(frame);
        } catch {
          /* skip non-JSON keepalives */
        }
      }
    }
    setBusy(false);
  }, [question]);

  useEffect(() => {
    threadIdRef.current = crypto.randomUUID();
  }, []);

  return (
    <main style={{ maxWidth: 720, margin: "32px auto", fontFamily: "system-ui" }}>
      <h1>Agentic chat (Vercel AI SDK shell)</h1>
      <p style={{ color: "#666" }}>
        Streams from a FastAPI agent backend. Pause-on-interrupt + resume work end-to-end.
      </p>
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question…"
        rows={3}
        style={{ width: "100%", padding: 8 }}
      />
      <button onClick={submit} disabled={busy} style={{ marginTop: 8 }}>
        {busy ? "Streaming…" : "Send"}
      </button>

      {pendingInterrupt && (
        <section style={{ marginTop: 16, padding: 12, background: "#fff8e1" }}>
          <strong>Approval needed.</strong>
          <pre style={{ whiteSpace: "pre-wrap" }}>
            {JSON.stringify(pendingInterrupt.payload, null, 2)}
          </pre>
          <button onClick={() => sendDecision("approve")}>Approve</button>{" "}
          <button onClick={() => sendDecision("deny")}>Deny</button>
        </section>
      )}

      <section style={{ marginTop: 16 }}>
        {frames.map((f, i) => (
          <div key={i} style={{ padding: "6px 0", borderBottom: "1px solid #eee" }}>
            <code>{f.event}</code>
            {f.node ? <> · <em>{f.node}</em></> : null}
          </div>
        ))}
      </section>
    </main>
  );
}
