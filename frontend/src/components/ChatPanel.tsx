import { useEffect, useRef, useState, useCallback } from "react";
import type { CartRecommendation, ChatResponse, ShoppingIntentItem } from "../types";
import { postChat } from "../api/client";
import { CandidateProductsTable } from "./CandidateProductsTable";

type Message =
  | { role: "user"; text: string; id: number }
  | { role: "assistant"; response: ChatResponse; id: number }
  | { role: "error"; text: string; id: number };

interface Props {
  onCartUpdate: (cart: CartRecommendation | null) => void;
}

let _id = 0;
const nextId = () => ++_id;

const LOADING_STEPS = [
  "Analizando tu pedido…",
  "Buscando en Metro…",
  "Buscando en Plaza Vea…",
  "Buscando en Vivanda…",
  "Buscando en Tottus…",
  "Comparando precios y marcas…",
  "Armando tu carrito optimizado…",
];

const SpeechRecognitionClass: (new () => SpeechRecognition) | undefined =
  (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;

function CheckIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 11 11" fill="none" aria-hidden="true">
      <path d="M1.5 5.5l2.5 2.5 5.5-5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 2a3.5 3.5 0 013.5 3.5v6a3.5 3.5 0 01-7 0V5.5A3.5 3.5 0 0112 2z" />
      <path d="M6.5 12a5.5 5.5 0 0011 0" />
      <path d="M12 18v3" />
      <path d="M9 21h6" />
    </svg>
  );
}

function IntentSummary({ items }: { items: ShoppingIntentItem[] }) {
  return (
    <ul className="mt-2 space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-center gap-2 text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-mint-400 shrink-0" />
          <span className="font-medium text-slate-700">{item.product_query}</span>
          {item.quantity != null && (
            <span className="text-slate-400">
              {item.quantity} {item.unit ?? ""}
            </span>
          )}
          {item.brand_preference && (
            <span className="text-slate-400">({item.brand_preference})</span>
          )}
        </li>
      ))}
    </ul>
  );
}

function AssistantMessage({ response }: { response: ChatResponse }) {
  const items = response.intent?.shopping_intent ?? [];
  const hasCart = (response.cart?.cart.length ?? 0) > 0;

  return (
    <div className="space-y-2">
      {items.length > 0 ? (
        <>
          <p className="text-sm text-slate-600">
            Encontré{" "}
            <span className="font-semibold text-slate-800">{items.length} producto(s)</span>:
          </p>
          <IntentSummary items={items} />
        </>
      ) : (
        <p className="text-sm text-slate-400">No pude interpretar el pedido.</p>
      )}

      {hasCart && (
        <div className="mt-2 pt-2 border-t border-slate-100">
          <p className="text-xs font-medium text-mint-600 flex items-center gap-1.5">
            <CheckIcon />
            Carrito listo — revisa el panel derecho
          </p>
          <CandidateProductsTable candidates={response.candidate_products} />
        </div>
      )}

      {response.warnings.map((w, i) => (
        <p key={i} className="text-xs text-amber-600 bg-amber-50 rounded-lg px-2.5 py-1.5 mt-1">
          ⚠ {w}
        </p>
      ))}
    </div>
  );
}

