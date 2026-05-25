export interface Agent {
  id: string;
  domain: string;
  name: string;
  public_key: string;
  capabilities: string[];
  verified: boolean;
  created_at: string;
  trust_score?: number;
}

export interface Bond {
  id: string;
  proposer_id: string;
  accepter_id: string;
  terms: Record<string, string>;
  status: string;
  created_at: string;
}

export interface ActivityEvent {
  idx: number;
  type: string;
  source_id: string;
  source_name: string;
  target_id: string;
  target_name: string;
  status: string;
  detail: string;
  timestamp: string;
}

export interface Stats {
  agent_count: number;
  bond_count: number;
  avg_trust: number;
}

/* ── Guided demo ─────────────────────────────────────────────────────────── */

export interface TraceEvent {
  kind: "thinking" | "tool_call" | "tool_result" | "final";
  text?: string;
  tool?: string;
  args?: Record<string, unknown>;
  ok?: boolean;
  result?: unknown;
}

export interface AgentMessage {
  from_name: string;
  to_name: string;
  kind: string;
  summary: string;
  payload?: Record<string, unknown>;
}

export interface StepAgent {
  key: string;
  name: string;
  icon: string;
}

export interface StepTrace {
  step_id: number;
  phase: string;
  narration_fr: string;
  agent: StepAgent;
  events: TraceEvent[];
  messages: AgentMessage[];
  final_text: string;
  source: "ai" | "fallback" | "scripted";
  step_idx: number;
  total_steps: number;
  done: boolean;
}

export interface DemoMeta {
  id: string;
  num: number;
  title: string;
  tagline: string;
  problem: string;
  punchline: string;
}

export interface ScenarioAgent {
  key: string;
  name: string;
  domain: string;
  icon: string;
}

export interface ScenarioOutline {
  scenario: DemoMeta;
  steps: { id: number; narration_fr: string }[];
  agents: ScenarioAgent[];
  total_steps: number;
  ai_enabled: boolean;
}
