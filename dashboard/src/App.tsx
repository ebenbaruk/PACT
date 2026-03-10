import { useCallback } from "react";
import { usePolling } from "./hooks/usePolling";
import {
  fetchAgents,
  fetchBonds,
  fetchActivity,
  fetchStats,
  fetchTrust,
} from "./api";
import type { Agent, Bond, ActivityEvent, Stats } from "./types";
import TopBar from "./components/TopBar";
import TrustNetwork from "./components/TrustNetwork";
import ActivityLog from "./components/ActivityLog";
import SystemInfo from "./components/SystemInfo";

const INTERVAL = 2500;

const emptyStats: Stats = { agent_count: 0, bond_count: 0, avg_trust: 0 };

export default function App() {
  // Fetch agents + trust scores together every cycle
  const fetchAgentsWithTrust = useCallback(async (): Promise<Agent[]> => {
    const agentList = await fetchAgents();
    if (agentList.length === 0) return [];
    const scores = await Promise.all(agentList.map((a) => fetchTrust(a.id)));
    return agentList.map((a, i) => ({ ...a, trust_score: scores[i].trust_score }));
  }, []);

  const { data: agents, isLive } = usePolling(fetchAgentsWithTrust, INTERVAL, [] as Agent[]);
  const { data: bonds } = usePolling(fetchBonds, INTERVAL, [] as Bond[]);
  const { data: activity } = usePolling(fetchActivity, INTERVAL, [] as ActivityEvent[]);
  const { data: stats } = usePolling(fetchStats, INTERVAL, emptyStats);

  return (
    <div className="app">
      <TopBar isLive={isLive} />
      <div className="main-grid">
        <section className="section section--log">
          <span className="rail-label">LOG</span>
          <div className="section-title">Activity Log</div>
          <ActivityLog events={activity} />
        </section>

        <section className="section section--sys">
          <span className="rail-label">SYS</span>
          <div className="section-title">System</div>
          <SystemInfo stats={stats} />
        </section>

        <section className="section section--net">
          <span className="rail-label">NET</span>
          <div className="section-title">Trust Network</div>
          <TrustNetwork agents={agents} bonds={bonds} />
        </section>
      </div>
    </div>
  );
}
