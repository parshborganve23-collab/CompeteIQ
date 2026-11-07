/**
 * Unified Workflows page — history list + detail drill-in.
 *
 * Every row is one real cross-platform workflow run: the CompeteIQ event,
 * the shared BAND room reference, the Hindsight memory references and the
 * stored recommendation all live under the same workflow ID.
 */
import { useEffect, useState } from "react";
import { Activity, ChevronRight, Network, RefreshCw } from "lucide-react";
import { workflowsApi } from "../services/api";
import UnifiedWorkflowDetail from "./UnifiedWorkflowDetail";
import "./UnifiedWorkflows.css";

const STATUS_CLASS = {
  completed: "wf-ok",
  dispatched: "wf-run",
  partial: "wf-warn",
  "awaiting-agent-replies": "wf-warn",
  failed: "wf-bad",
};

export default function UnifiedWorkflowsPage() {
  const [workflows, setWorkflows] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await workflowsApi.list();
      setWorkflows(data.workflows || []);
    } catch (e) {
      setError(e.message || "Failed to load workflow history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (selected) {
    return <UnifiedWorkflowDetail workflowId={selected} onBack={() => { setSelected(null); load(); }} />;
  }

  return (
    <div className="band-page" style={{ padding: "24px 28px", overflow: "auto", height: "100vh" }}>
      <div className="wf-list-page">
        <header className="uwd-header">
          <div>
            <div className="band-eyebrow">CROSS-PLATFORM SYNCHRONIZATION</div>
            <h2 style={{ margin: "2px 0 6px" }}>Unified workflows</h2>
            <p style={{ fontSize: 12.5, opacity: 0.6, margin: 0, maxWidth: 640 }}>
              Each workflow ties one CompeteIQ intelligence event to its shared BAND
              collaboration room, the seven real agent messages, the Hindsight
              memory references and the final strategic recommendation — under the
              same workflow ID in all three systems.
            </p>
          </div>
          <button className="band-btn ghost" onClick={load}><RefreshCw size={15} /> Refresh</button>
        </header>

        {error && <div className="wf-error">{error}</div>}

        {loading ? (
          <div className="uwd-loading"><Activity size={20} className="wf-spin" /> Loading workflow history…</div>
        ) : workflows.length === 0 ? (
          <div className="wf-section">
            <div className="wf-empty">
              No unified workflows yet. Run one from the BAND AI page
              ("Run unified BAND + Hindsight workflow" on a connected event) to create the first run.
            </div>
          </div>
        ) : (
          <div className="wf-section">
            <table className="wf-history-table">
              <thead>
                <tr>
                  <th>Workflow ID</th>
                  <th>Event</th>
                  <th>Status</th>
                  <th>BAND room</th>
                  <th>Hindsight</th>
                  <th>Started</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((w) => (
                  <tr key={w.workflow_id} className="wf-history-row" onClick={() => setSelected(w.workflow_id)}>
                    <td><code className="wf-mono">{w.workflow_id.slice(0, 8)}…</code></td>
                    <td>
                      <strong>{w.event_title || w.event_id}</strong>
                      <div className="wf-meta">{w.event_company}{w.event_category ? ` · ${w.event_category}` : ""}</div>
                    </td>
                    <td><span className={`wf-badge ${STATUS_CLASS[w.status] || ""}`}>{w.status}</span></td>
                    <td>
                      {w.band_room_id ? (
                        <code className="wf-mono">{w.band_room_id.slice(0, 8)}…</code>
                      ) : (
                        <span className="wf-muted">none</span>
                      )}
                    </td>
                    <td>
                      {w.hindsight_retained_at
                        ? <span className="wf-badge wf-ok">retained</span>
                        : <span>{w.hindsight_recall_count || 0} recalled</span>}
                    </td>
                    <td className="wf-meta">{w.started_at ? new Date(w.started_at).toLocaleString() : "—"}</td>
                    <td><ChevronRight size={14} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
