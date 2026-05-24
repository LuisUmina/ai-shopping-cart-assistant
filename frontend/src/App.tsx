import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "./api/client";

type Status =
  | { kind: "loading" }
  | { kind: "ok"; data: HealthResponse }
  | { kind: "error"; message: string };

function App() {
  const [status, setStatus] = useState<Status>({ kind: "loading" });

  useEffect(() => {
    getHealth()
      .then((data) => setStatus({ kind: "ok", data }))
      .catch((err) => setStatus({ kind: "error", message: String(err) }));
  }, []);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-800 flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-sm border border-slate-200 p-8">
        <h1 className="text-2xl font-semibold mb-1">AI Shopping Cart Assistant</h1>
        <p className="text-sm text-slate-500 mb-6">MVP — Phase 0 setup</p>

        <div className="rounded-lg border border-slate-200 p-4">
          <h2 className="text-sm font-medium text-slate-500 mb-2">Backend status</h2>
          {status.kind === "loading" && (
            <p className="text-slate-400">Checking…</p>
          )}
          {status.kind === "error" && (
            <p className="text-red-600">Backend unreachable: {status.message}</p>
          )}
          {status.kind === "ok" && (
            <ul className="space-y-1 text-sm">
              <li className="flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                <span className="font-medium">{status.data.status}</span>
              </li>
              <li className="text-slate-500">App: {status.data.app}</li>
              <li className="text-slate-500">Env: {status.data.environment}</li>
              <li className="text-slate-500">LLM provider: {status.data.llm_provider}</li>
            </ul>
          )}
        </div>
      </div>
    </main>
  );
}

export default App;
