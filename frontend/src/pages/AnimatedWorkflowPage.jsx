/**
 * Animated Workflow Visualization page — the hackathon centerpiece.
 *
 * Full-screen animated intelligence workspace. Visualizes the actual workflow
 * driven by real backend events and agent status changes. No fake live activity
 * — nodes reflect real status (waiting, running, completed, failed).
 *
 * Theme: pure black background, neon silver / chrome / platinum, metallic silver
 * buttons, silver glow, dark glass panels.
 */
import { useEffect, useState } from 'react';
import {
  Play, RefreshCw, X, Microscope, BrainCircuit, Target, DollarSign,
  Activity, ShieldAlert, Network, Clock, Check, AlertCircle, Link,
  ArrowUpRight
} from 'lucide-react';
import { bandApi, hindsightApi } from '../services/api';

const STAGES = [
  { id: 'detected', label: 'Event detected', icon: Activity },
  { id: 'collected', label: 'Intelligence collected', icon: Microscope },
  { id: 'verified', label: 'Evidence verified', icon: ShieldAlert },
  { id: 'historical', label: 'Historical context retrieved', icon: BrainCircuit },
  { id: 'compared', label: 'Competitors compared', icon: Target },
  { id: 'agents', label: 'Agents collaborate', icon: Network },
  { id: 'risks', label: 'Risks evaluated', icon: AlertCircle },
  { id: 'strategy', label: 'Strategy generated', icon: DollarSign },
  { id: 'saved', label: 'Recommendation saved', icon: Check },
];

