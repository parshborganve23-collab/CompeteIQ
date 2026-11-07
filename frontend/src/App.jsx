
import { useState, useEffect, useRef } from 'react';

import {
  LayoutDashboard,
  Building2,
  BrainCircuit,
  Package,
  Server,
  Target,
  Settings,
  Bell,
  Search,
  Plus,
  TrendingUp,
  Activity,
  Cpu,
  ArrowUpRight,
  Menu,
  Network,
  ChevronRight,
  Sparkles,
  ChevronDown,
  Swords
} from 'lucide-react';

import DashboardPage from './pages/DashboardPage';
import CompanyProfile from './company/CompanyProfile';
import AIModelsPage from './pages/AIModelsPage';
import IntelligencePage from './pages/IntelligencePage';
import DemoCompanyPage from './pages/DemoCompanyPage';
import HindsightPage from './pages/HindsightPage';
import BandPage from './pages/BandPage';
import UnifiedWorkflowsPage from './pages/UnifiedWorkflowsPage';
import AnimatedWorkflowPage from './pages/AnimatedWorkflowPage';
import StrategicReportPage from './pages/StrategicReportPage';
import CompetitorBattlePage from './pages/CompetitorBattlePage';

import { useCompany } from './company/CompanyContext';

import './App.css';

const initialModels = [
  {
    name: 'NEXORA-LLM',
    type: 'Large Language Model',
    status: 'Active',
    capability: 'Text & Reasoning'
  },
  {
    name: 'NEXORA-Vision',
    type: 'Vision Model',
    status: 'Development',
    capability: 'Image Understanding'
  },
  {
    name: 'NEXORA-Code',
    type: 'Code Model',
    status: 'Planned',
    capability: 'Code Generation'
  }
];

const navigation = [
  { label: 'Overview', icon: LayoutDashboard },
  { label: 'Company Profile', icon: Building2 },
  { label: 'AI Models', icon: BrainCircuit },
  { label: 'Trending Intelligence', icon: Activity },
  { label: 'Demo Company (MINTY-GPT)', icon: Network },
  { label: 'Products & Services', icon: Package },
  { label: 'Infrastructure', icon: Server },
  { label: 'Competitor Battle', icon: Swords },
  { label: 'Business Strategy', icon: Target }
];

