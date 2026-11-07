/**
 * Demo Company page — MINTY-GPT (simulated demo company).
 * Shows latest profile, update history, and allows sending test updates
 * to the demo-company API (requires configured API key).
 */
import { useEffect, useState } from 'react';
import {
  ShieldAlert, Activity, List, RefreshCw, Link, Clock,
  ShieldCheck, Info, Send, Copy, ArrowUpRight
} from 'lucide-react';
import { demoCompanyApi } from '../services/api';

export default function DemoCompanyPage() {
  const [demo, setDemo] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [form, setForm] = useState({
    company_name: 'MINTY-GPT',
    company_description: '',
    model_updates: '',
    product_updates: '',
    pricing_updates: '',
    infrastructure_updates: '',
    business_strategy_updates: '',
    event_title: '',
    event_description: '',
    event_category: 'products',
    publication_date: '',
    source_url: '',
    change_type: '',
  });
  const [submitStatus, setSubmitStatus] = useState(null); // 'sending' | 'ok' | 'error'

  const load = async () => {
    setLoading(true);
    try {
      const [d, ev] = await Promise.all([demoCompanyApi.get(), demoCompanyApi.events()]);
      setDemo(d);
      setEvents(Array.isArray(ev) ? ev : []);
    } catch (e) {
      setError(e.message || 'Failed to load demo company data');
      setDemo(null);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitStatus('sending');
    try {
      await demoCompanyApi.update(form, apiKey || undefined);
      setSubmitStatus('ok');
      load();
    } catch (err) {
      setSubmitStatus('error');
      setError(err.message || 'Update failed');
    }
  };

  return (
    <div className="dc-page">
      <header className="dc-header">
        <div>
          <div className="dc-eyebrow">DEMO COMPANY — MINTY-GPT</div>
          <h1>Simulated Demo Company</h1>
          <p>MINTY-GPT is a fictional simulated demo company. It is not a real company. Updates arrive via the backend demo-company API.</p>
        </div>
      </header>

      <div className="dc-alert">
        <ShieldAlert size={16} />
        <strong>SIMULATED DEMO COMPANY</strong> — All data here is simulated for demonstration. Never treat MINTY-GPT as a real company.
      </div>

      {error && <div className="dc-error">{error}</div>}

      <div className="dc-grid">
        <div className="dc-panel dc-profile-panel">
          <div className="dc-panel-head">
            <ShieldAlert size={18} />
            <div>
              <div className="dc-panel-title">{demo?.company_name || 'MINTY-GPT'}</div>
              <div className="dc-panel-sub">Latest received profile state</div>
            </div>
            <span className="dc-badge sim">SIMULATED DEMO</span>
          </div>
          <div className="dc-profile-body">
            {loading ? (
              <div className="dc-skeleton" />
            ) : demo ? (
              <>
                <div className="dc-field">
                  <span className="dc-field-label">Description</span>
                  <p className="dc-field-value">{demo.description || 'Not provided'}</p>
                </div>
                <div className="dc-field">
                  <span className="dc-field-label">Model updates</span>
                  <p className="dc-field-value">{demo.model_updates || 'Not provided'}</p>
                </div>
                <div className="dc-field">
                  <span className="dc-field-label">Product updates</span>
                  <p className="dc-field-value">{demo.product_updates || 'Not provided'}</p>
                </div>
                <div className="dc-field">
                  <span className="dc-field-label">Pricing updates</span>
                  <p className="dc-field-value">{demo.pricing_updates || 'Not provided'}</p>
                </div>
                <div className="dc-field">
                  <span className="dc-field-label">Infrastructure updates</span>
                  <p className="dc-field-value">{demo.infrastructure_updates || 'Not provided'}</p>
                </div>
                <div className="dc-field">
                  <span className="dc-field-label">Business strategy updates</span>
                  <p className="dc-field-value">{demo.business_strategy_updates || 'Not provided'}</p>
                </div>
                <div className="dc-field">
                  <span className="dc-field-label">Last updated</span>
                  <p className="dc-field-value">{demo.last_updated_at ? new Date(demo.last_updated_at).toLocaleString() : 'Never'}</p>
                </div>
              </>
            ) : (
              <div className="dc-empty">No demo company data received yet.</div>
            )}
          </div>
        </div>

        <div className="dc-panel dc-update-panel">
          <div className="dc-panel-head">
            <Activity size={18} />
            <div>
              <div className="dc-panel-title">Update history</div>
              <div className="dc-panel-sub">Events received from the external demo website</div>
            </div>
            <button className="dc-btn ghost" onClick={load}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
          <div className="dc-update-body">
            {loading ? (
              <div className="dc-skeleton dc-skeleton-wide" />
            ) : events.length === 0 ? (
              <div className="dc-empty">No update history yet.</div>
            ) : (
              <div className="dc-event-list">
                {events.map((ev) => (
                  <div key={ev.id} className="dc-event">
                    <div className="dc-event-head">
                      <div className="dc-event-title">{ev.event_title || '(no title)'}</div>
                      <span className={`dc-event-verif ${ev.change_type ? 'dc-verif-changed' : 'dc-verif-none'}`}>
                        {ev.change_type || 'profile update'}
                      </span>
                    </div>
                    <div className="dc-event-meta">
                      <span>Company: {ev.company_name || 'MINTY-GPT'}</span>
                      <span>·</span>
                      <span>Category: {ev.event_category || '—'}</span>
                      <span>·</span>
                      <span>Received: {new Date(ev.received_at).toLocaleString()}</span>
                    </div>
                    {ev.changed_fields && ev.changed_fields.length > 0 && (
                      <div className="dc-changed">
                        <span className="dc-changed-label">Changed fields:</span>
                        {ev.changed_fields.map((f) => (
                          <span key={f} className="dc-chip">{f}</span>
                        ))}
                      </div>
                    )}
                    {ev.source_url && (
                      <a href={ev.source_url} target="_blank" rel="noreferrer" className="dc-source-link">
                        <Link size={12} /> Source: {ev.source_url}
                      </a>
                    )}
                    {ev.created_intelligence_event && (
                      <span className="dc-badge created">Intelligence event created</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="dc-send-panel">
        <div className="dc-panel-head">
          <Send size={18} />
          <div>
            <div className="dc-panel-title">Send test update to demo API</div>
            <div className="dc-panel-sub">POST /api/demo-company/update — for testing the external website integration</div>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="dc-send-form">
          <div className="dc-form-row">
            <label>API key (X-Demo-API-Key)</label>
            <input
              name="apiKeyLocal"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Set DEMO_COMPANY_API_KEY in backend/.env"
            />
            <span className="dc-form-hint">Not exposed to the browser; sent only as a request header.</span>
          </div>
          <div className="dc-form-grid">
            <dcField label="Company name" name="company_name" default="MINTY-GPT" />
            <dcField label="Company description" name="company_description" type="area" />
            <dcField label="Model updates" name="model_updates" type="area" />
            <dcField label="Product updates" name="product_updates" type="area" />
            <dcField label="Pricing updates" name="pricing_updates" type="area" />
            <dcField label="Infrastructure updates" name="infrastructure_updates" type="area" />
            <dcField label="Business strategy updates" name="business_strategy_updates" type="area" />
            <dcField label="Event title" name="event_title" />
            <dcField label="Event description" name="event_description" type="area" />
            <dcField label="Event category" name="event_category" default="products" />
            <dcField label="Publication date" name="publication_date" type="date" />
            <dcField label="Source URL" name="source_url" type="url" />
            <dcField label="Change type" name="change_type" />
          </div>
          <div className="dc-submit-row">
            <button type="submit" className="dc-btn-send" disabled={submitStatus === 'sending'}>
              {submitStatus === 'sending' ? <><Activity size={16} spin /> Sending…</> : <><Send size={16} /> Send update</>}
            </button>
            {submitStatus === 'ok' && <span className="dc-msg ok"><ShieldCheck size={14} /> Update sent successfully.</span>}
            {submitStatus === 'error' && <span className="dc-msg err"><ShieldAlert size={14} /> Send failed.</span>}
          </div>
        </form>
      </div>

      <div className="dc-note">
        <Info size={14} />
        The external website must be configured with the API key (DEMO_COMPANY_API_KEY) and point at this backend.
        Until a connection is configured and tested, no external connection is claimed.
      </div>
    </div>
  );
}

function dcField({ label, name, type = 'text', default: defaultValue }) {
  return (
    <div className="dc-field-wrap">
      <label>{label}</label>
      {type === 'area' ? (
        <textarea name={name} defaultValue={defaultValue} rows={2} />
      ) : (
        <input type={type} name={name} defaultValue={defaultValue} />
      )}
    </div>
  );
}
