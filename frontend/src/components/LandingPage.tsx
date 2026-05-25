interface Props {
  onEnter: () => void;
}

const EMBED_URL =
  "https://www.youtube.com/embed/U5rhqsqGC7o" +
  "?autoplay=1&mute=1&rel=0&modestbranding=1&loop=1" +
  "&playlist=U5rhqsqGC7o&cc_load_policy=0&iv_load_policy=3";

function ArrowRight({ className = "" }: { className?: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={className} aria-hidden="true">
      <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CartLogo({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 15 15" fill="none" aria-hidden="true">
      <path d="M1.5 2h1.8l2.4 7h5.8l1.7-5H5" stroke="white" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="6" cy="12.5" r="1.2" fill="white" />
      <circle cx="10.5" cy="12.5" r="1.2" fill="white" />
    </svg>
  );
}

const FEATURES = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#14d5b5" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 2l2 5.5L19.5 9.5 14 12 12 18l-2-6L4.5 9.5 10 7.5z" />
      </svg>
    ),
    title: "Lenguaje natural",
    desc: "Escribe como hablas. Sin formularios, sin categorías, sin filtros.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#14d5b5" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
    title: "4 supermercados",
    desc: "Metro, Plaza Vea, Vivanda y Tottus comparados en paralelo.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#14d5b5" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M6 2H4L2 4.5h2l3 10h11l3-9H8.5" />
        <circle cx="9" cy="20" r="1.5" />
        <circle cx="17" cy="20" r="1.5" />
        <path d="M11 11.5l2 2 4-4" />
      </svg>
    ),
    title: "Carrito optimizado",
    desc: "El mejor precio, marca y presentación, elegido automáticamente.",
  },
];

