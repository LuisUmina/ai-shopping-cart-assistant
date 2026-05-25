import { useEffect, useState } from "react";
import { getPreferences } from "./api/client";
import { CartSummary } from "./components/CartSummary";
import { ChatPanel } from "./components/ChatPanel";
import { PreferencesPanel } from "./components/PreferencesPanel";
import type { CartRecommendation, UserPreferences } from "./types";

type Tab = "prefs" | "chat" | "cart";

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

// ── Bottom nav icons ──────────────────────────────────────────────────────────

function IconPrefs() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <line x1="4" y1="6"  x2="20" y2="6"  />
      <line x1="4" y1="12" x2="20" y2="12" />
      <line x1="4" y1="18" x2="20" y2="18" />
      <circle cx="8"  cy="6"  r="2.5" fill="currentColor" stroke="none" />
      <circle cx="16" cy="12" r="2.5" fill="currentColor" stroke="none" />
      <circle cx="10" cy="18" r="2.5" fill="currentColor" stroke="none" />
    </svg>
  );
}

function IconChat() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  );
}

function IconCart() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M6 2H4L2 5h2l3 10h11l3-9H8.5" />
      <circle cx="9"  cy="20" r="1.5" />
      <circle cx="17" cy="20" r="1.5" />
    </svg>
  );
}

function TabButton({
  label,
  icon,
  active,
  badge,
  onClick,
}: {
  label: string;
  icon: React.ReactNode;
  active: boolean;
  badge?: number;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 flex flex-col items-center justify-center gap-1 py-2.5 transition-colors duration-150 ${
        active ? "text-mint-600" : "text-slate-400 hover:text-slate-600"
      }`}
    >
      <span className="relative">
        {icon}
        {badge ? (
          <span className="absolute -top-1.5 -right-2 min-w-[16px] h-4 bg-mint-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center px-0.5">
            {badge > 9 ? "9+" : badge}
          </span>
        ) : null}
      </span>
      <span className="text-[10px] font-medium leading-none">{label}</span>
    </button>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFS);
  const [cart, setCart] = useState<CartRecommendation | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("chat");

  useEffect(() => {
    getPreferences()
      .then(setPreferences)
      .catch(() => {});
  }, []);

  const cartItemCount = cart?.cart.length ?? 0;

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
            Cartly AI
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

        {/* Preferences panel */}
        <div className={`${activeTab === "prefs" ? "flex flex-1" : "hidden"} lg:flex lg:flex-none flex-col overflow-hidden`}>
          <PreferencesPanel preferences={preferences} onChange={setPreferences} />
        </div>

        {/* Chat panel */}
        <div className={`${activeTab === "chat" ? "flex flex-1" : "hidden"} lg:flex lg:flex-1 flex-col min-w-0 overflow-hidden`}>
          <ChatPanel onCartUpdate={setCart} />
        </div>

        {/* Cart panel */}
        <div className={`${activeTab === "cart" ? "flex flex-1" : "hidden"} lg:flex lg:flex-none flex-col overflow-hidden`}>
          <CartSummary cart={cart} />
        </div>

      </div>

      {/* ── Bottom navigation — mobile only ──────────────────────────────── */}
      <nav className="lg:hidden flex items-stretch border-t border-[#E8EBED] bg-white shrink-0">
        <TabButton
          label="Preferencias"
          icon={<IconPrefs />}
          active={activeTab === "prefs"}
          onClick={() => setActiveTab("prefs")}
        />
        <TabButton
          label="Chat"
          icon={<IconChat />}
          active={activeTab === "chat"}
          onClick={() => setActiveTab("chat")}
        />
        <TabButton
          label="Carrito"
          icon={<IconCart />}
          active={activeTab === "cart"}
          badge={cartItemCount}
          onClick={() => setActiveTab("cart")}
        />
      </nav>

    </div>
  );
}
