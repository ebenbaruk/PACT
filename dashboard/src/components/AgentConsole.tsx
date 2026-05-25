import { useEffect, useRef } from "react";
import type { StepTrace, TraceEvent, AgentMessage } from "../types";

interface Props {
  traces: StepTrace[];
  loading: boolean;
  focusStep: number | null;
  agentIcons: Record<string, string>;
}

const MSG_LABELS: Record<string, string> = {
  bond_proposal: "Proposition de bond",
  bond_accept: "Bond accepté & signé",
  intent_broadcast: "Diffusion d'intention",
  intent_response: "Réponse à l'intention",
  network_query: "Requête — réseau de confiance",
  booking_request: "Demande de réservation",
  booking_confirmation: "Confirmation",
  decision: "Décision",
};

function shorten(value: unknown, max = 90): string {
  const s = typeof value === "string" ? value : JSON.stringify(value);
  if (!s) return "";
  return s.length > max ? s.slice(0, max - 1) + "…" : s;
}

function MessageBubble({ msg, icons }: { msg: AgentMessage; icons: Record<string, string> }) {
  const fromIcon = icons[msg.from_name] ?? "🤖";
  const toIcon = icons[msg.to_name] ?? (msg.to_name === "réseau" || msg.to_name.startsWith("réseau") ? "📡" : "🤖");
  return (
    <div className={`msg msg--${msg.kind}`}>
      <div className="msg__route">
        <span className="msg__who">{fromIcon} {msg.from_name}</span>
        <span className="msg__arrow">→</span>
        <span className="msg__who">{toIcon} {msg.to_name}</span>
        <span className="msg__kind">{MSG_LABELS[msg.kind] ?? msg.kind}</span>
      </div>
      <div className="msg__summary">{msg.summary}</div>
    </div>
  );
}

function StepCard({
  trace,
  icons,
  cardRef,
}: {
  trace: StepTrace;
  icons: Record<string, string>;
  cardRef: (el: HTMLDivElement | null) => void;
}) {
  const thinking = trace.events.filter((e: TraceEvent) => e.kind === "thinking" && e.text);
  const toolCalls = trace.events.filter((e: TraceEvent) => e.kind === "tool_call");

  return (
    <div className="step-card" ref={cardRef}>
      <div className="step-card__head">
        <span className="step-card__agent">{trace.agent.icon} {trace.agent.name}</span>
        <span className="step-card__step">Étape {trace.step_id}</span>
        <span className={`badge ${trace.source === "ai" ? "badge--ai" : trace.source === "fallback" ? "badge--warn" : "badge--muted"}`}>
          {trace.source === "ai" ? "🧠 IA" : trace.source === "fallback" ? "⚠️" : "scénarisé"}
        </span>
      </div>

      <div className="step-card__narration">{trace.narration_fr}</div>

      {thinking.map((e, i) => (
        <div key={`t-${i}`} className="thought">
          <span className="thought__icon">💭</span>
          <span className="thought__text">{e.text}</span>
        </div>
      ))}

      {trace.messages.map((m, i) => (
        <MessageBubble key={`m-${i}`} msg={m} icons={icons} />
      ))}

      {trace.final_text && (
        <div className="step-card__final">
          <span className="step-card__final-icon">{trace.agent.icon}</span>
          <span>« {trace.final_text} »</span>
        </div>
      )}

      {toolCalls.length > 0 && (
        <details className="tool-details">
          <summary>{toolCalls.length} appel(s) au protocole — détails techniques</summary>
          {trace.events.map((e, i) => {
            if (e.kind === "tool_call") {
              return (
                <div key={i} className="tool-line tool-line--call">
                  ⚡ {e.tool}({shorten(e.args, 70)})
                </div>
              );
            }
            if (e.kind === "tool_result") {
              return (
                <div key={i} className={`tool-line tool-line--result ${e.ok ? "" : "tool-line--err"}`}>
                  {e.ok ? "←" : "✗"} {shorten(e.result, 80)}
                </div>
              );
            }
            return null;
          })}
        </details>
      )}
    </div>
  );
}

export default function AgentConsole({ traces, loading, focusStep, agentIcons }: Props) {
  const cards = useRef<Map<number, HTMLDivElement>>(new Map());
  const endRef = useRef<HTMLDivElement | null>(null);

  // Scroll to the focused step when replaying, otherwise follow the latest.
  useEffect(() => {
    if (focusStep != null && cards.current.has(focusStep)) {
      cards.current.get(focusStep)?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [traces.length, focusStep, loading]);

  if (traces.length === 0 && !loading) {
    return (
      <div className="empty-state">
        Cliquez sur « Suivant » pour lancer la première étape — vous verrez ce que chaque
        agent pense, décide, et envoie aux autres.
      </div>
    );
  }

  return (
    <div className="agent-console">
      {traces.map((trace) => (
        <StepCard
          key={trace.step_id}
          trace={trace}
          icons={agentIcons}
          cardRef={(el) => {
            if (el) cards.current.set(trace.step_id, el);
            else cards.current.delete(trace.step_id);
          }}
        />
      ))}
      {loading && (
        <div className="step-card step-card--loading">
          <span className="thought__icon">💭</span> Mercury 2 réfléchit
          <span className="dots"><span>.</span><span>.</span><span>.</span></span>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
