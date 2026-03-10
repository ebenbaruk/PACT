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
