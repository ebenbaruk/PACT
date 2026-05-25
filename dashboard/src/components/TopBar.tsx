import DemoTabs from "./DemoTabs";
import type { DemoMeta } from "../types";

interface Props {
  isLive: boolean;
  demos: DemoMeta[];
  current: string | null;
  onSelect: (id: string) => void;
}

export default function TopBar({ isLive, demos, current, onSelect }: Props) {
  return (
    <header className="topbar">
      <div className="topbar__brand">PACT</div>
      <DemoTabs demos={demos} current={current} onSelect={onSelect} />
      <div className="topbar__right">
        <span className="topbar__version">v0.1.0</span>
        <span>
          <span className={`status-dot ${isLive ? "status-dot--live" : ""}`} />{" "}
          {isLive ? "LIVE" : "OFFLINE"}
        </span>
      </div>
    </header>
  );
}
