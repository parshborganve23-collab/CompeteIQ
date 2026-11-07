/**
 * AI Models page — clickable model intelligence.
 * Displays model cards; clicking a card opens a detailed model view.
 * All data comes from the backend; nothing is fabricated.
 */
import { useEffect, useState } from 'react';
import {
  BrainCircuit, Cpu, LayoutList, BarChart3, DollarSign, Cloud,
  Microscope, Server, Link, ShieldAlert, Info, ChevronRight,
  ArrowUpRight, X, RefreshCw, Sparkles
} from 'lucide-react';
import { modelsApi } from '../services/api';
import './AIModelsPage.css';

const UNKNOWN = 'Not publicly disclosed';

export default function AIModelsPage() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [filter, setFilter] = useState('all'); // all | company | status | category

  const load = async () => {
    setLoading(true);
    try {
      const data = await modelsApi.list();
      setModels(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message || 'Failed to load AI models');
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const groupedByCompany = {};
  models.forEach((m) => {
    (groupedByCompany[m.company || 'Unknown']) = (groupedByCompany[m.company || 'Unknown'] || 0) + 1;
  });

  const companies = Object.keys(groupedByCompany).sort();

  return (
    <div className="aim-page">
      {selected ? (
        <ModelDetail model={selected} onClose={() => setSelected(null)} />
      ) : (
        <ModelGrid
          models={models}
          loading={loading}
          error={error}
          onReload={load}
          onSelect={setSelected}
          companies={companies}
          filter={filter}
          setFilter={setFilter}
        />
      )}
    </div>
  );
}

/* ---------- Model grid ---------- */

function ModelGrid({ models, loading, error, onReload, onSelect, companies, filter, setFilter }) {
  const [search, setSearch] = useState('');

  const filtered = models.filter((m) => {
    const matchSearch =
      !search ||
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.company.toLowerCase().includes(search.toLowerCase()) ||
      (m.model_type || '').toLowerCase().includes(search.toLowerCase());
    return matchSearch;
  });

  return (
    <div className="aim-grid">
      <header className="aim-header">
        <div>
          <div className="aim-eyebrow">TECHNOLOGY PORTFOLIO</div>
          <h1>AI Models</h1>
          <p>Explore NEXORA AI and competitor AI models. Click any card for full technical specifications.</p>
        </div>
        <div className="aim-actions">
          <button className="aim-btn ghost" onClick={onReload}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </header>

      {error && <div className="aim-empty">{error}</div>}

      <div className="aim-toolbar">
        <div className="aim-chip-group">
          {companies.map((c) => (
            <button
              key={c}
              className={`aim-chip ${filter === c ? 'aim-chip-active' : ''}`}
              onClick={() => setFilter(filter === c ? 'all' : c)}
            >
              {c} <span className="aim-chip-count">{companies[c]}</span>
            </button>
          ))}
          <button
            className={`aim-chip ${filter === 'all' ? 'aim-chip-active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
        </div>
        <div className="aim-search">
          <input
            type="text"
            placeholder="Search models, company, type…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="aim-cards">
        {loading
          ? [...Array(6)].map((_, i) => <div key={i} className="aim-card-skeleton" />)
          : filtered.length === 0
          ? <div className="aim-empty">No AI models found.</div>
          : filtered.map((m) => (
              <ModelCard key={m.id} model={m} onSelect={onSelect} />
            ))}
      </div>
    </div>
  );
}

function ModelCard({ model, onSelect }) {
  const statusClass = `aim-status aim-status-${(model.status || 'unknown').toLowerCase()}`;
  return (
    <div className="aim-card" onClick={() => onSelect(model)} role="button" tabIndex={0} onKeyDown={(e) => e.key === 'Enter' && onSelect(model)}>
      <div className="aim-card-icon">
        <BrainCircuit size={20} />
      </div>
      <div className="aim-card-body">
        <div className="aim-card-meta">
          <span className="aim-card-company">{model.company}</span>
          <span className={`aim-tag aim-tag-type`}>{model.model_type || 'Model'}</span>
        </div>
        <h3 className="aim-card-title">{model.name}</h3>
        <div className="aim-card-sub">
          <span>{model.family}</span>
          {model.version && <span>· {model.version}</span>}
        </div>
        <p className="aim-card-desc">{model.capabilities || model.reasoning_capabilities || 'No description available.'}</p>
        <div className="aim-card-footer">
          <span className={statusClass}>{model.status || 'Unknown'}</span>
          <ChevronRight size={14} />
        </div>
      </div>
    </div>
  );
}

/* ---------- Model detail ---------- */

function ModelDetail({ model, onClose }) {
  const fields = [
    { label: 'Model name', value: model.name },
    { label: 'Version', value: model.version || UNKNOWN },
    { label: 'Developer', value: model.company },
    { label: 'Model family', value: model.family || UNKNOWN },
    { label: 'Release date', value: model.release_date || UNKNOWN },
    { label: 'Status', value: model.status || UNKNOWN },
    { label: 'Model type', value: model.model_type || UNKNOWN },
    { label: 'Model category', value: model.model_category || UNKNOWN },
  ];

  const techFields = [
    { label: 'Parameter count', value: model.parameters },
    { label: 'Context window', value: model.context_window },
    { label: 'Input modalities', value: model.input_modalities },
    { label: 'Output modalities', value: model.output_modalities },
    { label: 'Supported languages', value: model.supported_languages },
    { label: 'Maximum output length', value: model.max_output_length },
    { label: 'Architecture', value: model.architecture },
  ];

  const perfFields = [
    { label: 'Inference speed', value: model.inference_speed },
    { label: 'Latency', value: model.latency },
    { label: 'Throughput', value: model.throughput },
    { label: 'Reasoning capabilities', value: model.reasoning_capabilities },
    { label: 'Coding capabilities', value: model.coding_capabilities },
    { label: 'Vision & multimodal', value: model.vision_multimodal_capabilities },
  ];

  const deployFields = [
    { label: 'GPU requirements', value: model.gpu_requirements },
    { label: 'VRAM requirements', value: model.vram_requirements },
    { label: 'API availability', value: model.api_available ? 'Yes' : 'Not publicly disclosed' },
    { label: 'Deployment', value: model.deployment },
    { label: 'Quantization options', value: model.quantization_options },
    { label: 'Estimated compute', value: model.compute_requirements },
  ];

  const commFields = [
    { label: 'Input pricing', value: model.input_pricing },
    { label: 'Output pricing', value: model.output_pricing },
    { label: 'Subscription plans', value: model.subscription_plans },
    { label: 'Enterprise availability', value: model.enterprise_available ? 'Yes' : 'Not publicly disclosed' },
    { label: 'License', value: model.license },
  ];

  const benchmarks = model.benchmark_scores && typeof model.benchmark_scores === 'object'
    ? Object.entries(model.benchmark_scores).map(([name, val]) => ({
        name,
        ...(typeof val === 'object' && val !== null ? val : { score: val, date: '' }),
      }))
    : [];

  return (
    <div className="aim-detail" role="dialog" aria-modal="true">
      <div className="aim-detail-backdrop" onClick={onClose} />
      <div className="aim-detail-panel">
        <div className="aim-detail-header">
          <button className="aim-btn ghost aim-detail-close" onClick={onClose}>
            <X size={20} />
          </button>
          <div className="aim-detail-source">
            {model.source_url ? (
              <a href={model.source_url} target="_blank" rel="noreferrer" className="aim-link">
                <Link size={14} /> Source: {model.source_url}
              </a>
            ) : (
              <span className="aim-muted">No source URL recorded</span>
            )}
            {model.is_official !== undefined && (
              <span className={`aim-source-tag ${model.is_official ? 'aim-source-official' : 'aim-source-thirdparty'}`}>
                {model.is_official ? 'Official specification' : 'Third-party / estimated'}
              </span>
            )}
          </div>
        </div>

        <div className="aim-detail-body">
          <div className="aim-detail-identity">
            <h2>{model.name}</h2>
            <div className="aim-detail-id-line">
              <span>{model.company}</span>
              <span>·</span>
              <span>{model.family}</span>
              <span>·</span>
              <span>v{model.version}</span>
            </div>
            <p className="aim-detail-id-desc">{model.release_date ? `Released ${model.release_date}` : 'Release date not publicly disclosed'}</p>
          </div>

          <section className="aim-detail-section">
            <h3>Model identity</h3>
            <div className="aim-field-grid">{fields.map((f) => aimField(f))}</div>
          </section>

          <section className="aim-detail-section">
            <h3>Technical specifications</h3>
            <div className="aim-field-grid">{techFields.map((f) => aimField(f))}</div>
          </section>

          <section className="aim-detail-section">
            <h3>Performance</h3>
            <div className="aim-field-grid">{perfFields.map((f) => aimField(f))}</div>
            {benchmarks.length > 0 && (
              <div className="aim-benchmarks">
                <h4>Benchmark scores</h4>
                <div className="aim-bench-list">
                  {benchmarks.map((b, i) => (
                    <div key={i} className="aim-bench-item">
                      <span className="aim-bench-name">{b.name}</span>
                      <span className="aim-bench-score">{b.score}</span>
                      {b.date && <span className="aim-bench-date">{b.date}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="aim-detail-section">
            <h3>Capacity & deployment</h3>
            <div className="aim-field-grid">{deployFields.map((f) => aimField(f))}</div>
          </section>

          <section className="aim-detail-section">
            <h3>Commercial information</h3>
            <div className="aim-field-grid">{commFields.map((f) => aimField(f))}</div>
          </section>

          <section className="aim-detail-section">
            <h3>Competitive comparison</h3>
            <div className="aim-empty">
              Select a competing model from the grid to add a side-by-side comparison here.
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function aimField({ label, value }) {
  const empty = !value || value === UNKNOWN || value === '';
  return (
    <div className="aim-field">
      <span className="aim-field-label">{label}</span>
      <span className={`aim-field-value ${empty ? 'aim-field-empty' : ''}`}>
        {empty ? UNKNOWN : value}
      </span>
    </div>
  );
}
