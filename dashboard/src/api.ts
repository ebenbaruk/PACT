import type { Agent, Bond, ActivityEvent, Stats } from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const fetchAgents = () => get<Agent[]>("/agents");
export const fetchBonds = () => get<Bond[]>("/bonds");
export const fetchActivity = () => get<ActivityEvent[]>("/activity");
export const fetchStats = () => get<Stats>("/stats");
export const fetchTrust = (id: string) =>
  get<{ agent_id: string; trust_score: number }>(`/agents/${id}/trust`);