export default function App() {
  const {
    data: companyData,
    backendReady,
    backendError,
    loading: companyLoading
  } = useCompany();

  const [active, setActive] = useState('Overview');

  const [models, setModels] = useState(initialModels);

  const [showModelForm, setShowModelForm] = useState(false);

  const [newModel, setNewModel] = useState({
    name: '',
    type: '',
    capability: ''
  });

  const [companyMenuOpen, setCompanyMenuOpen] = useState(false);

  // Workflow modal state
  const [workflowEvent, setWorkflowEvent] = useState(null);
  const [showWorkflow, setShowWorkflow] = useState(false);

  // Strategic report modal state
  const [showReport, setShowReport] = useState(false);
  const [reportId, setReportId] = useState(null);

  const workflowRef = useRef();

  function addModel(e) {
    e.preventDefault();

    if (!newModel.name.trim()) return;

    setModels([
      ...models,
      {
        ...newModel,
        status: 'Planned'
      }
    ]);

    setNewModel({
      name: '',
      type: '',
      capability: ''
    });

    setShowModelForm(false);
  }

  const Stat = ({ title, value, icon: Icon, note }) => (
    <div className="stat-card">
      <div className="stat-top">
        <span>{title}</span>
        <Icon size={19} />
      </div>

      <div className="stat-value">{value}</div>

      <div className="stat-note">{note}</div>
    </div>
  );

  // Listen for workflow triggers from the intelligence feed
  useEffect(() => {
    const onHindsight = (e) => {
      setWorkflowEvent(e.detail);
      setShowWorkflow(true);
    };

    const onBand = (e) => {
      setWorkflowEvent(e.detail);
      setShowWorkflow(true);
    };

    window.addEventListener('intel:hindsight', onHindsight);
    window.addEventListener('intel:band', onBand);

    return () => {
      window.removeEventListener('intel:hindsight', onHindsight);
      window.removeEventListener('intel:band', onBand);
    };
  }, []);

  const handleWorkflowComplete = (result) => {
    setShowWorkflow(false);

    if (result.data && result.data.recommendation_id) {
      setReportId(result.data.recommendation_id);
      setShowReport(true);
    } else if (result.data && result.data.memory_id) {
      setReportId(null);
      setShowReport(true);
    }
  };

  const companyName =
    companyData?.overview?.companyName || 'NEXORA AI';

  // Pages handled by real components
  const componentPages = [
    'Overview',
    'Company Profile',
    'AI Models',
    'Trending Intelligence',
    'Demo Company (MINTY-GPT)',
    'Competitor Battle',
    'Hindsight',
    'BAND AI',
    'Unified Workflows'
  ];

  return (
    <div className="app-shell">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            <Activity size={22} />
          </div>

          <div>
            <strong>CompeteIQ</strong>
            <small>STRATEGY INTELLIGENCE</small>
          </div>
        </div>

        <div className="side-label">
          WORKSPACE
        </div>

        <div
          className="company-switch"
          onClick={() => setCompanyMenuOpen(!companyMenuOpen)}
          onKeyDown={(e) =>
            e.key === 'Enter' &&
            setCompanyMenuOpen(!companyMenuOpen)
          }
          role="button"
          tabIndex={0}
        >
          <div className="company-avatar">
            N
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <strong>{companyName}</strong>
            <small>Our Company</small>
          </div>

          <ChevronDown
            size={14}
            style={{
              transform: companyMenuOpen
                ? 'rotate(180deg)'
                : 'rotate(0deg)'
            }}
          />
        </div>

        {companyMenuOpen && (
          <div className="company-menu">

            <div
              className="menu-item"
              onClick={() => {
                setCompanyMenuOpen(false);
                setActive('Company Profile');
              }}
            >
              <Building2 size={14} />
              Company Profile
            </div>

            <div className="menu-divider" />

            <div
              className="menu-item"
              onClick={() => {
                setCompanyMenuOpen(false);
                setActive('Overview');
              }}
            >
              <LayoutDashboard size={14} />
              Back to Overview
            </div>

            {backendError && (
              <div
                className="menu-item menu-error"
                style={{
                  color: '#f5d76e',
                  fontSize: '12px',
                  padding: '8px 12px'
                }}
              >
                ⚠ {backendError}
              </div>
            )}

          </div>
        )}

        <div className="side-label">
          MAIN MENU
        </div>

        <nav>
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${
                active === label ? 'selected' : ''
              }`}
              onClick={() => setActive(label)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        {/* AI PLATFORMS */}
        <div className="side-label platform-label">
          AI PLATFORMS
        </div>

        <button
          className={`nav-item ${
            active === 'Hindsight' ? 'selected' : ''
          }`}
          onClick={() => setActive('Hindsight')}
        >
          <BrainCircuit size={18} />
          <span>Hindsight Memory</span>
        </button>

        <button
          className={`nav-item ${
            active === 'BAND AI' ? 'selected' : ''
          }`}
          onClick={() => setActive('BAND AI')}
        >
          <Network size={18} />
          <span>BAND AI Agents</span>
        </button>

        <button
          className={`nav-item ${
            active === 'Unified Workflows' ? 'selected' : ''
          }`}
          onClick={() => setActive('Unified Workflows')}
        >
          <Activity size={18} />
          <span>Unified Workflows</span>
        </button>

        {/* SIDEBAR BOTTOM */}
        <div className="sidebar-bottom">
          <div className="profile-avatar">
            N
          </div>

          <div>
            <strong>Admin Workspace</strong>
            <small>Company Administrator</small>
          </div>

          <Settings size={17} />
        </div>

      </aside>

      {/* MAIN CONTENT */}
      <main className="main-area">

        {/* TOP BAR */}
        <header className="topbar">

          <div>
            <div className="breadcrumb">
              Workspace / <strong>{active}</strong>
            </div>

            <div className="mobile-brand">
              CompeteIQ
            </div>
          </div>

          <div className="top-actions">

            <span className="live-indicator">
              <i />
              System workspace
            </span>

            <button className="icon-button">
              <Search size={19} />
            </button>

            <button className="icon-button">
              <Bell size={19} />
            </button>

            <div className="profile-avatar">
              N
            </div>

          </div>
        </header>

        {/* PAGE CONTENT */}
        <section className="page-content">

          {active === 'Overview' && (
            <DashboardPage />
          )}

          {active === 'Company Profile' && (
            <CompanyProfile />
          )}

          {active === 'AI Models' && (
            <AIModelsPage />
          )}

          {active === 'Trending Intelligence' && (
            <IntelligencePage />
          )}

          {active === 'Demo Company (MINTY-GPT)' && (
            <DemoCompanyPage />
          )}

          {/* NEW COMPETITOR BATTLE PAGE */}
          {active === 'Competitor Battle' && (
            <CompetitorBattlePage />
          )}

          {active === 'Hindsight' && (
            <HindsightPage />
          )}

          {active === 'BAND AI' && (
            <BandPage />
          )}

          {active === 'Unified Workflows' && (
            <UnifiedWorkflowsPage />
          )}

          {/* PLACEHOLDER FOR OTHER MODULES */}
          {!componentPages.includes(active) && (
            <div className="page-heading">
              <div className="eyebrow">
                COMPETIQ WORKSPACE
              </div>

              <h1>{active}</h1>

              <p>
                This module connects to the corresponding backend API.
                Configure Hindsight / BAND AI credentials in backend/.env
                to enable real integration.
              </p>
            </div>
          )}

        </section>
      </main>

      {/* ANIMATED WORKFLOW MODAL */}
      {showWorkflow && workflowEvent && (
        <div
          className="modal-overlay"
          onClick={() => setShowWorkflow(false)}
        >
          <div
            className="modal-panel"
            onClick={(e) => e.stopPropagation()}
          >
            <AnimatedWorkflowPage
              event={workflowEvent}
              onClose={() => setShowWorkflow(false)}
              onComplete={handleWorkflowComplete}
            />
          </div>
        </div>
      )}

      {/* STRATEGIC REPORT MODAL */}
      {showReport && (
        <div
          className="modal-overlay"
          onClick={() => setShowReport(false)}
        >
          <div
            className="modal-panel"
            onClick={(e) => e.stopPropagation()}
          >
            <StrategicReportPage
              recommendationId={reportId}
              onClose={() => setShowReport(false)}
            />
          </div>
        </div>
      )}

    </div>
  );
}
