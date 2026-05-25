import { useState } from "react";
import type { CartItem } from "../types";
import { STORE_COLORS, STORE_LABELS } from "../types";

interface Props {
  item: CartItem;
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden="true"
      className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    >
      <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ExternalLinkIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none" aria-hidden="true">
      <path d="M4.5 2H2a.5.5 0 0 0-.5.5v7c0 .28.22.5.5.5h7a.5.5 0 0 0 .5-.5V6.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <path d="M6.5 1.5H10v3.5M10 1.5L5.5 6" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function ProductCard({ item }: Props) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  const storeColor = STORE_COLORS[item.store] ?? "bg-slate-100 text-slate-600";
  const storeLabel = STORE_LABELS[item.store] ?? item.store;

  return (
    <div className="rounded-2xl border border-[#EEF1F2] bg-white p-4 shadow-[0_2px_16px_rgba(0,0,0,0.05)] space-y-3">

      {/* ── Store badge + external link ──────────────────────────────── */}
      <div className="flex items-center justify-between gap-2">
        <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${storeColor}`}>
          {storeLabel}
        </span>
        {item.product_url && (
          <a
            href={item.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-slate-400 hover:text-mint-600 flex items-center gap-1 shrink-0"
          >
            Ver <ExternalLinkIcon />
          </a>
        )}
      </div>

      {/* ── Product title ────────────────────────────────────────────── */}
      <p className="text-[13px] font-medium text-[#1B1D1F] leading-snug">
        {item.selected_product}
      </p>

      {/* ── Price row ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span className="font-medium text-slate-700">
          S/ {item.unit_price.toFixed(2)}/{item.product_quantity_unit}
        </span>
        <span className="text-slate-200">·</span>
        <span>{item.required_units} un.</span>
        <span className="text-slate-200">·</span>
        <span className="font-bold text-[#1B1D1F]">
          S/ {item.estimated_total.toFixed(2)}
        </span>
      </div>

      {/* ── AI reason ────────────────────────────────────────────────── */}
      {item.reason && (
        <p className="text-[11px] text-slate-400 italic border-l-2 border-mint-300 pl-3 leading-relaxed">
          {item.reason}
        </p>
      )}

      {/* ── Alternatives ─────────────────────────────────────────────── */}
      {item.alternatives.length > 0 && (
        <div>
          <button
            onClick={() => setShowAlternatives((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-mint-600"
          >
            <ChevronIcon open={showAlternatives} />
            {showAlternatives
              ? "Ocultar alternativas"
              : `${item.alternatives.length} alternativa${item.alternatives.length > 1 ? "s" : ""}`}
          </button>

          {showAlternatives && (
            <ul className="mt-2 space-y-1 max-h-56 overflow-y-auto overscroll-contain pr-1">
              {item.alternatives.map((alt, i) => (
                <li
                  key={i}
                  className="flex items-center justify-between gap-2 text-[11px] text-slate-500 bg-[#F7F8F8] rounded-xl px-3 py-1.5"
                >
                  <span className="truncate">{alt.title}</span>
                  {alt.product_url && (
                    <a
                      href={alt.product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-300 hover:text-mint-500 shrink-0"
                    >
                      <ExternalLinkIcon />
                    </a>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

    </div>
  );
}
