import type { DemoMeta } from "../types";

interface Props {
  demos: DemoMeta[];
  current: string | null;
  onSelect: (id: string) => void;
}

export default function DemoTabs({ demos, current, onSelect }: Props) {
  if (demos.length === 0) return null;
  return (
    <div className="demo-tabs">
      {demos.map((d) => (
        <button
          key={d.id}
          className={`demo-tab ${d.id === current ? "demo-tab--active" : ""}`}
          onClick={() => onSelect(d.id)}
        >
          <span className="demo-tab__num">{d.num}</span>
          <span className="demo-tab__title">{d.title}</span>
        </button>
      ))}
    </div>
  );
}
