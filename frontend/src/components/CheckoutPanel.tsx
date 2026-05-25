import type { CartItem, CartRecommendation, StoreId } from "../types";
import { STORE_COLORS, STORE_LABELS } from "../types";

interface Props {
  cart: CartRecommendation;
  onClose: () => void;
}

// ── Icons ─────────────────────────────────────────────────────────────────────

function LockIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2.5" y="7" width="11" height="8" rx="2" />
      <path d="M5 7V5.5a3 3 0 016 0V7" />
    </svg>
  );
}

function SparkleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2l2 5.5 5.5 2-5.5 2L12 18l-2-5.5L4.5 9.5 10 7.5z" />
    </svg>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────

function LockedInput({ placeholder, type = "text" }: { placeholder: string; type?: string }) {
  return (
    <div className="relative">
      <input
        type={type}
        disabled
        placeholder={placeholder}
        className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-slate-400 placeholder:text-slate-300 cursor-not-allowed pr-10 focus:outline-none"
      />
      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-300 pointer-events-none">
        <LockIcon />
      </span>
    </div>
  );
}

function StoreCredentials({ store }: { store: StoreId }) {
  const label = STORE_LABELS[store];
  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-2">
        <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${STORE_COLORS[store]}`}>
          {label}
        </span>
      </div>
      <LockedInput placeholder={`Correo o usuario de ${label}`} />
      <LockedInput placeholder="Contraseña" type="password" />
    </div>
  );
}

function OrderGroup({ store, items }: { store: StoreId; items: CartItem[] }) {
  const subtotal = items.reduce((s, i) => s + i.estimated_total, 0);
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full ${STORE_COLORS[store]}`}>
          {STORE_LABELS[store]}
        </span>
        <span className="text-[12px] font-semibold text-slate-600">
          S/ {subtotal.toFixed(2)}
        </span>
      </div>
      <div className="space-y-1.5 pl-1">
        {items.map((item, i) => (
          <div key={i} className="flex items-start justify-between gap-3">
            <p className="text-[12px] text-slate-600 leading-snug flex-1">{item.selected_product}</p>
            <span className="text-[12px] text-slate-500 font-mono shrink-0">
              S/ {item.estimated_total.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function CheckoutPanel({ cart, onClose }: Props) {
  // Group items by store
  const storeGroups = cart.cart.reduce<Record<string, CartItem[]>>((acc, item) => {
    (acc[item.store] ??= []).push(item);
    return acc;
  }, {});
  const activeStores = Object.keys(storeGroups) as StoreId[];

  return (
    <div className="flex flex-col h-full overflow-hidden font-sans antialiased">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#EDF0F2] bg-white shrink-0">
        <div>
          <h2 className="text-[14px] font-semibold text-slate-800 tracking-tight">
            Confirmar Pedido
          </h2>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {cart.cart.length} ítem(s) · {activeStores.length} tienda(s)
          </p>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          aria-label="Cerrar"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M1 1l10 10M11 1L1 11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">

        {/* ── Order summary ───────────────────────────────────────────── */}
        <section>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.14em] mb-3">
            Resumen del pedido
          </p>
          <div className="border border-[#EDF0F2] rounded-2xl divide-y divide-[#EDF0F2]">
            {activeStores.map((store) => (
              <div key={store} className="px-4 py-3.5">
                <OrderGroup store={store} items={storeGroups[store]} />
              </div>
            ))}
            <div className="px-4 py-3.5 flex items-center justify-between bg-slate-50/60">
              <span className="text-[13px] font-semibold text-slate-700">Total estimado</span>
              <span className="text-[16px] font-bold text-[#1B1D1F] tracking-tight">
                S/ {cart.total_estimated_cost.toFixed(2)}
              </span>
            </div>
          </div>
        </section>

        {/* ── Store credentials ───────────────────────────────────────── */}
        <section>
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.14em] mb-3">
            Acceso a tus cuentas
          </p>
          <div className="space-y-4">
            {activeStores.map((store) => (
              <div key={store} className="border border-[#EDF0F2] rounded-2xl px-4 py-4">
                <StoreCredentials store={store} />
              </div>
            ))}
          </div>
        </section>

        {/* ── Cartly Plus upsell ──────────────────────────────────────── */}
        <section className="bg-gradient-to-br from-mint-50 to-white border border-mint-200/70 rounded-2xl px-4 py-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-mint-500 flex items-center justify-center text-white shrink-0 shadow-[0_2px_10px_rgba(20,213,181,0.30)]">
              <SparkleIcon />
            </div>
            <div className="flex-1">
              <p className="text-[13px] font-semibold text-slate-800 mb-1">
                Cartly Plus
              </p>
              <p className="text-[12px] text-slate-500 leading-relaxed">
                La compra automática todavía no está activa. Por ahora puedes abrir los productos desde el carrito y completar la compra manualmente.
              </p>
              <button
                disabled
                className="mt-3 text-[12px] font-semibold text-mint-600 hover:text-mint-700 flex items-center gap-1 transition-colors cursor-not-allowed opacity-60"
              >
                Conocer Cartly Plus
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                  <path d="M2 6h8M6 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </section>

      </div>

      {/* Footer — disabled CTA */}
      <div className="px-5 py-4 border-t border-[#EDF0F2] bg-white shrink-0 space-y-2">
        <button
          disabled
          className="w-full flex items-center justify-center gap-2.5 bg-slate-100 text-slate-400 text-[14px] font-semibold rounded-full py-3.5 cursor-not-allowed"
        >
          <LockIcon />
          Compra automática próximamente
        </button>
        <p className="text-center text-[11px] text-slate-400">
          Usa los enlaces de cada producto para comprar manualmente en la tienda.
        </p>
      </div>

    </div>
  );
}
