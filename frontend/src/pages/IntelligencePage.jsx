/**
 * Trending Intelligence page — main interactive section.
 * Shows intelligence events from external companies, NEXORA AI, MINTY-GPT.
 * Clicking an event opens a detail view with Hindsight Memory and BAND AI options.
 */

import { useEffect, useState } from 'react';
import {
  Bell, TrendingUp, ArrowUpRight, Filter, SortAsc, ChevronRight,
  ShieldCheck, ShieldAlert, Clock, Link, Globe, BookOpen, Cpu,
  Activity, BrainCircuit, Network, X, Search
} from 'lucide-react';
import { intelligenceApi } from '../services/api';
import './IntelligencePage.css';

const CATEGORIES = [
  'All events', 'External competitors', 'Our company', 'Demo company',
  'Models', 'Pricing', 'Research', 'Funding', 'Partnerships',
  'Infrastructure', 'Products',
];

const COMPANY_FILTERS = [
  'All companies', 'OpenAI', 'Google DeepMind', 'Anthropic',
  'Microsoft AI', 'Meta AI', 'NVIDIA', 'xAI', 'Mistral AI',
  'DeepSeek', 'Amazon AWS AI', 'NEXORA AI', 'MINTY-GPT'
];

export default function IntelligencePage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('All events');
  const [companyFilter, setCompanyFilter] = useState('All companies');
  const [sortBy, setSortBy] = useState('date');
  const [search, setSearch] = useState('');

  const load = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await intelligenceApi.list();

      // Backend returns events inside data.value
      const arr = Array.isArray(data)
        ? data
        : Array.isArray(data?.value)
          ? data.value
          : [];

      setEvents(arr);
    } catch (e) {
      setError(e.message || 'Failed to load intelligence events');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = events.filter((e) => {
    let catMatch = false;

    if (categoryFilter === 'All events') {
      catMatch = true;
    } else if (categoryFilter === 'External competitors') {
      catMatch = e.company !== 'NEXORA AI' && e.company !== 'MINTY-GPT';
    } else if (categoryFilter === 'Our company') {
      catMatch = e.company === 'NEXORA AI';
    } else if (categoryFilter === 'Demo company') {
      catMatch = e.company === 'MINTY-GPT' || e.demo_company_label === true;
    } else {
      catMatch =
        e.category === categoryFilter ||
        e.company === categoryFilter;
    }

    const compMatch =
      companyFilter === 'All companies' ||
      e.company === companyFilter;

    const searchText = search.toLowerCase();

    const searchMatch =
      !searchText ||
      (e.title || '').toLowerCase().includes(searchText) ||
      (e.company || '').toLowerCase().includes(searchText) ||
      (e.description || '').toLowerCase().includes(searchText);

    return catMatch && compMatch && searchMatch;
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'importance') {
      const rank = {
        critical: 4,
        high: 3,
        medium: 2,
        low: 1
      };

      return (
        (rank[b.strategic_importance] || 0) -
        (rank[a.strategic_importance] || 0)
      ) || (
        new Date(b.collection_date || 0) -
        new Date(a.collection_date || 0)
      );
    }

    return (
      new Date(b.collection_date || 0) -
      new Date(a.collection_date || 0)
    );
  });

  return (
    <div className="int-page">

      <header className="int-header">
        <div>
          <div className="int-eyebrow">TRENDING INTELLIGENCE</div>
          <h1>Competitive Intelligence Feed</h1>
          <p>
            Live intelligence from AI companies, research sources,
            NEXORA AI and MINTY-GPT (simulated demo company).
          </p>
        </div>

        <div className="int-actions">
          <button className="int-btn ghost" onClick={load}>
            <Activity size={16} /> Refresh
          </button>
        </div>
      </header>

      {error && <div className="int-empty">{error}</div>}

      <div className="int-toolbar">

        <div className="int-chip-group">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              className={`int-chip ${
                categoryFilter === c ? 'int-chip-active' : ''
              }`}
              onClick={() => setCategoryFilter(c)}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="int-chip-group int-chip-group-compact">
          {COMPANY_FILTERS.map((c) => (
            <button
              key={c}
              className={`int-chip ${
                companyFilter === c ? 'int-chip-active' : ''
              }`}
              onClick={() => setCompanyFilter(c)}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="int-sort-search">

          <div className="int-sort">
            <SortAsc size={14} />

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="int-select"
            >
              <option value="date">Sort by date</option>
              <option value="importance">
                Sort by strategic importance
              </option>
            </select>
          </div>

          <div className="int-search">
            <Search size={16} />

            <input
              type="text"
              placeholder="Search events..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="int-search-input"
            />
          </div>

        </div>
      </div>

      <div className="int-stats">

        <div className="int-stat">
          <div className="int-stat-value">{events.length}</div>
          <div className="int-stat-label">Total events</div>
        </div>

        <div className="int-stat">
          <div className="int-stat-value">
            {events.filter(e => e.company === 'NEXORA AI').length}
          </div>
          <div className="int-stat-label">NEXORA AI events</div>
        </div>

        <div className="int-stat">
          <div className="int-stat-value">
            {events.filter(
              e => e.company === 'MINTY-GPT' || e.demo_company_label
            ).length}
          </div>
          <div className="int-stat-label">MINTY-GPT (simulated)</div>
        </div>

        <div className="int-stat">
          <div className="int-stat-value">
            {events.filter(
              e => e.verification_status === 'verified'
            ).length}
          </div>
          <div className="int-stat-label">Verified</div>
        </div>

      </div>

      <div className="int-cards">

        {loading ? (
          [...Array(8)].map((_, i) => (
            <IntelCardSkeleton key={i} />
          ))
        ) : sorted.length === 0 ? (
          <div className="int-empty">
            No intelligence events match your filters.
          </div>
        ) : (
          sorted.map((e) => (
            <IntelCard
              key={e.id}
              event={e}
              onSelect={setSelected}
            />
          ))
        )}

      </div>

      {selected && (
        <EventDetail
          event={selected}
          onClose={() => setSelected(null)}
        />
      )}

    </div>
  );
}

function IntelCardSkeleton() {
  return (
    <div className="int-card int-card-skeleton">
      <div
        className="int-card-skeleton-bar"
        style={{ width: '40%', height: 10 }}
      />
      <div
        className="int-card-skeleton-bar"
        style={{ width: '70%', height: 14, marginTop: 10 }}
      />
      <div
        className="int-card-skeleton-bar"
        style={{ width: '90%', height: 12, marginTop: 8 }}
      />
      <div
        className="int-card-skeleton-bar"
        style={{ width: '60%', height: 10, marginTop: 10 }}
      />
    </div>
  );
}

const COMPANY_ICONS = {
  OpenAI: Globe,
  'Google DeepMind': Globe,
  Anthropic: BrainCircuit,
  'Microsoft AI': Activity,
  'Meta AI': BookOpen,
  NVIDIA: Cpu,
  xAI: Activity,
  'Mistral AI': BrainCircuit,
  DeepSeek: Activity,
  'Amazon AWS AI': Globe,
  'NEXORA AI': BrainCircuit,
  'MINTY-GPT': ShieldAlert,
};

function ChipIcon({ company }) {
  const Icon = COMPANY_ICONS[company] || Activity;
  const isDemo = company === 'MINTY-GPT';

  return (
    <div
      className={`int-card-avatar ${
        isDemo ? 'int-card-avatar-demo' : ''
      }`}
    >
      <Icon size={18} />
    </div>
  );
}

function IntelCard({ event, onSelect }) {
  const isDemo =
    event.company === 'MINTY-GPT' || event.demo_company_label;

  const verif = event.verification_status || 'unverified';
  const imp = event.strategic_importance || 'medium';

  return (
    <div
      className="int-card"
      onClick={() => onSelect(event)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) =>
        e.key === 'Enter' && onSelect(event)
      }
    >

      <div className="int-card-head">

        <ChipIcon company={event.company} />

        <div className="int-card-company">
          <div className="int-card-company-name">
            {event.company || 'Unknown company'}
          </div>

          {isDemo && (
            <span className="int-demo-badge">
              SIMULATED DEMO COMPANY
            </span>
          )}
        </div>

        <div className={`int-card-verif int-verif-${verif}`}>
          {verif}
        </div>

      </div>

      <div className="int-card-body">
        <span className="int-card-category">
          {event.category || 'General'}
        </span>

        <h3 className="int-card-title">
          {event.title || 'Untitled event'}
        </h3>

        <p className="int-card-desc">
          {event.description || 'No description available.'}
        </p>
      </div>

      <div className="int-card-foot">

        <div className="int-card-meta">
          <Clock size={12} />
          <span>
            {event.collection_date
              ? new Date(event.collection_date).toLocaleString()
              : 'Date unavailable'}
          </span>
        </div>

        <div className={`int-card-imp int-imp-${imp}`}>
          {imp}
        </div>

        <ChevronRight size={14} />

      </div>
    </div>
  );
}

function EventDetail({ event, onClose }) {
  const isDemo =
    event.company === 'MINTY-GPT' || event.demo_company_label;

  return (
    <div className="int-detail" role="dialog" aria-modal="true">

      <div
        className="int-detail-backdrop"
        onClick={onClose}
      />

      <div className="int-detail-panel">

        <div className="int-detail-header">

          <button
            className="int-btn ghost int-detail-close"
            onClick={onClose}
          >
            <X size={20} />
          </button>

          <div className="int-detail-meta">

            <span
              className={`int-detail-verif int-verif-${
                event.verification_status || 'unverified'
              }`}
            >
              {event.verification_status || 'unverified'}
            </span>

            <span className="int-detail-source">
              <Link size={12} />
              {event.source_url || 'No source'}
            </span>

            <span className="int-detail-time">
              <Clock size={12} />
              Collected{' '}
              {event.collection_date
                ? new Date(event.collection_date).toLocaleString()
                : 'Date unavailable'}
            </span>

          </div>
        </div>

        <div className="int-detail-body">

          <div className="int-detail-company">

            <ChipIcon company={event.company} />

            <div>
              <div className="int-detail-company-name">
                {event.company || 'Unknown company'}
              </div>

              {isDemo && (
                <span className="int-demo-badge">
                  SIMULATED DEMO COMPANY
                </span>
              )}
            </div>

          </div>

          <h2 className="int-detail-title">
            {event.title || 'Untitled event'}
          </h2>

          <span className="int-detail-category">
            {event.category || 'General'}
          </span>

          <p className="int-detail-desc">
            {event.description || 'No description available.'}
          </p>

          {event.evidence_snippet && (
            <div className="int-detail-evidence">
              <span>Evidence:</span>
              <blockquote>{event.evidence_snippet}</blockquote>
            </div>
          )}

          <p className="int-detail-impact">
            <strong>Impact on NEXORA AI:</strong>{' '}
            {event.impact_on_nexora || 'Not assessed'}
          </p>

        </div>

        <div className="int-detail-actions">

          <h3>Choose intelligence workflow</h3>

          <div className="int-workflow-options">

            <button
              className="int-workflow-btn"
              onClick={() => {
                onClose();
                window.dispatchEvent(
                  new CustomEvent('intel:hindsight', {
                    detail: event
                  })
                );
              }}
            >
              <BrainCircuit size={20} />

              <div>
                <div className="int-wf-title">
                  Hindsight Memory
                </div>
                <div className="int-wf-desc">
                  Retrieve historical competitor events and previous strategies
                </div>
              </div>

              <ChevronRight size={14} />
            </button>

            <button
              className="int-workflow-btn"
              onClick={() => {
                onClose();
                window.dispatchEvent(
                  new CustomEvent('intel:band', {
                    detail: event
                  })
                );
              }}
            >
              <Network size={20} />

              <div>
                <div className="int-wf-title">
                  BAND AI Agent Collaboration
                </div>
                <div className="int-wf-desc">
                  Multi-agent strategic analysis and recommendation
                </div>
              </div>

              <ChevronRight size={14} />
            </button>

          </div>
        </div>

      </div>
    </div>
  );
}