/**
 * Hindsight Memory page — real historical learning.
 *
 * Connects to the actual Hindsight agent memory service via the backend API.
 * When Hindsight is not configured, shows a clear disconnected state with setup
 * instructions. Never simulates a successful Hindsight response.
 *
 * NOTE: this file only changes presentation (layout JSX + CSS imports).
 * All data state, effects, API calls and handlers are unchanged.
 */
import { useEffect, useState } from 'react';
import {
  Activity, Clock, Database, Search, AlertTriangle,
  ChevronRight, RefreshCw
} from 'lucide-react';
import { hindsightApi, intelligenceApi } from '../services/api';
import './UnifiedWorkflows.css';
// These two files were previously never imported, which is why the page
// rendered unstyled. CommandCenter.css holds the shared tokens/components.
import './CommandCenter.css';
import './HindsightPage.css';

// Same page size the page always requested from list_memories.
const MEMORY_LIST_LIMIT = 20;
const MEMORY_PREVIEW_CHARS = 240;
const BANK_PREVIEW_COUNT = 8;

// Presentation only: maps a backend status string to a badge tone.
const statusTone = (value) => {
  const v = String(value || '').toLowerCase();
  if (v === 'completed' || v === 'success' || v === 'ok') return 'ok';
  if (v === 'failed' || v === 'error') return 'bad';
  if (v.includes('awaiting')) return 'alt';
  if (v === 'dispatched' || v === 'running') return 'info';
  return 'warn'; // partial and anything unknown: never shown as completed
};

const formatTime = (value) => {
  if (!value) return null;
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    const d = new Date(value);
    if (!Number.isNaN(d.getTime())) return d.toLocaleString();
  }
  return String(value);
};