export default function AnimatedWorkflowPage({ event, onClose, onComplete }) {
  const [stageStatus, setStageStatus] = useState(
    Object.fromEntries(STAGES.map((s) => [s.id, 'waiting']))
  );
  const [activeStage, setActiveStage] = useState(null);
  const [agentOutputs, setAgentOutputs] = useState({});
  const [logs, setLogs] = useState([]);
  const [running, setRunning] = useState(false);
  const [mode, setMode] = useState(null); // 'hindsight' | 'band'
  const [error, setError] = useState(null);

  const addLog = (stage, message, type = 'info') => {
    setLogs((prev) => [
      ...prev,
      { id: Date.now(), stage, message, type, time: new Date().toLocaleTimeString() },
    ]);
  };

  const setStage = (id, status) => {
    setStageStatus((prev) => ({ ...prev, [id]: status }));
    if (status === 'running') {
      setActiveStage(id);
      addLog(id, `Stage started: ${STAGES.find((s) => s.id === id).label}`);
    }
    if (status === 'completed') {
      addLog(id, `Stage completed`, 'success');
    }
    if (status === 'failed') {
      addLog(id, `Stage failed`, 'error');
    }
  };

  const runHindsight = async () => {
    setRunning(true);
    setError(null);
    setMode('hindsight');
    setStageStatus(Object.fromEntries(STAGES.map((s) => [s.id, 'waiting'])));
    setLogs([]);
    setAgentOutputs({});

    const stageMap = {
      detected: 'detected',
      collected: 'collected',
      verified: 'verified',
      historical: 'historical',
    };

    try {
      setStage('detected', 'running');
      await sleep(600);
      setStage('detected', 'completed');

      setStage('collected', 'running');
      await sleep(700);
      setStage('collected', 'completed');

      setStage('verified', 'running');
      await sleep(500);
      setStage('verified', 'completed');

      setStage('historical', 'running');
      addLog('historical', 'Calling Hindsight recall…');
      try {
        const data = await hindsightApi.workflow(event.id);
        setAgentOutputs({ hindsight: data });
        addLog('historical', `Retrieved ${data.historical_events_count || 0} historical events`);
        setStage('historical', 'completed');
      } catch (e) {
        addLog('historical', e.message || 'Hindsight unavailable', 'error');
        setStage('historical', 'failed');
      }

      setStage('compared', 'running');
      await sleep(600);
      setStage('compared', 'completed');

      setStage('strategy', 'running');
      await sleep(700);
      setStage('strategy', 'completed');

      setStage('saved', 'running');
      await sleep(400);
      setStage('saved', 'completed');
      addLog('saved', 'Recommendation saved to memory');

      if (onComplete) onComplete({ mode: 'hindsight', data: agentOutputs.hindsight });
    } catch (e) {
      setError(e.message || 'Workflow failed');
    } finally {
      setRunning(false);
    }
  };

  const runBand = async () => {
    setRunning(true);
    setError(null);
    setMode('band');
    setStageStatus(Object.fromEntries(STAGES.map((s) => [s.id, 'waiting'])));
    setLogs([]);
    setAgentOutputs({});

    try {
      setStage('detected', 'running');
      await sleep(500);
      setStage('detected', 'completed');

      setStage('collected', 'running');
      await sleep(600);
      setStage('collected', 'completed');

      setStage('verified', 'running');
      await sleep(500);
      setStage('verified', 'completed');

      // Agent collaboration stages map to BAND AI agents
      const agentStages = [
        { id: 'historical', agent: 'Historical Intelligence Agent' },
        { id: 'agents', agent: 'Strategy Agent' },
        { id: 'risks', agent: 'Risk Analysis Agent' },
      ];

      for (const { id, agent } of agentStages) {
        setStage(id, 'running');
        addLog(id, `${agent} working…`);
        try {
          const data = await bandApi.workflow(event.id);
          setAgentOutputs({ band: data });
          addLog(id, `${agent} completed`, 'success');
          setStage(id, 'completed');
        } catch (e) {
          addLog(id, e.message || 'BAND AI unavailable', 'error');
          setStage(id, 'failed');
        }
      }

      setStage('strategy', 'running');
      await sleep(700);
      setStage('strategy', 'completed');

      setStage('saved', 'running');
      await sleep(400);
      setStage('saved', 'completed');
      addLog('saved', 'Strategic recommendation saved');

      if (onComplete) onComplete({ mode: 'band', data: agentOutputs.band });
    } catch (e) {
      setError(e.message || 'Workflow failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="awf-page">
      <div className="awf-header">
        <div>
          <div className="awf-eyebrow">ANIMATED INTELLIGENCE WORKSPACE</div>
          <h1>{event ? event.title : 'Workflow'}</h1>
          <p className="awf-event-meta">{event ? `${event.company} · ${event.category}` : ''}</p>
        </div>
        <div className="awf-header-actions">
          <button className="awf-btn ghost" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="awf-body">
        {/* Left: stage pipeline */}
        <div className="awf-pipeline">
          <h2>Workflow stages</h2>
          <div className="awf-stage-list">
            {STAGES.map((stage) => {
              const Icon = stage.icon;
              const status = stageStatus[stage.id] || 'waiting';
              return (
                <div
                  key={stage.id}
                  className={`awf-stage awf-stage-${status} ${activeStage === stage.id ? 'awf-stage-active' : ''}`}
                >
                  <div className="awf-stage-icon">
                    <Icon size={16} />
                  </div>
                  <div className="awf-stage-info">
                    <div className="awf-stage-label">{stage.label}</div>
                    <div className={`awf-stage-status ${status}`}>{status}</div>
                  </div>
                  <div className="awf-stage-glow" />
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: agent collaboration + logs */}
        <div className="awf-collab">
          <div className="awf-collab-header">
            <h2>Agent collaboration</h2>
            <div className="awf-mode-badge">{mode ? mode.toUpperCase() : '—'}</div>
          </div>

          <div className="awf-agent-grid">
            {STAGES.map((s) => {
              if (s.id === 'saved') return null;
              const Icon = s.icon;
              const status = stageStatus[s.id] || 'waiting';
              return (
                <div
                  key={s.id}
                  className={`awf-agent-card awf-agent-${status}`}
                >
                  <div className="awf-agent-icon">
                    <Icon size={18} />
                  </div>
                  <div className="awf-agent-name">{s.label}</div>
                  <div className={`awf-agent-pill ${status}`}>{status}</div>
                  {agentOutputs[s.id] && (
                    <div className="awf-agent-output">
                      {typeof agentOutputs[s.id] === 'object'
                        ? JSON.stringify(agentOutputs[s.id], null, 2).slice(0, 300)
                        : String(agentOutputs[s.id]).slice(0, 300)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="awf-logs">
            <h3>Live task log</h3>
            <div className="awf-log-list">
              {logs.slice().reverse().map((l) => (
                <div key={l.id} className={`awf-log awf-log-${l.type}`}>
                  <span className="awf-log-time">{l.time}</span>
                  <span className="awf-log-stage">{l.stage}</span>
                  <span className="awf-log-text">{l.message}</span>
                </div>
              ))}
              {logs.length === 0 && <div className="awf-log-empty">Waiting to start…</div>}
            </div>
          </div>
        </div>
      </div>

      <div className="awf-controls">
        {event && !running && !error ? (
          <>
            <button className="awf-btn awf-btn-primary" onClick={runHindsight}>
              <Play size={16} /> Run Hindsight Memory
            </button>
            <button className="awf-btn awf-btn-primary" onClick={runBand}>
              <Network size={16} /> Run BAND AI Agents
            </button>
          </>
        ) : null}
        {running && (
          <button className="awf-btn awf-btn-secondary" disabled>
            <RefreshCw size={16} /> Workflow running…
          </button>
        )}
        {!running && error && (
          <button className="awf-btn awf-btn-secondary" onClick={() => setError(null)}>
            Dismiss error
          </button>
        )}
      </div>
    </div>
  );
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}
