import { useState } from "react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
type Msg = { role: "user" | "assistant"; content: string };
type Step = { tool: string; args: Record<string, unknown>; result: string };

export default function App() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [trace, setTrace] = useState<Step[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!input.trim() || busy) return;
    const next: Msg[] = [...msgs, { role: "user", content: input }];
    setMsgs(next); setInput(""); setBusy(true);
    try {
      const r = await fetch(`${API}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ messages: next }) });
      if (!r.ok) throw new Error(String(r.status));
      const d = await r.json();
      setMsgs([...next, { role: "assistant", content: d.answer }]); setTrace(d.trace);
    } catch {
      setMsgs([...next, { role: "assistant", content: "Something went wrong. Please try again." }]);
    } finally { setBusy(false); }
  }

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: 16, fontFamily: "system-ui" }}>
      <h2>PlayAssist</h2>
      <p style={{ color: "#666" }}>Try: "What is Maya's win rate?" or "How do I get a refund?"</p>
      {msgs.map((m, i) => (
        <p key={i} style={{ background: m.role === "user" ? "#e8f0fe" : "#f3f3f3", padding: 10, borderRadius: 8 }}><b>{m.role === "user" ? "You" : "PlayAssist"}:</b> {m.content}</p>
      ))}
      {busy && <p>Thinking…</p>}
      {trace.length > 0 && (
        <details open><summary>Tool calls ({trace.length})</summary>
          {trace.map((s, i) => <pre key={i} style={{ background: "#fafafa", padding: 8, overflowX: "auto" }}>{s.tool}({JSON.stringify(s.args)}){"\n"}→ {s.result}</pre>)}
        </details>
      )}
      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <input style={{ flex: 1, padding: 8 }} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()} placeholder="Ask something…" />
        <button onClick={send} disabled={busy}>Send</button> <button onClick={() => { setMsgs([]); setTrace([]); }}>New chat</button>
      </div>
    </div>
  );
}
