import { useEffect, useRef, useState } from "react";
import type { Priority, StoreId, UserPreferences } from "../types";
import { PRIORITY_LABELS, STORE_LABELS } from "../types";
import { savePreferences } from "../api/client";

const ALL_STORES: StoreId[] = ["plaza_vea", "metro", "vivanda", "tottus"];
const PRIORITIES: Priority[] = ["high", "medium", "low"];

const STORE_DOTS: Record<StoreId, string> = {
  plaza_vea: "bg-orange-400",
  metro:     "bg-sky-500",
  vivanda:   "bg-pink-400",
  tottus:    "bg-emerald-500",
};

type SaveStatus = "idle" | "saving" | "saved" | "error";

interface Props {
  preferences: UserPreferences;
  onChange: (prefs: UserPreferences) => void;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.12em] mb-3">
      {children}
    </p>
  );
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex shrink-0 h-5 w-10 cursor-pointer rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-mint-500 focus-visible:ring-offset-1 ${
        checked ? "bg-mint-500" : "bg-slate-200"
      }`}
    >
      <span
        className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-200 ${
          checked ? "translate-x-5" : "translate-x-0"
        }`}
      />
    </button>
  );
}

export function PreferencesPanel({ preferences, onChange }: Props) {
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    };
  }, []);

  function queueSave(next: UserPreferences) {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
    setSaveStatus("saving");
    saveTimerRef.current = setTimeout(async () => {
      try {
        const updated = await savePreferences(next);
        onChange(updated);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("error");
      }
    }, 500);
  }

  function updatePreferences(next: UserPreferences) {
    onChange(next);
    queueSave(next);
  }

  function toggleStore(store: StoreId) {
    const current = preferences.preferred_stores;
    const updated = current.includes(store)
      ? current.filter((s) => s !== store)
      : [...current, store];
    updatePreferences({ ...preferences, preferred_stores: updated });
  }

  return (
    <aside className="w-full lg:w-64 h-full max-h-full flex flex-col min-h-0 overflow-hidden bg-white border-r border-[#E8EBED] shrink-0">

      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-[#F0F2F3]">
        <h2 className="text-[10px] font-semibold text-slate-400 uppercase tracking-[0.12em]">
          Preferencias
        </h2>
      </div>

      {/* Body */}
      <div className="flex-1 basis-0 min-h-0 overflow-y-auto overscroll-contain px-5 pt-5 pb-6 space-y-6">

        {/* ── Tiendas ─────────────────────────────────────────────────── */}
        <section>
          <SectionLabel>Tiendas</SectionLabel>
          <div className="space-y-1.5">
            {ALL_STORES.map((store) => {
              const active = preferences.preferred_stores.includes(store);
              return (
                <button
                  key={store}
                  type="button"
                  onClick={() => toggleStore(store)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left ${
                    active
                      ? "bg-mint-50 border border-mint-200"
                      : "bg-[#F7F8F8] border border-transparent hover:bg-slate-100"
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full shrink-0 ${STORE_DOTS[store]} ${
                      active ? "" : "opacity-25"
                    }`}
                  />
                  <span
                    className={`text-[13px] font-medium flex-1 ${
                      active ? "text-slate-800" : "text-slate-400"
                    }`}
                  >
                    {STORE_LABELS[store]}
                  </span>
                  {active && (
                    <svg width="11" height="11" viewBox="0 0 11 11" fill="none" aria-hidden="true">
                      <path
                        d="M1.5 5.5l2.5 2.5 5.5-5.5"
                        stroke="#14d5b5"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  )}
                </button>
              );
            })}
          </div>
        </section>

        {/* ── Prioridades ─────────────────────────────────────────────── */}
        <section className="space-y-3">
          <SectionLabel>Prioridades</SectionLabel>

          <div className="rounded-2xl bg-mint-50 border border-mint-100 px-3 py-3">
            <p className="text-[12px] font-semibold text-mint-800">Regla general</p>
            <p className="text-[11px] text-mint-700/80 leading-snug mt-1">
              Estas preferencias son tu punto de partida. Si escribes algo especifico en el chat, como "barato" o una marca concreta, tambien se considera en esa busqueda.
            </p>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1.5">
              Precio
            </label>
            <select
              value={preferences.price_priority}
              onChange={(e) =>
                updatePreferences({ ...preferences, price_priority: e.target.value as Priority })
              }
              className="w-full text-[13px] border border-[#DDE3E6] rounded-xl px-3 py-2 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-mint-400 focus:border-transparent appearance-none cursor-pointer"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-snug">
              Alta favorece el menor precio por kg, litro o unidad. Baja permite pagar mas si otro factor encaja mejor.
            </p>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1.5">
              Marca
            </label>
            <select
              value={preferences.brand_priority}
              onChange={(e) =>
                updatePreferences({ ...preferences, brand_priority: e.target.value as Priority })
              }
              className="w-full text-[13px] border border-[#DDE3E6] rounded-xl px-3 py-2 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-mint-400 focus:border-transparent appearance-none cursor-pointer"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-snug">
              Alta da mas peso a coincidencias de marca detectada o preferida. Media balancea marca con precio y presentacion.
            </p>
          </div>
        </section>

        {/* ── Opciones (toggles) ──────────────────────────────────────── */}
        <section className="space-y-4">
          <SectionLabel>Opciones</SectionLabel>

          <div className="flex items-center justify-between gap-4 rounded-2xl bg-slate-50 border border-slate-100 px-3 py-3 opacity-80">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-[13px] font-medium text-slate-500 leading-snug">
                Sustituciones
                </p>
                <span className="text-[9px] font-semibold text-slate-400 bg-white border border-slate-200 rounded-full px-1.5 py-0.5">
                  En preparacion
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                Esta opcion esta visible como futura mejora. Hoy la sustitucion depende principalmente de lo que escribes en el chat.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p className="text-[13px] font-medium text-slate-700 leading-snug">
                Marcas conocidas
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">
                Penaliza productos donde no se pudo detectar una marca clara.
              </p>
            </div>
            <Toggle
              checked={preferences.known_brands_only}
              onChange={(v) => updatePreferences({ ...preferences, known_brands_only: v })}
            />
          </div>
        </section>

        {/* ── Candidatos (slider) ─────────────────────────────────────── */}
        <section>
          <SectionLabel>Opciones evaluadas</SectionLabel>
          <div className="flex items-center justify-between mb-3">
            <span className="text-[13px] font-medium text-slate-600">Productos a comparar</span>
            <span className="text-sm font-semibold text-mint-600 bg-mint-50 border border-mint-200 w-8 h-7 flex items-center justify-center rounded-lg">
              {preferences.max_candidates_per_product}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={preferences.max_candidates_per_product}
            onChange={(e) =>
              updatePreferences({
                ...preferences,
                max_candidates_per_product: Number(e.target.value),
              })
            }
          />
          <div className="flex justify-between text-[11px] text-slate-300 mt-1.5">
            <span>Menos</span>
            <span>Más</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-2 leading-snug">
            Mas opciones aumenta alternativas y detalle, pero puede hacer la busqueda un poco mas lenta.
          </p>
        </section>

      </div>

      {/* ── Autosave status ──────────────────────────────────────────────── */}
      <div className="shrink-0 p-5 border-t border-[#F0F2F3] bg-white">
        <div className={`w-full rounded-2xl px-3 py-3 border ${
          saveStatus === "error"
            ? "bg-red-50 border-red-100 text-red-600"
            : saveStatus === "saving"
              ? "bg-amber-50 border-amber-100 text-amber-700"
              : "bg-mint-50 border-mint-100 text-mint-700"
        }`}>
          <p className="text-[12px] font-semibold">
            {saveStatus === "saving"
              ? "Guardando preferencias..."
              : saveStatus === "error"
                ? "No se pudo guardar"
                : "Preferencias autoguardadas"}
          </p>
          <p className="text-[11px] opacity-75 mt-0.5 leading-snug">
            {saveStatus === "error"
              ? "Revisa que el backend este activo antes de buscar."
              : "Los cambios se aplican en la siguiente busqueda."}
          </p>
        </div>
      </div>

    </aside>
  );
}
