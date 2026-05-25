import { useState } from "react";
import type { ProductCandidate } from "../types";
import { STORE_COLORS, STORE_LABELS } from "../types";

interface Props {
  candidates: Record<string, ProductCandidate[]>;
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 11 11"
      fill="none"
      aria-hidden="true"
      className={`text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    >
      <path d="M1.5 3.5l4 4 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CandidateProductsTable({ candidates }: Props) {
  const queries = Object.entries(candidates).filter(([, products]) => products.length > 0);
  if (queries.length === 0) return null;

  return (
    <div className="mt-3 space-y-1.5">
      <p className="text-[10px] font-semibold text-slate-300 uppercase tracking-[0.12em]">
        Candidatos evaluados
      </p>
      {queries.map(([query, products]) => (
        <CandidateGroup key={query} query={query} products={products} />
      ))}
    </div>
  );
}

function CandidateGroup({
  query,
  products,
}: {
  query: string;
  products: ProductCandidate[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl overflow-hidden border border-slate-100 bg-white">

      {/* Accordion header */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left px-3 py-2 bg-slate-50 hover:bg-slate-100 flex items-center justify-between gap-2"
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[12px] font-medium text-slate-600 capitalize truncate">
            {query}
          </span>
          <span className="text-[10px] font-semibold text-slate-400 bg-white border border-slate-200 px-1.5 py-0.5 rounded-full shrink-0">
            {products.length}
          </span>
        </div>
        <ChevronIcon open={open} />
      </button>

      {/* Accordion body */}
      {open && (
        <ul className="divide-y divide-slate-50 max-h-72 overflow-y-auto overscroll-contain">
          {products.map((p, i) => (
            <li
              key={i}
              className="flex items-center gap-2 px-3 py-2 text-xs bg-white hover:bg-slate-50"
            >
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-semibold ${STORE_COLORS[p.store]}`}>
                {STORE_LABELS[p.store]}
              </span>
              <span className="flex-1 truncate text-slate-600">{p.title}</span>
              <span className="text-slate-400 shrink-0 font-medium">
                S/ {p.unit_price.toFixed(2)}/{p.quantity_unit}
              </span>
              {p.product_url && (
                <a
                  href={p.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-300 hover:text-mint-500 shrink-0"
                  aria-label="Ver producto"
                >
                  ↗
                </a>
              )}
            </li>
          ))}
        </ul>
      )}

    </div>
  );
}
