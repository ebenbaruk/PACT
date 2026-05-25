import type { StepTrace } from "../types";

interface Props {
  loading: boolean;
  done: boolean;
  stepIdx: number;
  totalSteps: number;
  caption: string;
  isPunchline: boolean;
  source: StepTrace["source"] | null;
  onNext: () => void;
  onPrev: () => void;
  onRestart: () => void;
  canPrev: boolean;
}

const SOURCE_BADGE: Record<StepTrace["source"], { label: string; cls: string }> = {
  ai: { label: "🧠 Mercury 2", cls: "badge--ai" },
  fallback: { label: "⚠️ secours scripté", cls: "badge--warn" },
  scripted: { label: "scénarisé", cls: "badge--muted" },
};

export default function DemoControls({
  loading,
  done,
  stepIdx,
  totalSteps,
  caption,
  isPunchline,
  source,
  onNext,
  onPrev,
  onRestart,
  canPrev,
}: Props) {
  return (
    <div className="controls">
      <div className="controls__narration">
        <span className={`controls__caption ${isPunchline ? "controls__caption--win" : ""}`}>
          {isPunchline ? "✓ " : ""}
          {caption}
        </span>
        {!isPunchline && source && (
          <span className={`badge ${SOURCE_BADGE[source].cls}`}>{SOURCE_BADGE[source].label}</span>
        )}
      </div>

      <div className="controls__actions">
        <span className="controls__counter">{stepIdx} / {totalSteps}</span>
        <button className="btn btn--ghost" onClick={onRestart} title="Recommencer cette démo">↺</button>
        <button className="btn btn--ghost" onClick={onPrev} disabled={!canPrev} title="Revoir l'étape précédente">◀</button>
        {done ? (
          <span className="controls__done">Terminé ✓</span>
        ) : (
          <button className="btn btn--primary" onClick={onNext} disabled={loading}>
            {loading ? "Mercury 2 réfléchit…" : "Suivant ▶"}
          </button>
        )}
      </div>
    </div>
  );
}