export function LandingPage({ onEnter }: Props) {
  return (
    <div className="min-h-screen bg-white font-sans antialiased overflow-x-hidden">

      {/* ── Ambient orbs ──────────────────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div
          className="absolute -top-48 -right-48 w-[700px] h-[700px] bg-mint-500 rounded-full blur-[140px]"
          style={{ animation: "pulseGlow 6s ease-in-out infinite", opacity: 0.06 }}
        />
        <div
          className="absolute top-1/2 -left-72 w-[600px] h-[600px] bg-mint-400 rounded-full blur-[120px]"
          style={{ animation: "pulseGlow 8s ease-in-out infinite 2s", opacity: 0.04 }}
        />
        <div
          className="absolute -bottom-40 right-1/4 w-[400px] h-[400px] bg-mint-300 rounded-full blur-[100px]"
          style={{ animation: "pulseGlow 10s ease-in-out infinite 4s", opacity: 0.04 }}
        />
      </div>

      {/* ── Nav ───────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 sm:px-10 h-16 bg-white/80 backdrop-blur-xl border-b border-[#E8EBED]/70">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-mint-500 flex items-center justify-center shadow-[0_2px_14px_rgba(20,213,181,0.40)]">
            <CartLogo size={16} />
          </div>
          <span className="font-semibold text-[16px] tracking-tight text-[#1B1D1F]">
            Cartly AI
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] font-semibold text-mint-700 bg-mint-50 border border-mint-200 px-2.5 py-1 rounded-full tracking-wide">
            BETA
          </span>
          <button
            onClick={onEnter}
            className="hidden sm:inline-flex items-center gap-2 text-[13px] font-semibold text-[#1B1D1F] hover:text-mint-600 transition-colors duration-200"
          >
            Entrar
            <ArrowRight />
          </button>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-16 pb-32 px-6 text-center">

        {/* Beta badge */}
        <div
          className="mb-7 inline-flex items-center gap-2 bg-mint-50/80 border border-mint-200/70 rounded-full px-4 py-1.5 backdrop-blur-sm"
          style={{ animation: "fadeUp 0.7s ease both" }}
        >
          <span className="w-1.5 h-1.5 bg-mint-500 rounded-full" style={{ animation: "pulseGlow 2s ease-in-out infinite", opacity: 1 }} />
          <span className="text-[12px] font-medium text-mint-700 tracking-wide">
            Acceso anticipado · Beta privada
          </span>
        </div>

        {/* Headline */}
        <h1
          className="max-w-4xl text-[46px] sm:text-[64px] lg:text-[80px] font-semibold tracking-[-0.035em] leading-[1.04] text-[#1B1D1F]"
          style={{ animation: "fadeUp 0.7s 0.08s ease both" }}
        >
          De una frase a<br />
          <span className="text-mint-500">tu carrito completo.</span>
        </h1>

        {/* Subtitle */}
        <p
          className="mt-6 max-w-xl text-[17px] sm:text-[19px] text-slate-400 leading-relaxed font-light"
          style={{ animation: "fadeUp 0.7s 0.16s ease both" }}
        >
          Cartly AI convierte lenguaje natural en compras inteligentes,
          comparando supermercados y optimizando tu carrito en segundos.
        </p>

        {/* CTA */}
        <div
          className="mt-10 flex flex-col sm:flex-row items-center gap-4"
          style={{ animation: "fadeUp 0.7s 0.24s ease both" }}
        >
          <button
            onClick={onEnter}
            className="group inline-flex items-center gap-2.5 bg-mint-500 text-white text-[15px] font-semibold rounded-full px-8 py-4 shadow-[0_4px_28px_rgba(20,213,181,0.38)] hover:bg-mint-600 hover:shadow-[0_8px_36px_rgba(20,213,181,0.48)] hover:-translate-y-0.5 transition-all duration-200"
          >
            Explorar Beta
            <ArrowRight className="group-hover:translate-x-0.5 transition-transform duration-200" />
          </button>
          <span className="text-[13px] text-slate-400">
            Gratis durante la beta
          </span>
        </div>

        {/* Scroll hint */}
        <div
          className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
          style={{ animation: "fadeIn 0.7s 1.2s ease both" }}
        >
          <span className="text-[10px] text-slate-300 font-semibold tracking-[0.18em] uppercase">
            Ver demo
          </span>
          <div className="flex flex-col items-center gap-1" style={{ animation: "floatY 2.5s ease-in-out infinite" }}>
            <div className="w-px h-6 bg-gradient-to-b from-slate-200 to-transparent" />
            <svg width="10" height="6" viewBox="0 0 10 6" fill="none" aria-hidden="true">
              <path d="M1 1l4 4 4-4" stroke="#CBD5E1" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </div>

      </section>

      {/* ── Video ─────────────────────────────────────────────────────────── */}
      <section
        className="relative px-5 sm:px-12 lg:px-20 pb-28"
        style={{ animation: "fadeUp 0.9s 0.35s ease both" }}
      >
        <div className="max-w-5xl mx-auto">

          {/* Section label */}
          <div className="text-center mb-7">
            <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-[0.22em]">
              Demo · 40 segundos
            </span>
          </div>

          {/* Cinematic video card */}
          <div className="relative rounded-[28px] overflow-hidden shadow-[0_40px_100px_rgba(0,0,0,0.14),0_8px_32px_rgba(0,0,0,0.08)] border border-white/60 bg-[#0c0c0c]">

            {/* Browser chrome */}
            <div className="flex items-center gap-1.5 px-4 py-3 bg-[#161616] border-b border-white/[0.05]">
              <span className="w-3 h-3 rounded-full bg-[#ff5f57] opacity-90" />
              <span className="w-3 h-3 rounded-full bg-[#febc2e] opacity-90" />
              <span className="w-3 h-3 rounded-full bg-[#28c840] opacity-90" />
              <div className="flex-1 mx-6 flex justify-center">
                <div className="flex items-center gap-1.5 bg-white/[0.06] border border-white/[0.08] rounded-md px-3 py-1 w-44">
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="none" aria-hidden="true">
                    <path d="M1 4a3 3 0 106 0 3 3 0 00-6 0z" stroke="#6B7280" strokeWidth="1" />
                    <path d="M3.5 1.5C3 2.5 3 5.5 3.5 6.5M4.5 1.5C5 2.5 5 5.5 4.5 6.5M1 4h6" stroke="#6B7280" strokeWidth="0.8" strokeLinecap="round" />
                  </svg>
                  <span className="text-[10px] text-white/25 font-medium tracking-wide">cartly.ai</span>
                </div>
              </div>
            </div>

            {/* Iframe */}
            <div className="aspect-video">
              <iframe
                src={EMBED_URL}
                className="w-full h-full"
                allow="autoplay; encrypted-media; picture-in-picture"
                allowFullScreen
                title="Cartly AI — Demo"
              />
            </div>

          </div>

          {/* Soft reflection */}
          <div className="h-12 mx-8 rounded-b-[28px] bg-gradient-to-b from-black/[0.04] to-transparent blur-xl -mt-2 pointer-events-none" aria-hidden="true" />

        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section
        className="relative px-5 sm:px-12 lg:px-20 pb-28"
        style={{ animation: "fadeUp 0.9s 0.45s ease both" }}
      >
        <div className="max-w-4xl mx-auto">

          <div className="text-center mb-10">
            <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-[0.22em]">
              Cómo funciona
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group bg-white rounded-2xl border border-[#EDF0F2] p-6 hover:border-mint-200 hover:shadow-[0_6px_32px_rgba(20,213,181,0.09)] transition-all duration-250"
              >
                <div className="w-11 h-11 rounded-xl bg-mint-50 flex items-center justify-center mb-5 group-hover:bg-mint-100/60 transition-colors duration-200">
                  {f.icon}
                </div>
                <h3 className="text-[15px] font-semibold text-[#1B1D1F] mb-2 tracking-tight">
                  {f.title}
                </h3>
                <p className="text-[13px] text-slate-400 leading-relaxed">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>

        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────────── */}
      <section
        className="relative px-6 pb-32 text-center"
        style={{ animation: "fadeUp 0.9s 0.55s ease both" }}
      >
        <div className="max-w-lg mx-auto">

          {/* Ambient mint glow behind text */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none" aria-hidden="true">
            <div className="w-96 h-48 bg-mint-400 opacity-[0.06] rounded-full blur-3xl" />
          </div>

          <h2 className="relative text-[34px] sm:text-[44px] font-semibold tracking-[-0.03em] text-[#1B1D1F] leading-tight mb-4">
            Listo para el<br />
            <span className="text-mint-500">carrito inteligente.</span>
          </h2>
          <p className="relative text-[15px] text-slate-400 mb-9">
            Gratis durante el acceso anticipado.
          </p>
          <button
            onClick={onEnter}
            className="group relative inline-flex items-center gap-2.5 bg-mint-500 text-white text-[15px] font-semibold rounded-full px-9 py-4 shadow-[0_4px_28px_rgba(20,213,181,0.38)] hover:bg-mint-600 hover:shadow-[0_8px_40px_rgba(20,213,181,0.50)] hover:-translate-y-0.5 transition-all duration-200"
          >
            Iniciar ahora
            <ArrowRight className="group-hover:translate-x-0.5 transition-transform duration-200" />
          </button>

        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-[#EDF0F2] px-6 sm:px-10 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-[12px] text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-md bg-mint-500 flex items-center justify-center shadow-[0_1px_6px_rgba(20,213,181,0.30)]">
            <CartLogo size={10} />
          </div>
          <span className="font-medium text-slate-500">Cartly AI</span>
          <span className="text-slate-300">·</span>
          <span>2025</span>
        </div>
        <span className="text-slate-300 text-[11px] tracking-wide">
          Impulsado por IA ✦
        </span>
      </footer>

    </div>
  );
}