export function ChatPanel({ onCartUpdate }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [listening, setListening] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const loadingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const baseInputRef = useRef("");

  const startLoadingCycle = useCallback(() => {
    setLoadingStep(0);
    loadingTimerRef.current = setInterval(() => {
      setLoadingStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1));
    }, 4_500);
  }, []);

  const stopLoadingCycle = useCallback(() => {
    if (loadingTimerRef.current) {
      clearInterval(loadingTimerRef.current);
      loadingTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      stopLoadingCycle();
      recognitionRef.current?.stop();
    };
  }, [stopLoadingCycle]);

  function startListening() {
    if (!SpeechRecognitionClass || loading) return;
    const recognition = new SpeechRecognitionClass() as SpeechRecognition;
    recognition.lang = "es-PE";
    recognition.interimResults = true;
    recognition.continuous = false;
    baseInputRef.current = input;

    recognition.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = Array.from(e.results)
        .map((r) => r[0].transcript)
        .join("");
      const base = baseInputRef.current;
      const sep = base && !base.endsWith(" ") ? " " : "";
      setInput(base + (base ? sep : "") + transcript);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }

  function stopListening() {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
  }

  function toggleMic() {
    if (listening) stopListening();
    else startListening();
  }

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text, id: nextId() }]);
    setLoading(true);
    startLoadingCycle();

    try {
      const response = await postChat(text);
      setMessages((prev) => [...prev, { role: "assistant", response, id: nextId() }]);
      onCartUpdate(response.cart);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "error", text: String(err), id: nextId() },
      ]);
    } finally {
      stopLoadingCycle();
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-[#F7F8F8]">

      {/* ── Panel header ──────────────────────────────────────────────── */}
      <div className="px-6 py-3.5 border-b border-[#E8EBED] bg-white">
        <h2 className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.12em]">
          Asistente de Compras
        </h2>
      </div>

      {/* ── Messages ──────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">

        {messages.length === 0 && (
          /* ── Welcome screen ──────────────────────────────────────── */
          <div className="relative flex flex-col items-center justify-center h-full text-center px-8">

            {/* Ambient glow */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden rounded-2xl">
              <div className="w-80 h-80 bg-mint-500 opacity-[0.05] rounded-full blur-3xl" />
            </div>

            {/* Icon */}
            <div className="relative w-14 h-14 rounded-2xl bg-white shadow-[0_4px_24px_rgba(0,0,0,0.08)] flex items-center justify-center mb-5">
              <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
                <path d="M3 3.5h2.5L9.5 16h9.5l2.8-8.5H7.5" stroke="#14d5b5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <circle cx="10.5" cy="21" r="1.8" fill="#14d5b5"/>
                <circle cx="17.5" cy="21" r="1.8" fill="#14d5b5"/>
              </svg>
            </div>

            {/* Headline */}
            <h3 className="relative text-[22px] font-semibold text-[#1B1D1F] tracking-tight leading-snug mb-3">
              De una frase<br />
              <span className="text-mint-500">a tu carrito completo.</span>
            </h3>

            {/* Subtitle */}
            <p className="relative text-sm text-slate-400 leading-relaxed max-w-xs mb-6">
              Escribe lo que necesitas en lenguaje natural — precios, cantidades,
              marcas — y armaré el carrito optimizado entre Metro, Plaza Vea,
              Vivanda y Tottus.
            </p>

            {/* Example chip */}
            <div
              className="relative text-xs text-slate-500 bg-white border border-[#E8EBED] rounded-xl px-4 py-3 shadow-[0_2px_12px_rgba(0,0,0,0.05)] cursor-pointer hover:border-mint-300 hover:shadow-[0_2px_16px_rgba(20,213,181,0.12)] max-w-sm"
              onClick={() => {
                setInput("Necesito 5 kg de arroz, 2 litros de leche Gloria y papel higiénico barato.");
                inputRef.current?.focus();
              }}
            >
              <span className="text-[10px] font-semibold text-slate-300 uppercase tracking-widest block mb-1">
                Ejemplo
              </span>
              "Necesito 5 kg de arroz, 2 litros de leche Gloria y papel higiénico barato."
            </div>

          </div>
        )}

        {messages.map((msg) => {

          if (msg.role === "user") {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-xs bg-gradient-to-br from-mint-500 to-mint-600 text-white text-sm rounded-2xl rounded-tr-none px-4 py-2.5 shadow-[0_4px_16px_rgba(20,213,181,0.25)]">
                  {msg.text}
                </div>
              </div>
            );
          }

          if (msg.role === "error") {
            return (
              <div key={msg.id} className="flex justify-start">
                <div className="max-w-sm bg-red-50 border border-red-100 text-red-600 text-sm rounded-2xl rounded-tl-none px-4 py-3">
                  <span className="font-medium">Error: </span>{msg.text}
                </div>
              </div>
            );
          }

          return (
            <div key={msg.id} className="flex justify-start">
              <div className="max-w-sm bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-[0_2px_16px_rgba(0,0,0,0.07)]">
                <AssistantMessage response={msg.response} />
              </div>
            </div>
          );

        })}

        {/* ── AI thinking indicator ──────────────────────────────────── */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3.5 shadow-[0_2px_16px_rgba(0,0,0,0.07)] min-w-[220px]">
              <div className="flex items-center gap-1.5 mb-2">
                <span className="w-1.5 h-1.5 bg-mint-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-mint-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-mint-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
              <p className="text-xs text-slate-400 transition-all duration-500">
                {LOADING_STEPS[loadingStep]}
              </p>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ─────────────────────────────────────────────────── */}
      <div className="px-4 py-3.5 border-t border-[#E8EBED] bg-white">
        <div className="flex gap-2 items-center">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={listening ? "Escuchando…" : "¿Qué necesitas hoy?"}
            disabled={loading}
            className="flex-1 text-sm bg-[#F7F8F8] border border-[#DDE3E6] rounded-full px-5 py-2.5 focus:outline-none focus:ring-2 focus:ring-mint-400 focus:border-transparent focus:bg-white disabled:opacity-50 placeholder:text-slate-400"
          />
          {SpeechRecognitionClass && (
            <button
              type="button"
              onClick={toggleMic}
              disabled={loading}
              title={listening ? "Detener dictado" : "Dictar mensaje"}
              aria-label={listening ? "Detener dictado" : "Dictar mensaje"}
              style={listening ? { animation: "micRing 1.4s ease-in-out infinite" } : undefined}
              className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed ${
                listening
                  ? "bg-red-50 text-red-500"
                  : "bg-[#F7F8F8] text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              }`}
            >
              <MicIcon />
            </button>
          )}
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="text-[13px] font-semibold bg-mint-500 text-white rounded-full px-5 py-2.5 hover:bg-mint-600 disabled:opacity-40 disabled:cursor-not-allowed shadow-[0_2px_10px_rgba(20,213,181,0.25)] hover:shadow-[0_4px_18px_rgba(20,213,181,0.38)] shrink-0"
          >
            Enviar
          </button>
        </div>
      </div>

    </div>
  );
}
