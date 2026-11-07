/**
 * Strategic Report page — final strategy result after Hindsight / BAND AI.
 *
 * Professional strategic report with event summary, competitor comparison,
 * impact analysis, recommended strategy, actions, risks, evidence, confidence.
 * Users can accept/reject and record action taken + outcome, feeding back into
 * Hindsight memory (continuous learning cycle).
 */
import { useEffect, useState } from 'react';
import {
  RefreshCw, Link, ShieldCheck, AlertTriangle, Clock, Target, DollarSign,
  Activity, BrainCircuit, Copy, Check, ChevronRight, X
} from 'lucide-react';
import { strategyApi, hindsightApi } from '../services/api';

export default function StrategicReportPage({ recommendationId, onClose }) {
  const [rec, setRec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const data = await strategyApi.get(recommendationId);
      setRec(data);
    } catch (e) {
      setError(e.message || 'Failed to load recommendation');
    } finally {
      setLoading(false);
  }
  };

  const updateStatus = async (status) => {
    try {
      await strategyApi.update(recommendationId, { status });
      setRec((r) => (r ? { ...r, status } : r));
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e.message || 'Update failed');
  }
  };

  const recordOutcome = async (field, value) => {
    try {
      await strategyApi.update(recommendationId, { [field]: value });
      setRec((r) => (r ? { ...r, [field]: value } : r));
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      // Feed back into Hindsight memory as an outcome record
      try {
        await hindsightApi.retain(
          `Outcome for recommendation ${recommendationId}: ${value}`,
          'competeiq-outcomes',
          { recommendation_id: recommendationId, field }
        );
      } catch {
        // Hindsight not configured — that's fine, outcome still saved locally
      }
    } catch (e) {
      setError(e.message || 'Failed to record outcome');
    }
  };

  useEffect(() => { load(); }, [recommendationId]);

  if (loading) {
    return (
      <div className="strat-page">
        <div className="strat-loading"><Activity size={24} /> Loading strategy report…</div>
      </div>
    );
  }

  if (!rec) {
    return (
      <div className="strat-page">
        <div className="strat-empty">{error || 'Recommendation not found.'}</div>
        <button className="strat-btn" onClick={onClose}>Close</button>
      </div>
    );
  }

  return (
    <div className="strat-page">
      <header className="strat-header">
        <div>
          <div className="strat-eyebrow">STRATEGIC REPORT</div>
          <h1>Competitive Intelligence Recommendation</h1>
          <p>{rec.event_summary || 'Strategic recommendation generated from intelligence event.'}</p>
        </div>
        <div className="strat-header-actions">
          <button className="strat-btn ghost" onClick={onClose}>
            <X /> Close
          </button>
        </div>
      </header>

      <div className="strat-meta">
        <div className="strat-meta-item">
          <span className="strat-meta-label">Workflow</span>
          <span className="strat-meta-value">{rec.workflow_type}</span>
        </div>
        <div className="strat-meta-item">
          <span className="strat-meta-label">Confidence</span>
          <span className={`strat-confidence strat-conf-${rec.confidence_score}`}>
            {rec.confidence_score}
          </span>
        </div>
        <div className="strat-meta-item">
          <span className="strat-meta-label">Status</span>
          <span className={`strat-status strat-status-${rec.status}`}>{rec.status}</span>
        </div>
        <div className="strat-meta-item">
          <span className="strat-meta-label">Created</span>
          <span className="strat-meta-value">{rec.created_at ? new Date(rec.created_at).toLocaleString() : '—'}</span>
        </div>
        <div className="strat-meta-item">
          <span className="strat-meta-label">Event</span>
          <span className="strat-event-id">{rec.event_id}</span>
        </div>
      </div>

      <div className="strat-grid">
        <section className="strat-section">
          <h3>Event summary</h3>
          <p className="strat-text">{rec.event_summary || 'Not provided'}</p>
        </section>
        <section className="strat-section">
          <h3>Competitor comparison</h3>
          <p className="strat-text">{rec.competitor_comparison || 'Not provided'}</p>
        </section>
        <section className="strat-section strat-wide">
          <h3>Impact on NEXORA AI</h3>
          <p className="strat-text">{rec.impact_on_nexora || 'Not assessed'}</p>
        </section>
        <section className="strat-section strat-wide">
          <h3>Impact on MINTY-GPT</h3>
          <p className="strat-text">{rec.impact_on_minty || 'Not assessed (demo company not selected)'}</p>
        </section>
        <section className="strat-section">
          <h3>Historical context</h3>
          <p className="strat-text">{rec.historical_context || 'No historical context available'}</p>
        </section>
        <section className="strat-section">
          <h3>Market opportunity</h3>
          <p className="strat-text">{rec.market_opportunity || 'Not provided'}</p>
        </section>
        <section className="strat-section">
          <h3>Competitive threats</h3>
          <p className="strat-text">{rec.competitive_threats || 'Not provided'}</p>
        </section>
        <section className="strat-section strat-wide">
          <h3>Strengths & weaknesses</h3>
          <p className="strat-text">{rec.strengths_weaknesses || 'Not provided'}</p>
        </section>
      </div>

      <section className="strat-section strat-full">
        <h3>Recommended strategy</h3>
        <p className="strat-text strat-highlight">{rec.recommended_strategy || 'Not provided'}</p>
      </section>

      <div className="strat-actions-grid">
        <section className="strat-section">
          <h3>Immediate actions</h3>
          <p className="strat-text">{rec.immediate_actions || 'Not provided'}</p>
        </section>
        <section className="strat-section">
          <h3>30-day actions</h3>
          <p className="strat-text">{rec.actions_30_day || 'Not provided'}</p>
        </section>
        <section className="strat-section">
          <h3>90-day actions</h3>
          <p className="strat-text">{rec.actions_90_day || 'Not provided'}</p>
        </section>
      </div>

      <section className="strat-section strat-full">
        <h3>Expected business impact</h3>
        <p className="strat-text">{rec.expected_business_impact || 'Not provided'}</p>
      </section>
      <section className="strat-section strat-full">
        <h3>Risks & assumptions</h3>
        <p className="strat-text">{rec.risks_assumptions || 'Not provided'}</p>
      </section>
      <section className="strat-section strat-full">
        <h3>Evidence sources</h3>
        <p className="strat-text">{rec.evidence_sources || rec.source_url || 'No sources recorded'}</p>
      </section>

      <div className="strat-decision">
        <h3>Record decision & outcome</h3>
        <p>Feed the outcome back into Hindsight memory for continuous learning.</p>
        <div className="strat-decision-buttons">
          <button className="strat-btn strat-btn-accept" onClick={() => updateStatus('accepted')}>
            <Check size={16} /> Accept recommendation
          </button>
          <button className="strat-btn strat-btn-reject" onClick={() => updateStatus('rejected')}>
            <AlertTriangle size={16} /> Reject recommendation
          </button>
        </div>
        <div className="strat-outcome">
          <label>Action taken</label>
          <textarea
            rows={2}
            placeholder="Describe the action taken…"
            onChange={(e) => recordOutcome('action_taken', e.target.value)}
          />
          <label>Eventual outcome</label>
          <textarea
            rows={2}
            placeholder="Describe the eventual outcome…"
            onChange={(e) => recordOutcome('outcome_recorded', e.target.value)}
          />
        </div>
        {saved && <span className="strat-saved"><Check size={14} /> Saved to memory</span>}
      </div>

      {error && <div className="strat-error">{error}</div>}
    </div>
  );
}
