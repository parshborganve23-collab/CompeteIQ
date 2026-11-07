import { useEffect, useRef, useState } from 'react';
import { useCompany } from './CompanyContext';
import {
  SECTIONS,
  CONCEPT,
  DEMO_COMPETITOR_NOTE,
  PLATFORM_NAME,
} from './companySchema';
import './CompanyProfile.css';

const uid = () =>
  globalThis.crypto?.randomUUID ? globalThis.crypto.randomUUID() : String(Date.now() + Math.random());

/* ---------- small pieces ---------- */

function Ring({ pct, size = 38, stroke = 3.5, showLabel = false }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <svg className="ciq-ring" width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-label={`${pct}% complete`}>
      <circle className="ciq-ring-track" cx={size / 2} cy={size / 2} r={r} strokeWidth={stroke} fill="none" />
      <circle
        className="ciq-ring-bar"
        cx={size / 2}
        cy={size / 2}
        r={r}
        strokeWidth={stroke}
        fill="none"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - pct / 100)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
      {showLabel && (
        <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" className="ciq-ring-text">
          {pct}%
        </text>
      )}
    </svg>
  );
}

function Field({ f, value, onChange }) {
  const id = `f-${f.key}`;
  const common = {
    id,
    value: value ?? '',
    placeholder: f.placeholder || '',
    onChange: (e) => onChange(e.target.value),
  };
  let input;
  if (f.type === 'area') input = <textarea rows={3} {...common} />;
  else if (f.type === 'select')
    input = (
      <select {...common}>
        <option value="">Select</option>
        {f.options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    );
  else if (f.type === 'logo')
    input = (
      <div className="ciq-logo-input">
        {value ? <img src={value} alt="Company logo" /> : <span className="ciq-logo-empty">No logo</span>}
        <label className="ciq-btn ghost">
          Upload logo
          <input
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              if (file.size > 600 * 1024) return alert('Choose an image under 600 KB.');
              const rd = new FileReader();
              rd.onload = () => onChange(rd.result);
              rd.readAsDataURL(file);
            }}
          />
        </label>
        {value && (
          <button type="button" className="ciq-btn ghost" onClick={() => onChange('')}>
            Remove
          </button>
        )}
      </div>
    );
  else input = <input type={f.type === 'text' ? 'text' : f.type} {...common} />;

  return (
    <div className={`ciq-field ${f.wide ? 'wide' : ''}`}>
      <label htmlFor={id}>
        {f.label}
        {f.optional && <em> (optional)</em>}
      </label>
      {input}
    </div>
  );
}

/* ---------- summary (read) view ---------- */

function Value({ f, v }) {
  if (f.type === 'logo') return v ? <img className="ciq-logo-sm" src={v} alt="Company logo" /> : <span className="ciq-empty">Not added yet</span>;
  if (!v && v !== 0) return <span className="ciq-empty">Not added yet</span>;
  if (f.type === 'url') return <a href={v} target="_blank" rel="noreferrer">{v}</a>;
  if (f.type === 'email') return <a href={`mailto:${v}`}>{v}</a>;
  return <span className="ciq-val">{v}</span>;
}

