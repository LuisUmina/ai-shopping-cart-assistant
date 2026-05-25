import type { CartRecommendation } from "../types";
import { ProductCard } from "./ProductCard";

interface Props {
  cart: CartRecommendation | null;
}

export function CartSummary({ cart }: Props) {
  const isEmpty = !cart || cart.cart.length === 0;
  const itemCount = cart?.cart.length ?? 0;

  return (
    <aside className="w-80 flex flex-col bg-white border-l border-[#E8EBED] shrink-0">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="px-5 py-3.5 border-b border-[#F0F2F3] flex items-center justify-between">
        <h2 className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.12em]">
          Carrito Recomendado
        </h2>
        {!isEmpty && (
          <span className="text-[11px] font-semibold text-mint-700 bg-mint-50 border border-mint-200 px-2 py-0.5 rounded-full">
            {itemCount} {itemCount === 1 ? "ítem" : "ítems"}
          </span>
        )}
      </div>

      {/* ── Body ────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">

        {isEmpty ? (
          /* ── Empty state ────────────────────────────────────────────── */
          <div className="flex flex-col items-center justify-center h-full text-center px-6 py-16">
            <div className="w-12 h-12 rounded-2xl bg-[#F7F8F8] flex items-center justify-center mb-4">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
                <path d="M2 2.5h2l2.5 8.5h9l2.2-6.5H6" stroke="#A9B3B8" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="8.5" cy="17.5" r="1.5" fill="#A9B3B8"/>
                <circle cx="14.5" cy="17.5" r="1.5" fill="#A9B3B8"/>
              </svg>
            </div>
            <p className="text-sm font-medium text-slate-400 mb-1.5">Tu carrito aparece aquí</p>
            <p className="text-xs text-slate-300 leading-relaxed">
              Describe tu pedido y el asistente construirá tu lista optimizada.
            </p>
          </div>
        ) : (
          cart!.cart.map((item, i) => <ProductCard key={i} item={item} />)
        )}

      </div>

      {/* ── Footer — total + warnings ────────────────────────────────────── */}
      {!isEmpty && (
        <div className="border-t border-[#F0F2F3] bg-white px-5 py-4 space-y-3">

          {/* Total */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-500">Total estimado</span>
            <div className="text-right">
              <span className="text-lg font-bold text-[#1B1D1F] tracking-tight">
                S/ {cart!.total_estimated_cost.toFixed(2)}
              </span>
            </div>
          </div>

          {/* Warnings */}
          {cart!.warnings.length > 0 && (
            <ul className="space-y-1.5">
              {cart!.warnings.map((w, i) => (
                <li key={i} className="text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2 leading-snug">
                  ⚠ {w}
                </li>
              ))}
            </ul>
          )}

          {/* Questions */}
          {cart!.questions.length > 0 && (
            <ul className="space-y-1.5">
              {cart!.questions.map((q, i) => (
                <li key={i} className="text-xs text-sky-700 bg-sky-50 border border-sky-100 rounded-xl px-3 py-2 leading-snug">
                  ? {q}
                </li>
              ))}
            </ul>
          )}

        </div>
      )}

    </aside>
  );
}
