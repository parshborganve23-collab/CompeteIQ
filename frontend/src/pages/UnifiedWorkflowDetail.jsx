/**
 * UnifiedWorkflowDetail — one workflow across CompeteIQ, BAND and Hindsight.
 *
 * Shows the real BAND room reference and transcript, actual agent messages
 * with timestamps, Hindsight recall/reflect/retain references and the stored
 * final recommendation. Platform tool events are labelled as such and are
 * never confused with agent analysis responses.
 */
import { useEffect, useState } from "react";
import {
  Activity, CheckCircle2, ChevronRight, Database, Link2, RefreshCw,
  ShieldAlert, Network, Clock,
} from "lucide-react";
import { workflowsApi } from "../services/api";
import "./UnifiedWorkflows.css";

const STATUS_CLASS = {
  completed: "wf-ok",
  dispatched: "wf-run",
  pending: "wf-run",
  partial: "wf-warn",
  "awaiting-agent-replies": "wf-warn",
  failed: "wf-bad",
  sent: "wf-ok",
  ok: "wf-ok",
  skipped: "wf-warn",
};

export default function UnifiedWorkflowDetail({ workflowId, onBack }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [finalizing, setFinalizing] = useState(false);
  const [feedback, setFeedback] = useState("");

  const load = async (sync = true) => {
    setLoading(true);
    setError(null);
    try {
      const d = await workflowsApi.detail(workflowId, sync);
      setData(d);
    } catch (e) {
      setError(e.message || "Failed to load workflow detail.");
    } finally {
      setLoading(false);
    }
  };

  const finalize = async () => {
    setFinalizing(true);
    setError(null);
    try {
      await workflowsApi.finalize(workflowId, feedback);
      await load(true);
    } catch (e) {
      setError(e.message || "Finalize failed.");
    } finally {
      setFinalizing(false);
    }
  };

  useEffect(() => {
    load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  if (loading) {
    return (
      <div className="uwd-page">
        <div className="uwd-loading"><Activity size={20} className="wf-spin" /> Loading unified workflow…</div>
      </div>
    );
  }
  if (!data) {
    return <div className="uwd-page"><div className="wf-error">{error || "Workflow not found."}</div>{onBack && <button className="wf-btn" onClick={onBack}>Back</button>}</div>;
  }

  const room = data.band_room || { room_id: "", participants: [], messages: [] };
  const hindsight = data.hindsight || {};
  const rec = data.recommendation;
  const agentMessages = data.agent_messages || [];
  const textRoomMessages = (room.messages || []).filter((m) => m.message_type === "text");
  const toolEvents = (room.messages || []).filter((m) => m.message_type !== "text");

  return (
    <div className="uwd-page">
      <header className="uwd-header">
        <div>
          <div className="band-eyebrow">UNIFIED WORKFLOW</div>
          <h2 style={{ margin: "4px 0" }}><code className="wf-mono">{data.workflow_id}</code></h2>
          <span className={`wf-badge ${STATUS_CLASS[data.status] || ""}`}>{data.status}</span>
          <span className="wf-meta">started {data.started_at ? new Date(data.started_at).toLocaleString() : "—"} {data.completed_at && `· completed ${new Date(data.completed_at).toLocaleString()}`}</span>
        </div>
        <div className="wf-actions">
          <button className="band-btn ghost" onClick={() => load(true)}><RefreshCw size={15} /> Sync room</button>
          {onBack && <button className="band-btn ghost" onClick={onBack}><ChevronRight size={15} style={{ transform: "rotate(180deg)" }} /> Back</button>}
        </div>
      </header>

      {error && <div className="wf-error">{error}</div>}
      {data.error && <div className="wf-warn-box">Last recorded error: {data.error}</div>}

      {/* ---- Intelligence event ---- */}
      {data.event && (
        <section className="wf-section">
          <h3><ShieldAlert size={15} /> Intelligence event</h3>
          <div className="wf-kv"><span>Event ID</span><code className="wf-mono">{data.event.id}</code></div>
          <div className="wf-kv"><span>Headline</span><strong>{data.event.title}</strong></div>
          <div className="wf-kv"><span>Competitor</span>{data.event.company}</div>
          <div className="wf-kv"><span>Category</span>{data.event.category}</div>
          <div className="wf-kv"><span>Published</span>{data.event.publication_date || "—"}</div>
          {data.event.source_url && (
            <div className="wf-kv"><span>Source</span>
              <a href={data.event.source_url} target="_blank" rel="noreferrer" className="wf-link"><Link2 size={12} /> {data.event.source_url}</a>
            </div>
          )}
          {data.event.evidence_snippet && <div className="wf-kv"><span>Evidence</span>{data.event.evidence_snippet}</div>}
        </section>
      )}

      {/* ---- BAND room ---- */}
      <section className="wf-section">
        <h3><Network size={15} /> BAND collaboration room (real reference)</h3>
        <div className="wf-kv"><span>Room ID</span><code className="wf-mono">{room.room_id || "—"}</code></div>
        {room.room_title && <div className="wf-kv"><span>Room name</span>{room.room_title}</div>}
        <div className="wf-kv"><span>Open room</span><span className="wf-muted">Band's Agent API does not expose web room URLs — open app.band.ai &amp; search room ID <code className="wf-mono">{room.room_id}</code></span></div>
        <div className="wf-kv">
          <span>Participants ({(room.participants || []).length})</span>
          <span>{(room.participants || []).map((p) => p.name || p.handle).join(", ") || "—"}</span>
        </div>
        <div className="wf-kv"><span>Messages in room</span>{(room.messages || []).length} real messages ({textRoomMessages.length} text · {toolEvents.length} platform tool/system events)</div>
      </section>

      {/* ---- Agent messages + handoff timeline ---- */}
      <section className="wf-section">
        <h3><Clock size={15} /> Agent messages &amp; handoff timeline</h3>
        <div className="wf-msg-list">
          {agentMessages.length === 0 && <div className="wf-empty">No messages recorded yet.</div>}
          {agentMessages.map((m) => (
            <div key={m.id} className="wf-msg-row">
              <div className="wf-msg-head">
                <span className="wf-msg-agent">{m.agent_name}</span>
                <span className={`wf-badge ${STATUS_CLASS[m.status] || ""}`}>{m.status}</span>
                <span className={`wf-badge ${m.direction === "agent_reply" ? "wf-type-reply" : m.direction === "event_publish" ? "wf-type-publish" : "wf-type-dispatch"}`}>{m.direction}</span>
              </div>
              <div className="wf-msg-content">{m.direction === "agent_reply" ? m.output : m.message}</div>
              <div className="wf-msg-meta">
                {m.band_message_id && <>BAND message <code className="wf-mono">{m.band_message_id}</code> · </>}
                {m.sender_name && <>sent by {m.sender_name} · </>}
                {m.band_sent_at ? new Date(m.band_sent_at).toLocaleString() : new Date(m.timestamp).toLocaleString()}
                {m.handoff_to && <> · handoff → {m.handoff_to}</>}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ---- Hindsight ---- */}
      <section className="wf-section">
        <h3><Database size={15} /> Hindsight memory references (bank {hindsight.bank_id || "competeiq-intelligence"})</h3>
        <div className="wf-kv"><span>Integration</span>{hindsight.available ? "Available (real API)" : "Unavailable"}</div>
        <div className="wf-kv"><span>Recall</span>{hindsight.recall_count || 0} memories retrieved before this workflow</div>
        {(hindsight.recall_refs || []).length > 0 && (
          <div className="wf-refs">
            {hindsight.recall_refs.map((r) => (
              <div key={r.id} className="wf-ref"><code className="wf-mono">{r.id}</code> — {(r.content || "").slice(0, 140)}{r.score != null && <em> (score {r.score})</em>}</div>
            ))}
          </div>
        )}
        <div className="wf-kv"><span>Reflect synthesis</span>
          <div className="wf-reflect">{hindsight.reflection || <em className="wf-muted">No reflect synthesis recorded for this workflow.</em>}</div>
        </div>
        <div className="wf-kv">
          <span>Retained</span>
          {hindsight.retained_at
            ? <>Yes — {new Date(hindsight.retained_at).toLocaleString()} (real Hindsight retain; refs: <code className="wf-mono">{JSON.stringify(hindsight.retained_refs)}</code>)</>
            : "Not yet retained (happens at finalize, once actual agent findings exist)"}
        </div>
      </section>

      {/* ---- Final recommendation ---- */}
      <section className="wf-section">
        <h3><CheckCircle2 size={15} /> Final strategic recommendation (stored in CompeteIQ)</h3>
        {rec?.recommended_strategy ? (
          <div className="wf-recommendation">{rec.recommended_strategy}</div>
        ) : (
          <div className="wf-empty">No final recommendation yet — the Strategy Agent's real reply has not been collected. Run band_worker.py, then finalize.</div>
        )}
        {rec && <div className="wf-kv"><span>Recommendation ID</span><code className="wf-mono">{rec.id}</code></div>}
        {rec && <div className="wf-kv"><span>Status</span>{rec.status} · confidence {rec.confidence_score}</div>}
      </section>

      {/* ---- Pipeline stages ---- */}
      <section className="wf-section">
        <h3><Activity size={15} /> Pipeline stage results (real)</h3>
        <div className="wf-stages">
          {(data.stages || []).map((s, i) => (
            <div key={i} className="wf-stage">
              <span className={`wf-badge ${STATUS_CLASS[s.status] || ""}`}>{s.status}</span>
              <strong>{s.stage}</strong>
              <span className="wf-stage-detail">{s.detail || s.error || ""}</span>
              <span className="wf-meta">{s.at ? new Date(s.at).toLocaleTimeString() : ""}</span>
            </div>
          ))}
          {(data.stages || []).length === 0 && <div className="wf-empty">No stages recorded.</div>}
        </div>
      </section>

      {/* ---- Finalize ---- */}
      {!data.stages?.some((s) => s.stage === "final_recommendation" && s.status === "ok") && (
        <section className="wf-section wf-finalize">
          <h3>Collect agent responses &amp; finalize (Hindsight retain + final rec)</h3>
          <p>Pulls the actual agent replies out of the BAND room, stores the Strategy Agent's reply as the final recommendation (when it exists), retains the completed experience in Hindsight and publishes the completion summary back to the room.</p>
          <input
            className="wf-input"
            placeholder="Optional user feedback / outcome to retain with the experience…"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
          <button className="band-btn" onClick={finalize} disabled={finalizing}>
            {finalizing ? <Activity size={15} className="wf-spin" /> : <RefreshCw size={15} />}
            {finalizing ? "Finalizing…" : "Sync & finalize workflow"}
          </button>
        </section>
      )}
    </div>
  );
}
