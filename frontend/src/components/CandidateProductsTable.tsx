import { useState } from "react";
import type { ProductCandidate } from "../types";
import { STORE_COLORS, STORE_LABELS } from "../types";

interface Props {
  candidates: Record<string, ProductCandidate[]>;
}

export function CandidateProductsTable({ candidates }: Props) {
  const queries = Object.entries(candidates).filter(([, products]) => products.length > 0);
  if (queries.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-medium text-slate-400 uppercase tracking-wide">
        Candidatos encontrados
      </p>
      {queries.map(([query, products]) => (
        <CandidateGroup key={query} query={query} products={products} />
      ))}
    </div>
  );
}

function CandidateGroup({ query, products }: { query: string; products: ProductCandidate[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-slate-100 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left px-3 py-2 bg-slate-50 hover:bg-slate-100 transition-colors flex justify-between items-center"
      >
        <span className="text-xs font-medium text-slate-600 capitalize">
          {query}
          <span className="ml-1 font-normal text-slate-400">— {products.length} candidato(s)</span>
        </span>
        <span className="text-xs text-slate-400">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <ul className="divide-y divide-slate-100">
          {products.map((p, i) => (
            <li key={i} className="flex items-center gap-2 px-3 py-2 text-xs">
              <span className={`shrink-0 px-1.5 py-0.5 rounded-full font-medium ${STORE_COLORS[p.store]}`}>
                {STORE_LABELS[p.store]}
              </span>
              <span className="flex-1 truncate text-slate-700">{p.title}</span>
              <span className="text-slate-400 shrink-0">
                S/ {p.unit_price.toFixed(2)}/{p.quantity_unit}
              </span>
              <a
                href={p.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-500 hover:text-indigo-700 shrink-0"
              >
                ↗
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
