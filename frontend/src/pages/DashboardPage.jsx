/**
 * Dashboard overview — metrics computed from actual database data.
 */
import { useEffect, useState } from 'react';
import {
  LayoutDashboard, Building2, BrainCircuit, ShieldAlert, TrendingUp,
  Activity, Network, Clock, Users, Cpu, DollarSign, RefreshCw
} from 'lucide-react';
import { dashboardApi } from '../services/api';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await dashboardApi.stats();
      setStats(data);
    } catch (e) {
      setError(e.message || 'Failed to load dashboard stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="dash-page">
      <header className="dash-header">
        <div>
          <div className="dash-eyebrow">OVERVIEW</div>
          <h1>NEXORA AI Dashboard</h1>
          <p>Competitive intelligence overview computed from live database data.</p>
        </div>
        <button className="dash-btn ghost" onClick={load}>
          <RefreshCw size={16} /> Refresh
        </button>
      </header>

      {error && <div className="dash-empty">{error}</div>}

      <div className="dash-stats">
        <StatCard
          icon={Building2}
          label="AI Companies Monitored"
          value={stats?.companies_monitored ?? '--'}
          note="Distinct companies in intelligence feed"
          color="stat-company"
        />
        <StatCard
          icon={Activity}
          label="Latest Intelligence Events"
          value={stats?.latest_events ?? '--'}
          note="Total events collected"
          color="stat-events"
        />
        <StatCard
          icon={BrainCircuit}
          label="AI Models Tracked"
          value={stats?.ai_models_tracked ?? '--'}
          note="Models in database"
          color="stat-models"
        />
        <StatCard
          icon={LayoutDashboard}
          label="Company Profile Completion"
          value={stats?.profile_completion !== undefined ? stats.profile_completion : '--'}
          note="NEXORA AI profile sections filled"
          color="stat-profile"
        />
        <StatCard
          icon={ShieldAlert}
          label="MINTY-GPT Updates"
          value={stats?.minty_updates ?? '--'}
          note="Demo company update history"
          color="stat-minty"
        />
        <StatCard
          icon={Clock}
          label="Last Updated"
          value={stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Never'}
          note="Most recent intelligence collection"
          color="stat-time"
        />
      </div>

      <div className="dash-grid">
        <IntegrationPanel
          title="Hindsight Memory"
          icon={BrainCircuit}
          status={stats?.hindsight_status}
          description="Historical learning from past competitor events and decisions."
        />
        <IntegrationPanel
          title="BAND AI Agents"
          icon={Network}
          status={stats?.band_status}
          description="Multi-agent collaboration for strategic recommendations."
        />
        <MetricPanel
          title="Recent Strategic Recommendations"
          icon={Activity}
          value={stats?.recent_recommendations ?? '--'}
          note="Strategy reports generated"
        />
        <MetricPanel
          title="Competitive Threats"
          icon={ShieldAlert}
          value={stats?.threats ?? '--'}
          note="High/critical importance events"
        />
        <MetricPanel
          title="Market Opportunities"
          icon={TrendingUp}
          value={stats?.opportunities ?? '--'}
          note="Events framed as opportunities"
        />
      </div>

      <div className="dash-note">
        All metrics are computed from the backend database. No statistics are hardcoded or fabricated.
        Integration status reflects actual configuration (Hindsight / BAND AI environment variables).
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, note, color }) {
  return (
    <div className={`dash-stat ${color}`}>
      <div className="dash-stat-top">
        <div className="dash-stat-icon"><Icon size={18} /></div>
        <span className="dash-stat-label-small">{label}</span>
      </div>
      <div className="dash-stat-value">{value}</div>
      <div className="dash-stat-note">{note}</div>
    </div>
  );
}

function IntegrationPanel({ title, icon: Icon, status, description }) {
  const configured = status === 'configured';
  return (
    <div className="dash-panel">
      <div className="dash-panel-head">
        <div className="dash-panel-icon"><Icon size={18} /></div>
        <div>
          <div className="dash-panel-title">{title}</div>
          <div className="dash-panel-desc">{description}</div>
        </div>
        <span className={`dash-status ${configured ? 'dash-status-on' : 'dash-status-off'}`}>
          {configured ? 'Configured' : 'Not configured'}
        </span>
      </div>
      <div className="dash-panel-body">
        {configured
          ? 'Integration is connected and ready.'
          : `Set ${title.toLowerCase()} API credentials in backend/.env to enable.`}
      </div>
    </div>
  );
}

function MetricPanel({ title, icon: Icon, value, note }) {
  return (
    <div className="dash-panel">
      <div className="dash-panel-head">
        <div className="dash-panel-icon"><Icon size={18} /></div>
        <div>
          <div className="dash-panel-title">{title}</div>
          <div className="dash-panel-desc">{note}</div>
        </div>
      </div>
      <div className="dash-panel-body">
        <div className="dash-metric-value">{value}</div>
      </div>
    </div>
  );
}
