interface Props {
  loading: boolean;
  done: boolean;
  stepIdx: number;
  totalSteps: number;
  caption: string;
  isPunchline: boolean;
  onNext: () => void;
  onPrev: () => void;
  onRestart: () => void;
  canPrev: boolean;
}

export default function DemoControls({
  loading,
  done,
  stepIdx,
  totalSteps,
  caption,
  isPunchline,
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
