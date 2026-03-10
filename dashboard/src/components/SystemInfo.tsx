import type { Stats } from "../types";

interface Props {
  stats: Stats;
}

export default function SystemInfo({ stats }: Props) {
  return (
    <div>
      <div className="sys-headline">
        <span>From Isolated.</span>
        <br />
        To Networked.
      </div>
      <div className="sys-stats">
        <div className="stat">
          <span className="stat__value">{stats.agent_count}</span>
          <span className="stat__label">Agents</span>
        </div>
        <div className="stat">
          <span className="stat__value">{stats.bond_count}</span>
          <span className="stat__label">Bonds</span>
        </div>
        <div className="stat">
          <span className="stat__value">{stats.avg_trust.toFixed(3)}</span>
          <span className="stat__label">Avg Trust</span>
        </div>
      </div>
    </div>
  );
}
