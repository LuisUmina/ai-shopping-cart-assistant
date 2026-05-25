import { useEffect, useRef, useState } from "react";
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

function IntentSummary({ items }: { items: ShoppingIntentItem[] }) {
  return (
    <ul className="mt-1 space-y-1">
      {items.map((item, i) => (
        <li key={i} className="text-xs text-slate-600">
          •{" "}
          <span className="font-medium">{item.product_query}</span>
          {item.quantity != null && (
            <span className="text-slate-400">
              {" "}— {item.quantity} {item.unit ?? ""}
            </span>
          )}
          {item.brand_preference && (
            <span className="text-slate-400"> ({item.brand_preference})</span>
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
    <div className="space-y-1">
      {items.length > 0 ? (
        <>
          <p className="text-sm text-slate-700">
            Entendí tu pedido con{" "}
            <span className="font-semibold">{items.length} producto(s)</span>:
          </p>
          <IntentSummary items={items} />
        </>
      ) : (
        <p className="text-sm text-slate-500">No pude interpretar el pedido.</p>
      )}

      {hasCart && (
        <>
          <p className="text-xs text-green-700 mt-2">
            ✓ Carrito listo — revisa el panel derecho.
          </p>
          <CandidateProductsTable candidates={response.candidate_products} />
        </>
      )}

      {response.warnings.map((w, i) => (
        <p key={i} className="text-xs text-amber-600 mt-1">⚠ {w}</p>
      ))}
    </div>
  );
}

export function ChatPanel({ onCartUpdate }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", text, id: nextId() }]);
    setLoading(true);

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
    <div className="flex-1 flex flex-col min-w-0">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 bg-white">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
          Asistente de Compras
        </h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="text-4xl mb-3">🛍</div>
            <p className="text-slate-400 text-sm">
              Escribe tu pedido en lenguaje natural.
            </p>
            <p className="text-slate-300 text-xs mt-1">
              Ej: "Necesito 5 kg de arroz, 2 litros de leche Gloria y papel higiénico barato."
            </p>
          </div>
        )}

        {messages.map((msg) => {
          if (msg.role === "user") {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-xs bg-indigo-600 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-2">
                  {msg.text}
                </div>
              </div>
            );
          }

          if (msg.role === "error") {
            return (
              <div key={msg.id} className="flex justify-start">
                <div className="max-w-sm bg-red-50 border border-red-200 text-red-700 text-sm rounded-2xl rounded-tl-sm px-4 py-2">
                  Error: {msg.text}
                </div>
              </div>
            );
          }

          return (
            <div key={msg.id} className="flex justify-start">
              <div className="max-w-sm bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <AssistantMessage response={msg.response} />
              </div>
            </div>
          );
        })}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-slate-200 bg-white">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu pedido aquí…"
            disabled={loading}
            className="flex-1 text-sm border border-slate-200 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:bg-slate-50 disabled:text-slate-400"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="text-sm font-medium bg-indigo-600 text-white rounded-xl px-4 py-2 hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            Enviar
          </button>
        </div>
      </div>
    </div>
  );
}
