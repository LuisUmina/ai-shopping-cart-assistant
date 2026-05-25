import { useState } from "react";
import type { CandidateDebug, PipelineDebug, QueryDebug, StoreId } from "../types";
import { STORE_COLORS, STORE_LABELS } from "../types";

interface Props {
  debug: PipelineDebug;
  onClose: () => void;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function scoreColor(v: number) {
  if (v >= 0.75) return "bg-mint-500";
  if (v >= 0.50) return "bg-amber-400";
  return "bg-red-400";
}

function scoreText(v: number) {
  if (v >= 0.75) return "text-mint-600";
  if (v >= 0.50) return "text-amber-500";
  return "text-red-400";
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-slate-400 w-20 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${scoreColor(value)}`}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-[10px] font-mono text-slate-500 w-8 text-right">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

function CandidateRow({ candidate, rank }: { candidate: CandidateDebug; rank: number }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <tr
        className="border-b border-slate-50 hover:bg-slate-50/60 cursor-pointer select-none"
        onClick={() => setOpen((v) => !v)}
      >
        <td className="px-3 py-2.5 text-[11px] text-slate-400 font-mono">
          #{rank}
        </td>
        <td className="px-3 py-2.5 max-w-[180px]">
          <p className="text-[12px] font-medium text-slate-700 truncate">{candidate.title}</p>
          {candidate.brand && (
            <p className="text-[10px] text-slate-400 truncate">{candidate.brand}</p>
          )}
        </td>
        <td className="px-3 py-2.5 whitespace-nowrap">
          <span
            className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
              STORE_COLORS[candidate.store as StoreId] ?? "bg-slate-100 text-slate-500"
            }`}
          >
            {STORE_LABELS[candidate.store as StoreId] ?? candidate.store}
          </span>
        </td>
        <td className="px-3 py-2.5 text-[11px] font-mono text-slate-600 text-right whitespace-nowrap">
          S/.{candidate.unit_price.toFixed(2)}
        </td>
        <td className="px-3 py-2.5 text-right whitespace-nowrap">
          <span className={`text-[12px] font-semibold font-mono ${scoreText(candidate.rank_final)}`}>
            {Math.round(candidate.rank_final * 100)}
          </span>
          <span className="text-[9px] text-slate-300 ml-0.5">pts</span>
        </td>
        <td className="px-3 py-2.5 text-slate-300 text-[9px] w-5">
          {open ? "▲" : "▼"}
        </td>
      </tr>

      {open && (
        <tr className="bg-slate-50/50">
          <td colSpan={6} className="px-4 py-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-[0.14em] mb-2.5">
                  Filtro de relevancia
                </p>
                <div className="space-y-2">
                  <ScoreBar label="Título" value={candidate.filter_title} />
                  <ScoreBar label="Marca" value={candidate.filter_brand} />
                  <ScoreBar label="Categoría" value={candidate.filter_category} />
                  <ScoreBar label="Unidad" value={candidate.filter_unit} />
                  <div className="border-t border-slate-100 pt-2 mt-2">
                    <ScoreBar label="Score total" value={candidate.filter_score} />
                  </div>
                </div>
              </div>
              <div>
                <p className="text-[9px] font-semibold text-slate-400 uppercase tracking-[0.14em] mb-2.5">
                  Ranking final
                </p>
                <div className="space-y-2">
                  <ScoreBar label="Relevancia" value={candidate.rank_relevance} />
                  <ScoreBar label="Precio" value={candidate.rank_price} />
                  <ScoreBar label="Unidad" value={candidate.rank_unit} />
                  <ScoreBar label="Marca" value={candidate.rank_brand} />
                  <ScoreBar label="Tienda" value={candidate.rank_store} />
                  <div className="border-t border-slate-100 pt-2 mt-2">
                    <ScoreBar label="Score final" value={candidate.rank_final} />
                  </div>
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function QuerySection({ qd }: { qd: QueryDebug }) {
  return (
    <div className="mb-8">
      {/* Query header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-[13px] font-semibold text-slate-800">
            &ldquo;{qd.query}&rdquo;
          </h3>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-[11px] text-slate-400">
              {qd.scraped_total} scrapeados
            </span>
            <span className="text-slate-200">·</span>
            <span className="text-[11px] text-mint-600 font-medium">
              {qd.passed_filter} en análisis
            </span>
          </div>
        </div>
      </div>

      {/* Per-store counts */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {Object.entries(qd.scraped_per_store).map(([store, count]) => (
          <span
            key={store}
            className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
              STORE_COLORS[store as StoreId] ?? "bg-slate-100 text-slate-500"
            }`}
          >
            {STORE_LABELS[store as StoreId] ?? store}: {count}
          </span>
        ))}
      </div>

      {/* Candidates table */}
      {qd.candidates.length > 0 ? (
        <div className="border border-[#EDF0F2] rounded-2xl overflow-hidden">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-[#EDF0F2]">
                {["#", "Producto", "Tienda", "S/. u.", "Score", ""].map((h, i) => (
                  <th
                    key={i}
                    className={`px-3 py-2 text-[9px] font-semibold text-slate-400 uppercase tracking-wider ${
                      i >= 3 ? "text-right" : "text-left"
                    }`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {qd.candidates.map((c, i) => (
                <CandidateRow key={i} candidate={c} rank={i + 1} />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-[12px] text-slate-400 py-2">
          Sin candidatos en análisis.
        </p>
      )}
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export function DebugPanel({ debug, onClose }: Props) {
  const totalCandidates = debug.queries.reduce((s, q) => s + q.candidates.length, 0);
  const totalScraped = debug.queries.reduce((s, q) => s + q.scraped_total, 0);

  return (
    <div className="flex flex-col h-full overflow-hidden font-sans antialiased">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#EDF0F2] bg-white shrink-0">
        <div>
          <h2 className="text-[14px] font-semibold text-slate-800 tracking-tight">
            Análisis del pipeline
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {totalScraped} scrapeados &middot; {totalCandidates} en análisis &middot; {debug.queries.length} producto(s)
          </p>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          aria-label="Cerrar panel"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Legend */}
      <div className="px-5 py-2 bg-[#FAFAFA] border-b border-[#EDF0F2] flex items-center gap-5 shrink-0">
        <span className="text-[10px] text-slate-400 font-medium">Score:</span>
        {[
          { color: "bg-mint-500", label: "≥ 75" },
          { color: "bg-amber-400", label: "50–74" },
          { color: "bg-red-400",   label: "< 50" },
        ].map(({ color, label }) => (
          <span key={label} className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <span className={`w-2 h-2 rounded-full inline-block ${color}`} />
            {label}
          </span>
        ))}
        <span className="ml-auto text-[10px] text-slate-300">
          Clic en fila para ver detalle
        </span>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-5 py-5">
        {debug.queries.map((qd) => (
          <QuerySection key={qd.query} qd={qd} />
        ))}
      </div>

    </div>
  );
}
