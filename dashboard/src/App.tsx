import { useCallback, useEffect, useState } from "react";
import { usePolling } from "./hooks/usePolling";
import {
  fetchAgents,
  fetchBonds,
  fetchActivity,
  fetchStats,
  fetchTrust,
  fetchScenarios,
  postDemoReset,
  postDemoStep,
} from "./api";
import type { Agent, Bond, ActivityEvent, Stats, DemoMeta, ScenarioOutline, StepTrace } from "./types";
import TopBar from "./components/TopBar";
import TrustNetwork from "./components/TrustNetwork";
import ActivityLog from "./components/ActivityLog";
import AgentConsole from "./components/AgentConsole";
import DemoControls from "./components/DemoControls";
import DemoMenu from "./components/DemoMenu";

const INTERVAL = 2500;
const emptyStats: Stats = { agent_count: 0, bond_count: 0, avg_trust: 0 };

export default function App() {
  const fetchAgentsWithTrust = useCallback(async (): Promise<Agent[]> => {
    const agentList = await fetchAgents();
    if (agentList.length === 0) return [];
    const scores = await Promise.all(agentList.map((a) => fetchTrust(a.id)));
    return agentList.map((a, i) => ({ ...a, trust_score: scores[i].trust_score }));
  }, []);

  const { data: agents, isLive, refresh: refreshAgents } = usePolling(fetchAgentsWithTrust, INTERVAL, [] as Agent[]);
  const { data: bonds, refresh: refreshBonds } = usePolling(fetchBonds, INTERVAL, [] as Bond[]);
  const { data: activity, refresh: refreshActivity } = usePolling(fetchActivity, INTERVAL, [] as ActivityEvent[]);
  const { data: stats, refresh: refreshStats } = usePolling(fetchStats, INTERVAL, emptyStats);

  const [scenarios, setScenarios] = useState<DemoMeta[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [outline, setOutline] = useState<ScenarioOutline | null>(null);
  const [traces, setTraces] = useState<StepTrace[]>([]);
  const [loading, setLoading] = useState(false);
  const [focusStep, setFocusStep] = useState<number | null>(null);

  useEffect(() => {
    fetchScenarios().then(setScenarios).catch(() => {});
  }, []);

  const refreshAll = useCallback(() => {
    refreshAgents();
    refreshBonds();
    refreshActivity();
    refreshStats();
  }, [refreshAgents, refreshBonds, refreshActivity, refreshStats]);

  const currentTrace = traces.length > 0 ? traces[traces.length - 1] : null;
  const totalSteps = outline?.total_steps ?? 0;
  const stepIdx = currentTrace?.step_idx ?? 0;
  const done = currentTrace?.done ?? false;

  const agentIcons: Record<string, string> = {};
  outline?.agents.forEach((a) => {
    agentIcons[a.name] = a.icon;
  });

  const startDemo = useCallback(async (id: string) => {
    setSelected(id);
    setLoading(true);
    setOutline(null);
    setTraces([]);
    setFocusStep(null);
    try {
      const res = await postDemoReset(id);
      setOutline(res);
      refreshAll();
    } finally {
      setLoading(false);
    }
  }, [refreshAll]);

  const backToMenu = useCallback(() => {
    setSelected(null);
    setOutline(null);
    setTraces([]);
    setFocusStep(null);
  }, []);

  const onNext = useCallback(async () => {
    if (loading || done) return;
    setLoading(true);
    setFocusStep(null);
    try {
      const res = await postDemoStep();
      if ("events" in res) {
        setTraces((prev) => [...prev, res]);
        refreshAll();
      }
    } finally {
      setLoading(false);
    }
  }, [loading, done, refreshAll]);

  const onPrev = useCallback(() => {
    setFocusStep((f) => {
      const cur = f ?? currentTrace?.step_id ?? 1;
      return Math.max(1, cur - 1);
    });
  }, [currentTrace]);

  const canPrev = traces.length > 1 && (focusStep ?? currentTrace?.step_id ?? 1) > 1;

  const caption = !outline
    ? "Chargement…"
    : done
      ? outline.scenario.punchline
      : traces.length === 0
        ? "Prêt. Cliquez sur « Suivant » pour lancer la première étape."
        : currentTrace?.narration_fr ?? "";

  return (
    <div className="app">
      <TopBar isLive={isLive} demos={scenarios} current={selected} onSelect={startDemo} />

      {selected == null || !outline ? (
        <DemoMenu demos={scenarios} onSelect={startDemo} />
      ) : (
        <div className="demo-stage">
          <div className="demo-header">
            <button className="btn btn--ghost" onClick={backToMenu}>← Menu</button>
            <div className="demo-header__text">
              <div className="demo-header__title">
                Mécanisme {outline.scenario.num} — {outline.scenario.title}
              </div>
              <div className="demo-header__problem">{outline.scenario.problem}</div>
            </div>
          </div>

          <DemoControls
            loading={loading}
            done={done}
            stepIdx={stepIdx}
            totalSteps={totalSteps}
            caption={caption}
            isPunchline={done}
            source={currentTrace?.source ?? null}
            onNext={onNext}
            onPrev={onPrev}
            onRestart={() => startDemo(selected)}
            canPrev={canPrev}
          />

          <div className="main-grid">
            <section className="section section--console">
              <span className="rail-label">AI</span>
              <div className="section-title">Conversation des agents</div>
              <AgentConsole traces={traces} loading={loading} focusStep={focusStep} agentIcons={agentIcons} />
            </section>

            <section className="section section--net">
              <span className="rail-label">NET</span>
              <div className="section-title">Réseau de confiance</div>
              <div className="net-stats">
                <div className="stat"><span className="stat__value">{stats.agent_count}</span><span className="stat__label">Agents</span></div>
                <div className="stat"><span className="stat__value">{stats.bond_count}</span><span className="stat__label">Liens</span></div>
                <div className="stat"><span className="stat__value">{stats.avg_trust.toFixed(2)}</span><span className="stat__label">Confiance moy.</span></div>
              </div>
              <div className="net-graph">
                <TrustNetwork agents={agents} bonds={bonds} activeTrace={currentTrace} agentIcons={agentIcons} />
              </div>
              <details className="log-drawer">
                <summary>Journal technique — événements signés ({activity.length})</summary>
                <ActivityLog events={activity} />
              </details>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
