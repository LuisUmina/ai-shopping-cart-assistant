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
      .catch(() => {}); // use defaults if backend is down
  }, []);

  return (
    <div className="h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Top bar */}
      <header className="h-12 flex items-center px-5 border-b border-slate-200 bg-white shrink-0">
        <span className="font-semibold text-slate-800 text-sm">
          AI Shopping Cart Assistant
        </span>
        <span className="ml-2 text-xs text-slate-400">MVP</span>
      </header>

      {/* Main layout */}
      <div className="flex-1 flex overflow-hidden">
        <PreferencesPanel preferences={preferences} onChange={setPreferences} />
        <ChatPanel onCartUpdate={setCart} />
        <CartSummary cart={cart} />
      </div>
    </div>
  );
}
