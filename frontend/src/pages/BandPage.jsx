/**
 * BAND AI page — real multi-agent collaboration.
 *
 * Connects to the actual BAND AI multi-agent platform via the backend API.
 * Displays the live authentication status of all seven agents.
 * Never fakes successful agent communication.
 *
 * NOTE: this file only changes presentation (layout JSX + CSS imports).
 * All state, effects, API calls and handlers are unchanged.
 */
import { useEffect, useState } from 'react';
import {
  Activity,
  Network,
  RefreshCw,
  ChevronRight,
  ShieldAlert,
  BrainCircuit,
  Microscope,
  DollarSign,
  Target,
  Database,
  AlertTriangle,
} from 'lucide-react';

import {
  bandApi,
  intelligenceApi,
  workflowsApi,
} from '../services/api';

import UnifiedWorkflowDetail from './UnifiedWorkflowDetail';
import './UnifiedWorkflows.css';
// These two files were previously never imported, which is why the page
// rendered unstyled. CommandCenter.css holds the shared tokens/components.
import './CommandCenter.css';
import './BandPage.css';

const AGENT_ICONS = {
  'Research Agent': Microscope,
  'Product Intelligence Agent': BrainCircuit,
  'Market Intelligence Agent': Target,
  'Financial Intelligence Agent': DollarSign,
  'Historical Intelligence Agent': Activity,
  'Risk Analysis Agent': ShieldAlert,
  'Strategy Agent': Network,
};

const BAND_AGENT_DEFS = [
  { name: 'Research Agent', role: 'Competitor evidence gathering' },
  { name: 'Product Intelligence Agent', role: 'Model & product comparison' },
  { name: 'Market Intelligence Agent', role: 'Market positioning' },
  { name: 'Financial Intelligence Agent', role: 'Pricing & financial analysis' },
  { name: 'Historical Intelligence Agent', role: 'Historical context' },
  { name: 'Risk Analysis Agent', role: 'Assumption & threat checking' },
  { name: 'Strategy Agent', role: 'Final recommendation' },
];

// Presentation only: maps a backend status string to a badge tone.
const statusTone = (value) => {
  const v = String(value || '').toLowerCase();
  if (v === 'completed' || v === 'success' || v === 'ok') return 'ok';
  if (v === 'failed' || v === 'error') return 'bad';
  if (v.includes('awaiting')) return 'alt';
  if (v === 'dispatched' || v === 'running') return 'info';
  return 'warn'; // partial and anything unknown: never shown as completed
};

const stepLabel = (name) =>
  name
    .replace(' Intelligence Agent', '')
    .replace(' Analysis Agent', '')
    .replace(' Agent', '');

