import type { ChatResponse, UserPreferences } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  app: string;
  environment: string;
  llm_provider: string;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function postChat(message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Error ${res.status}`);
  }
  return res.json();
}

export async function getPreferences(): Promise<UserPreferences> {
  const res = await fetch(`${API_BASE_URL}/api/preferences`);
  if (!res.ok) throw new Error(`Failed to load preferences: ${res.status}`);
  return res.json();
}

export async function savePreferences(prefs: UserPreferences): Promise<UserPreferences> {
  const res = await fetch(`${API_BASE_URL}/api/preferences`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prefs),
  });
  if (!res.ok) throw new Error(`Failed to save preferences: ${res.status}`);
  return res.json();
}
