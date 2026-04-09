import type { Agent, Case, CaseEvent, DashboardSummary, JinyiweiBoard, ModelRuntimeCapabilities } from "../types";

declare global {
  interface Window {
    REGENTOS_CONFIG?: {
      apiBase?: string;
    };
  }
}

const fallbackBase = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
export const apiBase = window.REGENTOS_CONFIG?.apiBase ?? fallbackBase;

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    throw new Error(`${path} -> ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return fetchJson<DashboardSummary>("/api/dashboard/summary");
}

export async function getJinyiweiBoard(): Promise<JinyiweiBoard> {
  return fetchJson<JinyiweiBoard>("/api/dashboard/jinyiwei-board");
}

export async function getCases(): Promise<Case[]> {
  const payload = await fetchJson<{ items: Case[] }>("/api/cases");
  return payload.items;
}

export async function getCase(caseId: string): Promise<Case> {
  return fetchJson<Case>(`/api/cases/${caseId}`);
}

export async function getTimeline(caseId: string): Promise<CaseEvent[]> {
  const payload = await fetchJson<{ case_id: string; timeline: CaseEvent[] }>(
    `/api/cases/${caseId}/timeline`,
  );
  return payload.timeline;
}

export async function getAgents(): Promise<Agent[]> {
  const payload = await fetchJson<{ items: Agent[] }>("/api/agents");
  return payload.items;
}

export async function getModelCapabilities(): Promise<ModelRuntimeCapabilities> {
  return fetchJson<ModelRuntimeCapabilities>("/api/models/runtime-capabilities");
}
