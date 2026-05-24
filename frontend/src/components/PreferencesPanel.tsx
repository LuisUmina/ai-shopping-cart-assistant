import { useState } from "react";
import type { Priority, StoreId, UserPreferences } from "../types";
import { PRIORITY_LABELS, STORE_LABELS } from "../types";
import { savePreferences } from "../api/client";

const ALL_STORES: StoreId[] = ["plaza_vea", "metro", "vivanda", "tottus"];
const PRIORITIES: Priority[] = ["high", "medium", "low"];

interface Props {
  preferences: UserPreferences;
  onChange: (prefs: UserPreferences) => void;
}

export function PreferencesPanel({ preferences, onChange }: Props) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function toggleStore(store: StoreId) {
    const current = preferences.preferred_stores;
    const updated = current.includes(store)
      ? current.filter((s) => s !== store)
      : [...current, store];
    onChange({ ...preferences, preferred_stores: updated });
  }

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await savePreferences(preferences);
      onChange(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // silently fail — preferences are still updated in-memory
    } finally {
      setSaving(false);
    }
  }

  return (
    <aside className="w-72 flex flex-col border-r border-slate-200 bg-white">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
          Preferencias
        </h2>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Stores */}
        <section>
          <p className="text-xs font-medium text-slate-500 mb-2">Tiendas</p>
          <div className="grid grid-cols-2 gap-2">
            {ALL_STORES.map((store) => (
              <label key={store} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.preferred_stores.includes(store)}
                  onChange={() => toggleStore(store)}
                  className="accent-indigo-600"
                />
                <span className="text-sm text-slate-700">{STORE_LABELS[store]}</span>
              </label>
            ))}
          </div>
        </section>

        {/* Price priority */}
        <section>
          <label className="text-xs font-medium text-slate-500 block mb-1">
            Prioridad precio
          </label>
          <select
            value={preferences.price_priority}
            onChange={(e) =>
              onChange({ ...preferences, price_priority: e.target.value as Priority })
            }
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
            ))}
          </select>
        </section>

        {/* Brand priority */}
        <section>
          <label className="text-xs font-medium text-slate-500 block mb-1">
            Prioridad marca
          </label>
          <select
            value={preferences.brand_priority}
            onChange={(e) =>
              onChange({ ...preferences, brand_priority: e.target.value as Priority })
            }
            className="w-full text-sm border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400"
          >
            {PRIORITIES.map((p) => (
              <option key={p} value={p}>{PRIORITY_LABELS[p]}</option>
            ))}
          </select>
        </section>

        {/* Toggles */}
        <section className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.allow_substitutions}
              onChange={(e) =>
                onChange({ ...preferences, allow_substitutions: e.target.checked })
              }
              className="accent-indigo-600"
            />
            <span className="text-sm text-slate-700">Permitir sustituciones</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.known_brands_only}
              onChange={(e) =>
                onChange({ ...preferences, known_brands_only: e.target.checked })
              }
              className="accent-indigo-600"
            />
            <span className="text-sm text-slate-700">Solo marcas conocidas</span>
          </label>
        </section>

        {/* Max candidates */}
        <section>
          <label className="text-xs font-medium text-slate-500 block mb-1">
            Candidatos por producto: {preferences.max_candidates_per_product}
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={preferences.max_candidates_per_product}
            onChange={(e) =>
              onChange({
                ...preferences,
                max_candidates_per_product: Number(e.target.value),
              })
            }
            className="w-full accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-0.5">
            <span>1</span><span>10</span>
          </div>
        </section>
      </div>

      {/* Save button */}
      <div className="p-4 border-t border-slate-200">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full text-sm font-medium bg-indigo-600 text-white rounded-lg py-2 hover:bg-indigo-700 disabled:opacity-60 transition-colors"
        >
          {saving ? "Guardando…" : saved ? "✓ Guardado" : "Guardar"}
        </button>
      </div>
    </aside>
  );
}
