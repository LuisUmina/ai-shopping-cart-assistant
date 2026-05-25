import { useEffect, useState } from "react";
import { getPreferences } from "./api/client";
import { CartSummary } from "./components/CartSummary";
import { ChatPanel } from "./components/ChatPanel";
import { PreferencesPanel } from "./components/PreferencesPanel";
import type { CartRecommendation, UserPreferences } from "./types";

const DEFAULT_PREFS: UserPreferences = {
  price_priority: "high",
  brand_priority: "medium",
  known_brands_only: false,
  allow_substitutions: true,
  allow_equivalent_sizes: true,
  preferred_stores: ["plaza_vea", "metro", "vivanda", "tottus"],
  excluded_brands: [],
  preferred_brands: [],
  max_candidates_per_product: 5,
};

export default function App() {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFS);
  const [cart, setCart] = useState<CartRecommendation | null>(null);

  useEffect(() => {
    getPreferences()
      .then(setPreferences)
      .catch(() => {});
  }, []);

  return (
    <div className="h-screen flex flex-col bg-[#F7F8F8] font-sans text-[#1B1D1F] antialiased">

      {/* ── Header ───────────────────────────────────────────────────────── */}
      <header className="h-14 flex items-center px-6 bg-white border-b border-[#E8EBED] shrink-0">

        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-mint-500 flex items-center justify-center shadow-[0_2px_8px_rgba(20,213,181,0.35)]">
            <svg width="15" height="15" viewBox="0 0 15 15" fill="none" aria-hidden="true">
              <path d="M1.5 2h1.8l2.4 7h5.8l1.7-5H5" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="6" cy="12.5" r="1.2" fill="white"/>
              <circle cx="10.5" cy="12.5" r="1.2" fill="white"/>
            </svg>
          </div>
          <span className="font-semibold text-[15px] tracking-tight text-[#1B1D1F]">
            CartAI
          </span>
        </div>

        {/* Divider */}
        <div className="mx-4 h-4 w-px bg-[#E8EBED]" />

        {/* Tagline */}
        <span className="text-xs text-slate-400 hidden sm:block">
          Asistente de compras inteligente
        </span>

        {/* Right side */}
        <div className="ml-auto flex items-center gap-3">
          <span className="text-[11px] font-semibold text-mint-700 bg-mint-50 border border-mint-200 px-2.5 py-1 rounded-full tracking-wide">
            BETA
          </span>
        </div>
      </header>

      {/* ── Main layout ──────────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">
        <PreferencesPanel preferences={preferences} onChange={setPreferences} />
        <ChatPanel onCartUpdate={setCart} />
        <CartSummary cart={cart} />
      </div>

    </div>
  );
}
