import { useMemo } from "react";
import type { Agent, Bond } from "../types";

interface Props {
  agents: Agent[];
  bonds: Bond[];
}

export default function TrustNetwork({ agents, bonds }: Props) {
  const activeBonds = bonds.filter((b) => b.status === "active");

  const layout = useMemo(() => {
    const n = agents.length;
    if (n === 0) return [];
    const cx = 50;
    const cy = 50;
    const rx = 36;
    const ry = 36;
    const offset = -Math.PI / 2;
    return agents.map((agent, i) => {
      const angle = offset + (2 * Math.PI * i) / n;
      return {
        agent,
        x: cx + rx * Math.cos(angle),
        y: cy + ry * Math.sin(angle),
      };
    });
  }, [agents]);

  const posMap = useMemo(
    () => new Map(layout.map((l) => [l.agent.id, { x: l.x, y: l.y }])),
    [layout],
  );

  const keyHash = (key: string) =>
    key.length >= 8 ? `${key.slice(0, 4)}...${key.slice(-4)}` : key;

  if (agents.length === 0) {
    return <div className="empty-state">No agents registered yet.</div>;
  }

  return (
    <div className="trust-network">
      {/* SVG bond lines (lines only, no text) */}
      <svg className="bond-layer" viewBox="0 0 100 100" preserveAspectRatio="none">
        {activeBonds.map((bond) => {
          const p1 = posMap.get(bond.proposer_id);
          const p2 = posMap.get(bond.accepter_id);
          if (!p1 || !p2) return null;
          return (
            <line
              key={bond.id}
              className="bond-line"
              x1={p1.x}
              y1={p1.y}
              x2={p2.x}
              y2={p2.y}
              vectorEffect="non-scaling-stroke"
            />
          );
        })}
      </svg>

      {/* Bond labels as HTML (so font-size is in px, not SVG units) */}
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
            className="bond-label-html"
            style={{ left: `${mx}%`, top: `${my}%` }}
          >
            {service}
          </span>
        );
      })}

      {/* Agent nodes */}
      {layout.map(({ agent, x, y }) => (
        <div
          key={agent.id}
          className="node"
          style={{
            left: `${x}%`,
            top: `${y}%`,
            transform: "translate(-50%, -50%)",
          }}
        >
          <div className="node-inner">
            <div className="node__name">{agent.name}</div>
            <div className="node__domain">{agent.domain}</div>
            <div className="node__key">{keyHash(agent.public_key)}</div>
            <div className="node__trust">
              {agent.trust_score != null
                ? `Trust: ${agent.trust_score.toFixed(3)}`
                : "Trust: —"}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