function SectionView({ section, data = {}, onEdit }) {
  return (
    <div className="ciq-view">
      {section.groups.map((g, gi) =>
        g.kind === 'fields' ? (
          <div className="ciq-cards" key={gi}>
            {g.fields.map((f) => (
              <div className={`ciq-card ${f.wide ? 'wide' : ''}`} key={f.key}>
                <div className="ciq-card-label">{f.label}</div>
                <Value f={f} v={data[f.key]} />
              </div>
            ))}
          </div>
        ) : (
          <div key={g.key} className="ciq-listgroup">
            <h4>{g.label}</h4>
            {(data[g.key] || []).length === 0 ? (
              <button className="ciq-emptybox" onClick={onEdit}>
                No {g.label.toLowerCase()} yet. Add your first {g.itemName}.
              </button>
            ) : (
              <div className="ciq-cards">
                {data[g.key].map((item) => (
                  <div className="ciq-card entry" key={item.id}>
                    <div className="ciq-card-title">{item[g.titleKey] || `Untitled ${g.itemName}`}</div>
                    {g.fields
                      .filter((f) => f.key !== g.titleKey)
                      .map((f) =>
                        item[f.key] ? (
                          <div className="ciq-kv" key={f.key}>
                            <span>{f.label}</span>
                            <p>{item[f.key]}</p>
                          </div>
                        ) : null
                      )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )
      )}
    </div>
  );
}

/* ---------- editor ---------- */

function SectionEditor({ section, initial = {}, onSave, onCancel }) {
  const [draft, setDraft] = useState(() => JSON.parse(JSON.stringify(initial)));
  const setField = (k, v) => setDraft((d) => ({ ...d, [k]: v }));
  const items = (k) => draft[k] || [];
  const setItems = (k, arr) => setDraft((d) => ({ ...d, [k]: arr }));

  return (
    <form
      className="ciq-edit"
      onSubmit={(e) => {
        e.preventDefault();
        // Drop list entries the user left completely blank.
        const cleaned = { ...draft };
        section.groups.forEach((g) => {
          if (g.kind === 'list')
            cleaned[g.key] = items(g.key).filter((it) => g.fields.some((f) => String(it[f.key] ?? '').trim()));
        });
        onSave(cleaned);
      }}
    >
      {section.groups.map((g, gi) =>
        g.kind === 'fields' ? (
          <div className="ciq-grid" key={gi}>
            {g.fields.map((f) => (
              <Field key={f.key} f={f} value={draft[f.key]} onChange={(v) => setField(f.key, v)} />
            ))}
          </div>
        ) : (
          <fieldset className="ciq-listedit" key={g.key}>
            <legend>{g.label}</legend>
            {items(g.key).map((item, idx) => (
              <div className="ciq-entryform" key={item.id}>
                <div className="ciq-entryhead">
                  <span>
                    {g.itemName.charAt(0).toUpperCase() + g.itemName.slice(1)} {idx + 1}
                  </span>
                  <button
                    type="button"
                    className="ciq-btn danger"
                    onClick={() => setItems(g.key, items(g.key).filter((x) => x.id !== item.id))}
                  >
                    Delete
                  </button>
                </div>
                <div className="ciq-grid">
                  {g.fields.map((f) => (
                    <Field
                      key={f.key}
                      f={{ ...f, key: `${item.id}-${f.key}` }}
                      value={item[f.key]}
                      onChange={(v) =>
                        setItems(g.key, items(g.key).map((x) => (x.id === item.id ? { ...x, [f.key]: v } : x)))
                      }
                    />
                  ))}
                </div>
              </div>
            ))}
            <button type="button" className="ciq-btn ghost" onClick={() => setItems(g.key, [...items(g.key), { id: uid() }])}>
              Add {g.itemName}
            </button>
          </fieldset>
        )
      )}
      <div className="ciq-actions">
        <button type="submit" className="ciq-btn primary">Save changes</button>
        <button type="button" className="ciq-btn ghost" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}

/* ---------- page ---------- */

export default function CompanyProfile() {
  const { data, isSample, completeness, saveSection, loadSample, clearAll, getAgentContext } = useCompany();
  const [activeId, setActiveId] = useState(SECTIONS[0].id);
  const [editing, setEditing] = useState(false);
  const [toast, setToast] = useState('');
  const [showAgent, setShowAgent] = useState(false);
  const timer = useRef();

  const section = SECTIONS.find((s) => s.id === activeId);
  const overview = data.overview || {};
  const name = overview.companyName || PLATFORM_NAME;

  useEffect(() => () => clearTimeout(timer.current), []);
  const flash = (msg) => {
    setToast(msg);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setToast(''), 2400);
  };
  const go = (id) => {
    setActiveId(id);
    setEditing(false);
  };

  return (
    <div className="ciq-profile">
      <header className="ciq-hero">
        <div className="ciq-hero-id">
          {overview.logo ? (
            <img className="ciq-logo" src={overview.logo} alt={`${name} logo`} />
          ) : (
            <div className="ciq-logo mono" aria-hidden="true">{name.charAt(0)}</div>
          )}
          <div>
            <h2>{name}</h2>
            <p className="ciq-concept">{CONCEPT}</p>
          </div>
        </div>
        <div className="ciq-hero-side">
          <Ring pct={completeness.overall} size={84} stroke={6} showLabel />
          <span className="ciq-hero-cap">Profile complete</span>
        </div>
        <div className="ciq-chips">
          <span className="ciq-chip sim">{DEMO_COMPETITOR_NOTE}</span>
          {isSample && <span className="ciq-chip warn">Sample data loaded. Replace with real information.</span>}
        </div>
        <div className="ciq-toolbar">
          <button className="ciq-btn ghost" onClick={() => setShowAgent((v) => !v)}>
            {showAgent ? 'Hide' : 'Preview'} what the agents see
          </button>
          <button
            className="ciq-btn ghost"
            onClick={() => {
              if (window.confirm('Load clearly marked sample entries? This replaces your current profile.')) {
                loadSample();
                flash('Sample data loaded');
              }
            }}
          >
            Load sample data
          </button>
          <button
            className="ciq-btn ghost"
            onClick={() => {
              if (window.confirm('Clear the whole company profile?')) {
                clearAll();
                setEditing(false);
                flash('Profile cleared');
              }
            }}
          >
            Clear profile
          </button>
        </div>
      </header>

      {showAgent && (
        <section className="ciq-agentbox">
          <h3>Context shared with Competitive Intelligence agents</h3>
          <p>
            Agents compare external competitor developments (OpenAI, Google, Anthropic, Microsoft, Meta, NVIDIA and
            others) against this profile. MINTY-GPT stays a separate simulated competitor.
          </p>
          <pre>{getAgentContext().promptText}</pre>
        </section>
      )}

      <div className="ciq-body">
        <nav className="ciq-tabs" role="tablist" aria-label="Company information sections">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              role="tab"
              aria-selected={s.id === activeId}
              className={`ciq-tab ${s.id === activeId ? 'on' : ''}`}
              onClick={() => go(s.id)}
            >
              <Ring pct={completeness.bySection[s.id].pct} size={26} stroke={3} />
              <span>{s.title}</span>
            </button>
          ))}
        </nav>

        <main className="ciq-panel" key={activeId}>
          <div className="ciq-panelhead">
            <div>
              <h3>{section.title}</h3>
              <p>{section.blurb}</p>
              <span className="ciq-progress">
                {completeness.bySection[section.id].done} of {completeness.bySection[section.id].total} items filled
              </span>
              <div className="ciq-bar"><i style={{ width: `${completeness.bySection[section.id].pct}%` }} /></div>
            </div>
            {!editing && (
              <button className="ciq-btn primary" onClick={() => setEditing(true)}>
                Edit section
              </button>
            )}
          </div>

          {editing ? (
            <SectionEditor
              section={section}
              initial={data[section.id]}
              onCancel={() => setEditing(false)}
              onSave={(values) => {
                saveSection(section.id, values);
                setEditing(false);
                flash(`${section.title} saved`);
              }}
            />
          ) : (
            <SectionView section={section} data={data[section.id]} onEdit={() => setEditing(true)} />
          )}
        </main>
      </div>

      <div className={`ciq-toast ${toast ? 'show' : ''}`} role="status">{toast}</div>
    </div>
  );
}