import { useState } from "react";
import type { ActivityEvent } from "../types";

interface Props {
  events: ActivityEvent[];
}

export default function ActivityLog({ events }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const toggle = (idx: number) =>
    setExpandedIdx((prev) => (prev === idx ? null : idx));

  return (
    <div>
      {events.length === 0 ? (
        <div className="empty-state">Waiting for activity...</div>
      ) : (
        <table className="activity-table">
          <thead>
            <tr>
              <th>#</th>
              <th>SOURCE</th>
              <th>TARGET</th>
              <th>METHOD</th>
              <th>STATUS</th>
              <th>TIME</th>
            </tr>
          </thead>
          <tbody>
            {[...events].reverse().map((e) => (
              <>
                <tr
                  key={e.idx}
                  className={`activity-row ${expandedIdx === e.idx ? "activity-row--active" : ""}`}
                  onClick={() => toggle(e.idx)}
                >
                  <td>{e.idx}</td>
                  <td>{e.source_name || e.source_id}</td>
                  <td>{e.target_name || e.target_id || "—"}</td>
                  <td>{e.type}</td>
                  <td>{e.status}</td>
                  <td>{e.timestamp.slice(11, 19)}</td>
                </tr>
                {expandedIdx === e.idx && e.detail && (
                  <tr key={`${e.idx}-detail`} className="activity-detail-row">
                    <td colSpan={6}>
                      <div className="activity-detail">{e.detail}</div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