/** Presentational memory card with expand / collapse for long content. */
function MemoryCard({ memory }) {
  const [expanded, setExpanded] = useState(false);

  const content = memory.content || memory.text || '';
  const id = memory.id || memory.memory_id;
  const type = memory.fact_type || memory.type || memory.memory_type;
  const time = formatTime(
    memory.timestamp ||
      memory.created_at ||
      memory.occurred_at ||
      memory.mentioned_at ||
      memory.date
  );
  const state = memory.state || memory.status;
  const long = content.length > MEMORY_PREVIEW_CHARS;
  const shown =
    long && !expanded
      ? `${content.slice(0, MEMORY_PREVIEW_CHARS).trimEnd()}…`
      : content;

  return (
    <div className="hind-memory-card">
      <div className="hind-memory-top">
        <span className="cc-badge plain">{type || 'memory'}</span>
        {state && <span className="cc-badge info">{state}</span>}
      </div>

      <div className="hind-memory-content">
        {shown || <em>No content returned.</em>}
      </div>

      {long && (
        <div>
          <button
            className="cc-btn link"
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        </div>
      )}

      <div className="hind-memory-meta">
        <div className="hind-memory-meta-row">
          <span>ID</span>
          <code className="cc-mono">{id || '—'}</code>
        </div>

        {memory.bank_id && (
          <div className="hind-memory-meta-row">
            <span>Bank</span>
            <span>{memory.bank_id}</span>
          </div>
        )}

        {time && (
          <div className="hind-memory-meta-row">
            <span>Time</span>
            <span>{time}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function HindsightPage() {
  const [status, setStatus] = useState(null);
  const [memories, setMemories] = useState([]);
  const [memoriesNote, setMemoriesNote] = useState('');
  const [bankMemories, setBankMemories] = useState([]);
  const [bankMemoriesCount, setBankMemoriesCount] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState('');
  // UI-only: whether to show every returned bank memory or just a preview.
  const [showAllBank, setShowAllBank] = useState(false);

  const loadStatus = async () => {
    try {
      const s = await hindsightApi.status();
      setStatus(s);
    } catch {
      setStatus({ configured: false, available: false, reason: 'Backend unreachable', setup_instructions: [] });
    }
  };

  const loadMemories = async () => {
    try {
      const ev = await intelligenceApi.list();
      setEvents(Array.isArray(ev) ? ev : []);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  // Real bank memories from the actual Hindsight API (list_memories).
  const loadBankMemories = async () => {
    try {
      const data = await hindsightApi.memories(MEMORY_LIST_LIMIT);
      setBankMemories(data.memories || []);
      setBankMemoriesCount(data.count);
      setMemoriesNote(data.note || '');
    } catch (e) {
      setMemoriesNote(e.message || 'Listing real bank memories failed.');
    }
  };

  // Historical decision timeline from the CompeteIQ DB (real workflow records).
  const loadHistory = async () => {
    try {
      const data = await hindsightApi.history();
      setTimeline(data.timeline || []);
    } catch {
      setTimeline([]);
    }
  };

  const recall = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await hindsightApi.recall(query);
      setMemories(data.memories || []);
    } catch (e) {
      setError(e.message || 'Recall failed — Hindsight may not be configured.');
    } finally {
      setLoading(false);
    }
  };

  const runWorkflow = async (eventId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await hindsightApi.workflow(eventId);
      setMemories([
        { content: `Recommendation: ${data.recommended_action || 'No recommendation generated.'}`, bank_id: 'hindsight-workflow', id: data.memory_id, timestamp: new Date().toLocaleString() },
      ]);
    } catch (e) {
      setError(e.message || 'Workflow failed — Hindsight may not be configured.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadStatus(); loadMemories(); loadBankMemories(); loadHistory(); }, []);

  // ---- Presentation helpers (no behaviour of their own) ----
  const activate = (handler) => ({
    role: 'button',
    tabIndex: 0,
    onClick: handler,
    onKeyDown: (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handler();
      }
    },
  });

  const renderEventCards = () => (
    <div className="cc-list">
      {events.map((e) => (
        <div
          key={e.id}
          className={`cc-action ${loading ? 'is-busy' : ''}`}
          {...activate(() => runWorkflow(e.id))}
        >
          <div className="cc-action-main">
            <div className="cc-action-title">{e.title}</div>
            <div className="cc-action-meta">
              <span>{e.company}</span>
              <span className="cc-chip">{e.category}</span>
            </div>
          </div>

          <span className="cc-action-cta">
            Run
            <ChevronRight size={14} />
          </span>
        </div>
      ))}
      {events.length === 0 && (
        <div className="cc-empty">No intelligence events available.</div>
      )}
    </div>
  );

  const renderRefreshButton = () => (
    <button className="cc-btn" onClick={loadStatus}>
      <RefreshCw size={15} />
      Refresh status
    </button>
  );

  // Disconnected state
  if (!status || !status.available) {
    return (
      <div className="hind-page">
        <header className="cc-header">
          <div className="cc-header-text">
            <div className="cc-eyebrow">HINDSIGHT MEMORY</div>
            <h1>Historical Learning</h1>
            <p>Retrieve relevant historical competitor events, previous strategies, decisions and outcomes to improve strategic recommendations.</p>
          </div>
          {renderRefreshButton()}
        </header>

        <div className="cc-disconnected">
          <div className="cc-disconnected-icon">
            <Database size={30} />
          </div>
          <h2>Hindsight Memory — Not Connected</h2>
          <p>{status?.reason || 'Hindsight is not configured.'}</p>
          <div className="cc-instructions">
            <h3>Setup instructions</h3>
            <ol>
              {(status?.setup_instructions || []).map((s, i) => <li key={i}>{s}</li>)}
            </ol>
            <p className="cc-note">
              Until Hindsight is configured and tested, no historical memory retrieval or learning is performed.
              CompeteIQ does not simulate successful Hindsight responses.
            </p>
          </div>
        </div>

        <section className="cc-panel">
          <div className="cc-panel-head">
            <div>
              <h2>Available intelligence events (from trending feed)</h2>
              <div className="cc-panel-sub">
                Select an event to run the Hindsight workflow against it (once connected).
              </div>
            </div>
          </div>
          {renderEventCards()}
        </section>

        {error && (
          <div className="cc-error" role="alert">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }

  // Connected state
  const bankId = status.banks?.[0] || 'competeiq-intelligence';
  const visibleBank = showAllBank
    ? bankMemories
    : bankMemories.slice(0, BANK_PREVIEW_COUNT);

  return (
    <div className="hind-page">
      <header className="cc-header">
        <div className="cc-header-text">
          <div className="cc-eyebrow">HINDSIGHT MEMORY</div>
          <h1>Historical Learning</h1>
          <p>Real Hindsight memory retrieval — historical events, strategies, decisions and outcomes.</p>
        </div>
        {renderRefreshButton()}
      </header>

      {/* ---- Connection ---- */}
      <section className="cc-panel" aria-label="Hindsight connection">
        <div className="cc-panel-head">
          <div>
            <h2>
              <Database size={16} />
              Memory connection
            </h2>
            <div className="cc-panel-sub">
              Values reported live by the backend from Hindsight.
            </div>
          </div>
        </div>

        <div className="hind-conn-grid">
          <div className="hind-conn-item">
            <span className="hind-conn-label">Status</span>
            <span className="hind-conn-value">
              <span className="cc-dot ok" />
              Connected to Hindsight
            </span>
          </div>

          <div className="hind-conn-item">
            <span className="hind-conn-label">SDK version</span>
            <span className="hind-conn-value">
              {status.version || '—'}
            </span>
          </div>

          <div className="hind-conn-item">
            <span className="hind-conn-label">Bank ID</span>
            <span className="hind-conn-value">
              <code className="cc-mono">
                {Array.isArray(status.banks) && status.banks.length > 0
                  ? status.banks.join(', ')
                  : bankId}
              </code>
            </span>
          </div>
        </div>

        {status.reason && (
          <div className="hind-conn-reason">{status.reason}</div>
        )}
      </section>

      {/* ---- Statistics ---- */}
      <div className="cc-stats">
        <div className="cc-stat">
          <div className="cc-stat-label">Memory bank</div>
          <div className="cc-stat-value small">
            <code className="cc-mono">{bankId}</code>
          </div>
          <div className="cc-stat-note">Active Hindsight bank</div>
        </div>

        <div className="cc-stat">
          <div className="cc-stat-label">Memories returned</div>
          <div className="cc-stat-value">
            {bankMemoriesCount != null ? bankMemoriesCount : '—'}
          </div>
          <div className="cc-stat-note">
            {bankMemoriesCount != null
              ? `Returned by this list request (limit ${MEMORY_LIST_LIMIT}), not the total bank size.${memoriesNote ? ` ${memoriesNote}` : ''}`
              : `Listing memories failed — ${memoriesNote || 'unknown error (real API failure, not hidden)'}.`}
          </div>
        </div>

        <div className="cc-stat">
          <div className="cc-stat-label">Connection</div>
          <div className="cc-stat-value small">
            <span className="cc-dot ok" />
            Connected
          </div>
          <div className="cc-stat-note">
            {status.reason || 'Reported by Hindsight status API'}
          </div>
        </div>

        <div className="cc-stat">
          <div className="cc-stat-label">Historical workflow records</div>
          <div className="cc-stat-value">{timeline.length}</div>
          <div className="cc-stat-note">
            Unified workflow records in the CompeteIQ database
          </div>
        </div>
      </div>

      {/* ---- Recent memories (real API results) ---- */}
      <section className="cc-panel" aria-label="Recent memories">
        <div className="cc-panel-head">
          <div>
            <h2>
              <Database size={16} />
              Recent memories
            </h2>
            <div className="cc-panel-sub">
              Real results from the Hindsight list_memories API.
            </div>
          </div>
        </div>

        {bankMemories.length > 0 ? (
          <>
            <div className="hind-memory-grid">
              {visibleBank.map((m, i) => (
                <MemoryCard key={m.id || m.memory_id || i} memory={m} />
              ))}
            </div>

            {bankMemories.length > BANK_PREVIEW_COUNT && (
              <div className="hind-more">
                <button
                  className="cc-btn"
                  onClick={() => setShowAllBank((v) => !v)}
                >
                  {showAllBank
                    ? 'Show fewer memories'
                    : `Show all ${bankMemories.length} returned memories`}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="cc-empty">
            {bankMemoriesCount == null
              ? 'No memories could be listed — see the status note above.'
              : 'No memories returned by this request.'}
          </div>
        )}
      </section>

      {/* ---- Historical decision timeline (workflow-specific counts) ---- */}
      {timeline.length > 0 && (
        <section className="cc-panel" aria-label="Historical decision timeline">
          <div className="cc-panel-head">
            <div>
              <h2>
                <Clock size={16} />
                Historical decision timeline ({timeline.length} unified workflow records)
              </h2>
              <div className="cc-panel-sub">
                Workflow-specific counts from the CompeteIQ database — kept separate from the real bank statistics above.
              </div>
            </div>
          </div>

          <ol className="hind-timeline">
            {timeline.map((t) => {
              const tone = statusTone(t.status);
              return (
                <li key={t.workflow_id} className="hind-timeline-item">
                  <span className={`hind-timeline-marker ${tone}`} />

                  <div className="hind-timeline-card">
                    <div className="hind-timeline-head">
                      <div className="hind-timeline-title">
                        {t.event_title || t.event_id}
                        {t.event_company && (
                          <div className="hind-timeline-company">
                            {t.event_company}
                          </div>
                        )}
                      </div>

                      <span className={`cc-badge ${tone}`}>{t.status}</span>
                    </div>

                    <div className="hind-timeline-facts">
                      <div className="hind-fact">
                        <span className="hind-fact-label">Workflow ID</span>
                        <code className="cc-mono">{t.workflow_id}</code>
                      </div>

                      <div className="hind-fact">
                        <span className="hind-fact-label">Recall count</span>
                        <span>{t.recall_count} memories</span>
                      </div>

                      <div className="hind-fact">
                        <span className="hind-fact-label">Retained</span>
                        <span>
                          {t.retained_at
                            ? new Date(t.retained_at).toLocaleString()
                            : 'not retained yet'}
                        </span>
                      </div>
                    </div>

                    {t.retained_refs?.length > 0 && (
                      <div className="hind-fact">
                        <span className="hind-fact-label">Memory references</span>
                        <div className="hind-refs">
                          {t.retained_refs.map((ref, i) => (
                            <code key={i} className="cc-chip cc-mono">
                              {typeof ref === 'string' ? ref : JSON.stringify(ref)}
                            </code>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
        </section>
      )}

      {error && (
        <div className="cc-error" role="alert">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="cc-two-col">
        <section className="cc-panel" aria-label="Recall historical memories">
          <div className="cc-panel-head">
            <div>
              <h2>
                <Search size={16} />
                Recall historical memories
              </h2>
              <div className="cc-panel-sub">
                Search Hindsight memory banks for relevant past events.
              </div>
            </div>
          </div>

          <div className="hind-recall">
            <div className="hind-recall-field">
              <Search size={15} />
              <input
                className="hind-recall-input"
                type="text"
                placeholder="Search memory…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') recall();
                }}
              />
            </div>

            <button
              className="cc-btn primary"
              onClick={recall}
              disabled={loading}
            >
              {loading
                ? <><Activity size={15} className="cc-spin" /> Recalling…</>
                : <><Search size={15} /> Recall</>}
            </button>
          </div>

          <div className="hind-results">
            {loading && memories.length === 0 && (
              <div className="hind-loading">
                <Activity size={16} className="cc-spin" />
                Loading…
              </div>
            )}

            {!loading && memories.length === 0 && (
              <div className="cc-empty">No memories retrieved yet.</div>
            )}

            {memories.map((m, i) => (
              <MemoryCard key={i} memory={m} />
            ))}
          </div>
        </section>

        <section className="cc-panel" aria-label="Run Hindsight workflow">
          <div className="cc-panel-head">
            <div>
              <h2>
                <Activity size={16} />
                Run Hindsight workflow
              </h2>
              <div className="cc-panel-sub">
                Select a trending event to retrieve historical context and generate a strategic recommendation.
              </div>
            </div>
          </div>

          {renderEventCards()}
        </section>
      </div>
    </div>
  );
}