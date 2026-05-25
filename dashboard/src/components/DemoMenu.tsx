import type { DemoMeta } from "../types";

interface Props {
  demos: DemoMeta[];
  onSelect: (id: string) => void;
}

export default function DemoMenu({ demos, onSelect }: Props) {
  return (
    <div className="demo-menu">
      <div className="demo-menu__intro">
        <h1>Un protocole de coordination entre agents IA d'entreprises</h1>
        <p>
          Trois mécanismes, trois mini-démos. Choisissez-en une — à chaque clic, un agent IA
          (Mercury 2) <strong>décide et agit</strong>, et vous voyez le réseau se construire.
        </p>
      </div>
      <div className="demo-menu__cards">
        {demos.map((d) => (
          <button key={d.id} className="demo-card" onClick={() => onSelect(d.id)}>
            <div className="demo-card__num">{d.num}</div>
            <div className="demo-card__title">{d.title}</div>
            <div className="demo-card__tagline">{d.tagline}</div>
            <div className="demo-card__problem">{d.problem}</div>
            <div className="demo-card__cta">Lancer ▶</div>
          </button>
        ))}
      </div>
    </div>
  );
}
