import { useState } from "react";
import type { CartItem } from "../types";
import { STORE_COLORS, STORE_LABELS } from "../types";

interface Props {
  item: CartItem;
}

export function ProductCard({ item }: Props) {
  const [showAlternatives, setShowAlternatives] = useState(false);

  const storeColor = STORE_COLORS[item.store] ?? "bg-slate-100 text-slate-700";
  const storeLabel = STORE_LABELS[item.store] ?? item.store;

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3">
      {/* Store badge + link */}
      <div className="flex items-start justify-between gap-2">
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${storeColor}`}>
          {storeLabel}
        </span>
        <a
          href={item.product_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1 shrink-0"
        >
          Ver producto ↗
        </a>
      </div>

      {/* Title */}
      <p className="text-sm font-medium text-slate-800 leading-snug">
        {item.selected_product}
      </p>

      {/* Price row */}
      <div className="flex items-center gap-3 text-sm text-slate-600">
        <span>
          S/ {item.unit_price.toFixed(2)}/{item.product_quantity_unit}
        </span>
        <span className="text-slate-300">·</span>
        <span>{item.required_units} un.</span>
        <span className="text-slate-300">·</span>
        <span className="font-semibold text-slate-800">
          S/ {item.estimated_total.toFixed(2)}
        </span>
      </div>

      {/* Reason */}
      {item.reason && (
        <p className="text-xs text-slate-500 italic border-l-2 border-slate-200 pl-2">
          {item.reason}
        </p>
      )}

      {/* Alternatives toggle */}
      {item.alternatives.length > 0 && (
        <div>
          <button
            onClick={() => setShowAlternatives((v) => !v)}
            className="text-xs text-indigo-600 hover:text-indigo-800"
          >
            {showAlternatives ? "Ocultar" : `Ver ${item.alternatives.length} alternativa(s)`}
          </button>
          {showAlternatives && (
            <ul className="mt-2 space-y-1">
              {item.alternatives.map((alt, i) => (
                <li key={i} className="flex items-center justify-between text-xs text-slate-600 bg-slate-50 rounded px-2 py-1">
                  <span className="truncate">{alt.title}</span>
                  <a
                    href={alt.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-500 hover:text-indigo-700 ml-2 shrink-0"
                  >
                    ↗
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