export default function BandPage() {
  const [status, setStatus] = useState(null);
  const [agents, setAgents] = useState([]);
  const [events, setEvents] = useState([]);
  const [error, setError] = useState(null);
  const [workflowRunning, setWorkflowRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  const loadHistory = async () => {
    try {
      const data = await workflowsApi.list();
      setHistory(data.workflows || []);
    } catch (e) {
      console.error('Workflow history error:', e);
      setHistory([]);
    }
  };

  // Always request a fresh authentication status from BAND.
  const loadStatus = async () => {
    setLoadingStatus(true);

    try {
      const s = await bandApi.status();

      console.log('BAND STATUS FROM BACKEND:', s);

      setStatus(s);

      if (Array.isArray(s.agents)) {
        setAgents(s.agents);
      }
    } catch (e) {
      console.error('BAND STATUS ERROR:', e);

      setStatus({
        configured: false,
        available: false,
        reason: e.message || 'Backend unreachable',
        setup_instructions: [],
        agents: [],
        authenticated_count: 0,
        configured_count: 0,
      });
    } finally {
      setLoadingStatus(false);
    }
  };

  const loadAgents = async () => {
    try {
      const data = await bandApi.agents();

      if (Array.isArray(data.agents)) {
        setAgents(data.agents);
      }
    } catch (e) {
      console.error('BAND agents error:', e);
    }
  };

  const loadEvents = async () => {
    try {
      const data = await intelligenceApi.list();
      setEvents(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Intelligence events error:', e);
      setEvents([]);
    }
  };

  const runWorkflow = async (eventId) => {
    if (workflowRunning) return;

    setWorkflowRunning(true);
    setResult(null);
    setError(null);

    try {
      const data = await bandApi.workflow(eventId);

      setResult(data);
      await loadHistory();
    } catch (e) {
      console.error('BAND workflow error:', e);
      setError(
        e.message || 'Workflow failed. Check the backend logs.'
      );
    } finally {
      setWorkflowRunning(false);
    }
  };

  useEffect(() => {
    loadStatus();
    loadAgents();
    loadEvents();
    loadHistory();
  }, []);

  if (selectedWorkflow) {
    return (
      <UnifiedWorkflowDetail
        workflowId={selectedWorkflow}
        onBack={() => {
          setSelectedWorkflow(null);
          loadHistory();
        }}
      />
    );
  }

  const isConnected =
    status?.available === true ||
    (
      status?.authenticated_count > 0 &&
      status?.authenticated_count === status?.configured_count
    );

  const displayedAgents =
    agents.length > 0
      ? agents
      : BAND_AGENT_DEFS.map((agent) => ({
          ...agent,
          authenticated: false,
          configured: false,
        }));

  // ---- Presentation helpers (no behaviour of their own) ----
  const agentTotal = displayedAgents.length;
  const authenticatedCount = status?.authenticated_count ?? 0;
  const configuredCount = status?.configured_count ?? 0;
  const checking = status === null;

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

  const renderHeader = (description) => (
    <header className="cc-header">
      <div className="cc-header-text">
        <div className="cc-eyebrow">BAND AI AGENTS</div>
        <h1>Multi-Agent Collaboration</h1>
        <p>{description}</p>
      </div>

      <button
        className="cc-btn"
        onClick={loadStatus}
        disabled={loadingStatus}
      >
        <RefreshCw
          size={15}
          className={loadingStatus ? 'cc-spin' : ''}
        />
        {loadingStatus ? 'Checking...' : 'Refresh status'}
      </button>
    </header>
  );

  const renderConnectionPanel = () => (
    <section className="cc-panel" aria-label="BAND AI connection status">
      <div className="cc-panel-head">
        <div>
          <h2>
            <Network size={16} />
            Connection status
          </h2>
          <div className="cc-panel-sub">
            Values reported live by the backend from BAND AI.
          </div>
        </div>
      </div>

      <div className="cc-stats">
        <div className="cc-stat">
          <div className="cc-stat-label">BAND AI connection</div>
          <div className="cc-stat-value small">
            <span
              className={`cc-dot ${
                checking ? 'warn' : isConnected ? 'ok' : 'bad'
              }`}
            />
            {checking
              ? 'Checking…'
              : isConnected
                ? 'Connected'
                : 'Not connected'}
          </div>
        </div>

        <div className="cc-stat">
          <div className="cc-stat-label">Authenticated agents</div>
          <div className="cc-stat-value">
            {authenticatedCount}/{agentTotal}
          </div>
          <div className="cc-stat-note">Authenticated with BAND AI</div>
        </div>

        <div className="cc-stat">
          <div className="cc-stat-label">Configured agents</div>
          <div className="cc-stat-value">
            {configuredCount}/{agentTotal}
          </div>
          <div className="cc-stat-note">Agent credentials present</div>
        </div>
      </div>

      <div className="band-conn-reason">
        <strong>Reason</strong>
        <span>
          {status?.reason || 'Checking BAND AI connection...'}
        </span>
      </div>
    </section>
  );

  const renderAgentCard = (agent) => {
    const Icon = AGENT_ICONS[agent.name] || Network;
    const authenticated = agent.authenticated === true;

    return (
      <div
        key={agent.key || agent.name}
        className={`band-agent-card ${
          authenticated ? '' : 'band-agent-offline'
        }`}
      >
        <div className="band-agent-top">
          <div className="band-agent-icon">
            <Icon size={20} />
          </div>

          <span
            className={`cc-badge ${authenticated ? 'ok' : ''}`}
          >
            {authenticated
              ? isConnected
                ? 'Ready'
                : 'Authenticated'
              : 'Disconnected'}
          </span>
        </div>

        <div className="band-agent-info">
          <div className="band-agent-name">{agent.name}</div>
          <div className="band-agent-role">{agent.role}</div>
        </div>
      </div>
    );
  };

  const renderAgentGrid = () => (
    <section aria-label="Specialized agents">
      <div className="cc-section-title">
        <h2>Specialized agents</h2>
        <span>Status reflects real BAND AI authentication</span>
      </div>

      <div className="band-agent-grid">
        {displayedAgents.map(renderAgentCard)}
      </div>
    </section>
  );

  // Disconnected state
  if (!isConnected) {
    return (
      <div className="band-page">
        {renderHeader(
          'Seven specialized agents collaborating through BAND AI'
        )}

        {renderConnectionPanel()}

        <div className="cc-disconnected">
          <div className="cc-disconnected-icon">
            <Network size={30} />
          </div>

          <h2>
            {checking
              ? 'Checking BAND AI connection…'
              : 'BAND AI — Not Connected'}
          </h2>

          <p>
            {status?.reason ||
              'Checking BAND AI connection...'}
          </p>

          <div className="cc-instructions">
            <h3>Connection details</h3>

            <p>
              Configured agents: {configuredCount}/{agentTotal}
            </p>

            <p>
              Authenticated agents: {authenticatedCount}/{agentTotal}
            </p>

            <ol>
              {(status?.setup_instructions || []).map(
                (instruction, index) => (
                  <li key={index}>{instruction}</li>
                )
              )}
            </ol>

            <p className="cc-note">
              Agent communication is enabled only after successful
              authentication with BAND AI.
            </p>
          </div>
        </div>

        {renderAgentGrid()}
      </div>
    );
  }

  // Connected state
  return (
    <div className="band-page">
      {renderHeader(
        'Seven specialized agents collaborating through BAND AI'
      )}

      {renderConnectionPanel()}

      {renderAgentGrid()}

      <section className="cc-panel" aria-label="Agent workflow">
        <div className="cc-panel-head">
          <div>
            <h2>
              <Activity size={16} />
              Agent workflow
            </h2>
            <div className="cc-panel-sub">
              Order in which the agents collaborate on an event.
            </div>
          </div>
        </div>

        <ol className="band-pipeline">
          {BAND_AGENT_DEFS.map((agent, index) => (
            <li className="band-step" key={agent.name}>
              <span className="band-step-num">{index + 1}</span>
              <span className="band-step-label">
                {stepLabel(agent.name)}
              </span>
            </li>
          ))}
        </ol>

        <div className="band-pipeline-note">
          This shows the collaboration sequence only. An authenticated
          agent has not necessarily completed any work.
        </div>
      </section>

      <section className="cc-panel" aria-label="Intelligence events">
        <div className="cc-panel-head">
          <div>
            <h2>
              <Target size={16} />
              Run workflow on an event
            </h2>
            <div className="cc-panel-sub">
              Select an intelligence event to begin multi-agent analysis.
            </div>
          </div>
        </div>

        <div className="band-event-grid">
          {events.map((event) => (
            <div
              key={event.id}
              className={`cc-action ${
                workflowRunning ? 'is-busy' : ''
              }`}
              {...activate(() => runWorkflow(event.id))}
            >
              <div className="cc-action-main">
                <div className="cc-action-title">{event.title}</div>

                <div className="cc-action-meta">
                  <span>{event.company}</span>
                  <span className="cc-chip">{event.category}</span>
                </div>
              </div>

              <span className="cc-action-cta">
                Run workflow
                <ChevronRight size={14} />
              </span>
            </div>
          ))}
        </div>

        {events.length === 0 && (
          <div className="cc-empty">
            No intelligence events available.
          </div>
        )}
      </section>

      {workflowRunning && (
        <div className="band-running">
          <Activity size={22} className="cc-spin" />
          <div>
            <h3>Workflow in progress</h3>
            <p>Agents are being dispatched through BAND AI…</p>
          </div>
        </div>
      )}

      {result && (
        <div className="band-result">
          <section className="cc-panel band-result-summary">
            <h2>
              Unified workflow dispatched — {result.agent_count} agents
            </h2>

            <p>
              Event, agent dispatches, BAND room and Hindsight context
              are synchronized under workflow ID{' '}
              <code className="cc-mono">
                {result.workflow_id}
              </code>

              {result.recommendation_id && (
                <>
                  {' '}(recommendation{' '}
                  <code className="cc-mono">
                    {result.recommendation_id.slice(0, 8)}…
                  </code>
                  )
                </>
              )}

              {result.status !== 'completed' && (
                <>
                  {' '}Status:{' '}
                  <span
                    className={`cc-badge ${statusTone(result.status)}`}
                  >
                    {result.status}
                  </span>
                  {' '}— actual agent replies may still be pending.
                </>
              )}
            </p>
          </section>

          {result.band_room && (
            <section className="cc-panel">
              <div className="cc-panel-head">
                <h3>
                  <Network size={15} />
                  BAND collaboration room
                </h3>
              </div>

              <div className="cc-kv-list">
                <div className="cc-kv">
                  <span className="cc-kv-label">Room ID</span>
                  <code className="cc-mono">
                    {result.band_room.room_id}
                  </code>
                </div>

                {result.band_room.room_title && (
                  <div className="cc-kv">
                    <span className="cc-kv-label">Room name</span>
                    <span>{result.band_room.room_title}</span>
                  </div>
                )}

                <div className="cc-kv">
                  <span className="cc-kv-label">Open room</span>
                  <span>
                    Open app.band.ai and search for room ID{' '}
                    <code className="cc-mono">
                      {result.band_room.room_id}
                    </code>
                  </span>
                </div>

                <div className="cc-kv">
                  <span className="cc-kv-label">
                    Participants (
                    {(result.band_room.participants || []).length})
                  </span>

                  <span>
                    {(result.band_room.participants || [])
                      .map((participant) =>
                        participant.name || participant.handle
                      )
                      .join(', ')}
                  </span>
                </div>
              </div>
            </section>
          )}

          {result.hindsight && (
            <section className="cc-panel">
              <div className="cc-panel-head">
                <h3>
                  <Database size={15} />
                  Hindsight (bank {result.hindsight.bank_id})
                </h3>
              </div>

              <div className="cc-kv-list">
                <div className="cc-kv">
                  <span className="cc-kv-label">Recall</span>

                  {result.hindsight.available ? (
                    <span>
                      Retrieved {result.hindsight.recall_count}
                      {' '}historical memories before agent dispatch.
                    </span>
                  ) : (
                    <span className="cc-notice">
                      Hindsight unavailable — recall skipped.
                    </span>
                  )}
                </div>

                {(result.hindsight.recall_refs || []).length > 0 && (
                  <div className="cc-kv">
                    <span className="cc-kv-label">Recalled</span>

                    <div className="band-recall-list">
                      {result.hindsight.recall_refs
                        .slice(0, 4)
                        .map((reference, index) => (
                          <div
                            key={reference.id || index}
                            className="band-recall-item"
                          >
                            <code className="cc-mono">
                              {reference.id}
                            </code>
                            <span>
                              {(reference.content || '').slice(0, 120)}
                            </span>
                          </div>
                        ))}

                      {result.hindsight.recall_refs.length > 4 && (
                        <div className="cc-panel-sub">
                          …{result.hindsight.recall_refs.length - 4}
                          {' '}more (see unified workflow detail)
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="cc-kv">
                  <span className="cc-kv-label">Reflect</span>

                  {result.hindsight.reflection ? (
                    <div className="band-reflect">
                      {result.hindsight.reflection.slice(0, 500)}
                      {result.hindsight.reflection.length > 500
                        ? '…'
                        : ''}
                    </div>
                  ) : (
                    <span>No reflect synthesis available.</span>
                  )}
                </div>
              </div>
            </section>
          )}

          <section className="cc-panel">
            <div className="cc-panel-head">
              <h3>
                <Activity size={15} />
                Agent dispatch
              </h3>
            </div>

            <div className="band-dispatch-grid">
              {(result.agents || []).map((message, index) => (
                <div
                  key={message.band_message_id || index}
                  className="band-agent-message"
                >
                  <div className="band-message-head">
                    <span className="band-message-agent">
                      {message.agent_name}
                    </span>

                    <span
                      className={`cc-badge ${statusTone(message.status)}`}
                    >
                      {message.status}
                    </span>
                  </div>

                  <div className="band-message-output">
                    {message.band_message_id ? (
                      <>
                        Dispatched as real BAND message{' '}
                        <code className="cc-mono">
                          {message.band_message_id.slice(0, 8)}…
                        </code>

                        {message.band_sent_at && (
                          <>
                            {' '}at{' '}
                            {new Date(
                              message.band_sent_at
                            ).toLocaleString()}
                          </>
                        )}

                        {' '}— waiting for the agent's actual reply.
                      </>
                    ) : (
                      <>
                        Dispatch failed — no BAND message created.{' '}
                        {message.message
                          ? `Error: ${message.message}`
                          : ''}
                      </>
                    )}
                  </div>

                  {message.handoff_to && (
                    <div className="band-message-handoff">
                      Handoff → {message.handoff_to}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div>
              <button
                className="cc-btn primary"
                onClick={() => setSelectedWorkflow(result.workflow_id)}
              >
                View unified workflow detail
                <ChevronRight size={14} />
              </button>
            </div>
          </section>
        </div>
      )}

      {history.length > 0 && (
        <section className="cc-panel" aria-label="Workflow history">
          <div className="cc-panel-head">
            <div>
              <h2>
                <Database size={16} />
                Unified workflow history
              </h2>
              <div className="cc-panel-sub">
                Recent cross-platform runs — open a synchronized view
                of the event, BAND room, Hindsight and recommendation.
              </div>
            </div>
          </div>

          <div className="cc-list">
            {history.slice(0, 6).map((workflow) => (
              <div
                key={workflow.workflow_id}
                className="cc-action"
                {...activate(() =>
                  setSelectedWorkflow(workflow.workflow_id)
                )}
              >
                <div className="cc-action-main">
                  <div className="cc-action-title">
                    {workflow.event_title || workflow.workflow_id}
                  </div>

                  <div className="band-history-meta">
                    <code className="cc-mono">
                      {workflow.workflow_id.slice(0, 8)}…
                    </code>

                    <span
                      className={`cc-badge ${statusTone(workflow.status)}`}
                    >
                      {workflow.status}
                    </span>

                    {workflow.band_room_id && (
                      <span>
                        room{' '}
                        <code className="cc-mono">
                          {workflow.band_room_id.slice(0, 8)}…
                        </code>
                      </span>
                    )}

                    {workflow.hindsight_retained_at && (
                      <span className="cc-badge ok">retained</span>
                    )}
                  </div>
                </div>

                <span className="cc-action-cta">
                  Open
                  <ChevronRight size={14} />
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {error && (
        <div className="cc-error" role="alert">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}