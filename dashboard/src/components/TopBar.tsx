interface Props {
  isLive: boolean;
}

export default function TopBar({ isLive }: Props) {
  return (
    <header className="topbar">
      <div className="topbar__brand">PACT</div>
      <div className="topbar__right">
        <span className="topbar__version">v0.1.0</span>
        <span>
          <span
            className={`status-dot ${isLive ? "status-dot--live" : ""}`}
          />{" "}
          {isLive ? "LIVE" : "OFFLINE"}
        </span>
      </div>
    </header>
  );
}
