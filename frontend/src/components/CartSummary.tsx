import type { CartRecommendation } from "../types";
import { ProductCard } from "./ProductCard";

interface Props {
  cart: CartRecommendation | null;
}

export function CartSummary({ cart }: Props) {
  const isEmpty = !cart || cart.cart.length === 0;

  return (
    <aside className="w-80 flex flex-col border-l border-slate-200 bg-slate-50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 bg-white">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
          Carrito Recomendado
        </h2>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="text-4xl mb-3">🛒</div>
            <p className="text-sm text-slate-400">
              Tu carrito aparecerá aquí una vez que el asistente procese tu pedido.
            </p>
          </div>
        ) : (
          cart!.cart.map((item, i) => <ProductCard key={i} item={item} />)
        )}
      </div>

      {/* Footer — total + warnings */}
      {!isEmpty && (
        <div className="border-t border-slate-200 bg-white p-4 space-y-3">
          {/* Total */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-600">Total estimado</span>
            <span className="text-base font-bold text-slate-900">
              S/ {cart!.total_estimated_cost.toFixed(2)}
            </span>
          </div>

          {/* Warnings */}
          {cart!.warnings.length > 0 && (
            <ul className="space-y-1">
              {cart!.warnings.map((w, i) => (
                <li key={i} className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
                  ⚠ {w}
                </li>
              ))}
            </ul>
          )}

          {/* Questions */}
          {cart!.questions.length > 0 && (
            <ul className="space-y-1">
              {cart!.questions.map((q, i) => (
                <li key={i} className="text-xs text-indigo-700 bg-indigo-50 border border-indigo-200 rounded p-2">
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
