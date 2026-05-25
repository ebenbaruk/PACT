import { useMemo, useEffect, useRef, useState } from "react";
import type { Agent, Bond, StepTrace } from "../types";

interface Props {
  agents: Agent[];
  bonds: Bond[];
  activeTrace: StepTrace | null;
  agentIcons: Record<string, string>;
}

export default function TrustNetwork({ agents, bonds, activeTrace, agentIcons }: Props) {
  const activeBonds = bonds.filter((b) => b.status === "active");

  const layout = useMemo(() => {
    const n = agents.length;
    if (n === 0) return [];
    const cx = 50;
    const cy = 50;
    const r = 34;
    const offset = -Math.PI / 2;
    return agents.map((agent, i) => {
      const angle = offset + (2 * Math.PI * i) / n;
      return { agent, x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
    });
  }, [agents]);

  const posMap = useMemo(
    () => new Map(layout.map((l) => [l.agent.id, { x: l.x, y: l.y }])),
    [layout],
  );
  const nameToId = useMemo(
    () => new Map(agents.map((a) => [a.name, a.id])),
    [agents],
  );

  const keyHash = (key: string) =>
    key.length >= 8 ? `${key.slice(0, 4)}…${key.slice(-4)}` : key;

  // ── Reactive cues driven by the latest step ─────────────────────────────────
  const activeName = activeTrace && activeTrace.agent.key !== "system" ? activeTrace.agent.name : null;
  const activeId = activeName ? nameToId.get(activeName) : undefined;

  // Intent broadcast → ripple from the broadcasting node (re-keyed per step).
  const broadcast = activeTrace?.messages.find((m) => m.kind === "intent_broadcast");
  const ripplePos = broadcast && activeId ? posMap.get(activeId) : undefined;

  // Web-of-trust query → highlight the referral path (querier → referrer → recommended).
  const pathBondIds = useMemo(() => {
    const ids = new Set<string>();
    const netMsg = activeTrace?.messages.find((m) => m.kind === "network_query");
    if (!netMsg || !activeId) return ids;
    const recs = (netMsg.payload?.recommendations as Array<{ agent_id?: string; referred_by?: string }>) ?? [];
    const between = (a?: string, b?: string) =>
      activeBonds.find(
        (bd) =>
          (bd.proposer_id === a && bd.accepter_id === b) ||
          (bd.proposer_id === b && bd.accepter_id === a),
      );
    for (const rec of recs) {
      const e1 = between(activeId, rec.referred_by);
      const e2 = between(rec.referred_by, rec.agent_id);
      if (e1) ids.add(e1.id);
      if (e2) ids.add(e2.id);
    }
    return ids;
  }, [activeTrace, activeId, activeBonds]);

  // Trust score went up → flash the node briefly.
  const prevTrust = useRef<Map<string, number>>(new Map());
  const [flash, setFlash] = useState<Set<string>>(new Set());
  useEffect(() => {
    const inc = new Set<string>();
    for (const a of agents) {
      const prev = prevTrust.current.get(a.id);
      const cur = a.trust_score ?? 0;
      if (prev != null && cur > prev + 0.0001) inc.add(a.id);
      prevTrust.current.set(a.id, cur);
    }
    if (inc.size) {
      setFlash(inc);
      const t = setTimeout(() => setFlash(new Set()), 1300);
      return () => clearTimeout(t);
    }
  }, [agents]);

  if (agents.length === 0) {
    return <div className="empty-state">En attente des agents…</div>;
  }

  return (
    <div className="trust-network">
      <svg className="bond-layer" viewBox="0 0 100 100" preserveAspectRatio="none">
        {activeBonds.map((bond) => {
          const p1 = posMap.get(bond.proposer_id);
          const p2 = posMap.get(bond.accepter_id);
          if (!p1 || !p2) return null;
          return (
            <line
              key={bond.id}
              className={`bond-line ${pathBondIds.has(bond.id) ? "bond-line--path" : ""}`}
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>

      {/* Bond labels */}
      {activeBonds.map((bond) => {
        const p1 = posMap.get(bond.proposer_id);
        const p2 = posMap.get(bond.accepter_id);
        if (!p1 || !p2) return null;
        const service = bond.terms?.service ?? "";
        if (!service) return null;
        const mx = (p1.x + p2.x) / 2;
        const my = (p1.y + p2.y) / 2;
        return (
          <span
            key={`label-${bond.id}`}
            className={`bond-label-html ${pathBondIds.has(bond.id) ? "bond-label--path" : ""}`}
            style={{ left: `${mx}%`, top: `${my}%` }}
          >
            {service}
          </span>
        );
      })}

      {/* Intent broadcast ripple */}
      {ripplePos && (
        <span
          key={`ripple-${activeTrace?.step_id}`}
          className="ripple"
          style={{ left: `${ripplePos.x}%`, top: `${ripplePos.y}%` }}
        />
      )}

      {/* Agent nodes */}
      {layout.map(({ agent, x, y }) => {
        const isActive = activeName === agent.name;
        const isFlash = flash.has(agent.id);
        return (
          <div
            key={agent.id}
            className={`node ${isActive ? "node--active" : ""} ${isFlash ? "node--flash" : ""}`}
            style={{ left: `${x}%`, top: `${y}%`, transform: "translate(-50%, -50%)" }}
          >
            <div className="node-inner">
              <div className="node__head">
                <span className="node__icon">{agentIcons[agent.name] ?? "🏢"}</span>
                <span className="node__name">
                  {agent.name}
                  {agent.verified && <span className="node__check" title="Identité vérifiée"> ✓</span>}
                </span>
              </div>
              <div className="node__domain">{agent.domain}</div>
              <div className="node__key">{keyHash(agent.public_key)}</div>
              <div className="node__trust">
                {agent.trust_score != null ? `Confiance ${agent.trust_score.toFixed(2)}` : "Confiance —"}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
