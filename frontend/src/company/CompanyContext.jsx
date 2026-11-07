import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  SECTIONS,
  SAMPLE,
  PLATFORM_NAME,
  DEMO_COMPETITOR_NOTE,
  completion,
} from './companySchema';
import { companyApi } from '../services/api';

const CompanyContext = createContext(null);

// Company identity: NEXORA AI is OUR company. CompeteIQ is the platform.
const COMPANY_NAME = 'NEXORA AI';

const blank = () => ({ sample: false, data: { overview: { companyName: COMPANY_NAME } } });

function describeSection(section, data = {}) {
  const lines = [];
  section.groups.forEach((g) => {
    if (g.kind === 'fields') {
      g.fields.forEach((f) => {
        if (f.type === 'logo') return;
        const v = data[f.key];
        if (v !== undefined && v !== null && String(v).trim() !== '') lines.push(`${f.label}: ${v}`);
      });
    } else {
      (data[g.key] || []).forEach((item) => {
        const parts = g.fields
          .map((f) => (item[f.key] ? `${f.label}: ${item[f.key]}` : null))
          .filter(Boolean);
        if (parts.length) lines.push(`${g.label} | ${parts.join('; ')}`);
      });
    }
  });
  return lines;
}

export function CompanyProvider({ children }) {
  const [state, setState] = useState(blank());
  const [loading, setLoading] = useState(true);
  const [backendReady, setBackendReady] = useState(null); // null = checking, true/false = result
  const [backendError, setBackendError] = useState(null);

  // Load: try backend first, fall back to localStorage
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const profile = await companyApi.getProfile();
        if (!cancelled && profile && profile.sections) {
          setBackendReady(true);
          setBackendError(null);
          const data = {};
          profile.sections.forEach((s) => {
            data[s.section_id] = s.data || {};
          });
          if (profile.name) data.overview = data.overview || {};
          data.overview.companyName = profile.name || COMPANY_NAME;
          data.overview.description = profile.description || data.overview.description || '';
          data.overview.website = profile.website || data.overview.website || '';
          data.overview.contactEmail = profile.contact_email || data.overview.contactEmail || '';
          setState({ sample: false, data });
        } else if (!cancelled) {
          setBackendReady(false);
          loadFromLocalStorage();
        }
      } catch {
        if (!cancelled) {
          setBackendReady(false);
          setBackendError('Unable to reach backend. Using local storage.');
          loadFromLocalStorage();
        }
      }
      if (!cancelled) setLoading(false);
    })();
    return () => { cancelled = true; };
  }, []);

  function loadFromLocalStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setState(JSON.parse(raw));
      else setState(blank());
    } catch {
      setState(blank());
    }
  }

  const STORAGE_KEY = 'competeiq.company.v1';

  useEffect(() => {
    // Persist to localStorage as a mirror (only after initial load)
    if (!loading) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      } catch { /* ignore quota/privacy errors */ }
    }
  }, [state, loading]);

  const saveSection = useCallback(async (id, values) => {
    setState((s) => ({ ...s, data: { ...s.data, [id]: values } }));
    // Persist to backend
    try {
      const section = SECTIONS.find((s) => s.id === id);
      await companyApi.saveSection(id, {
        section_id: id,
        title: section ? section.title : id,
        data: values,
        is_sample: state.sample,
      });
    } catch (err) {
      // Surface save errors so they aren't silent
      setBackendError(`Failed to save ${section?.title || id} to backend. Changes saved locally only.`);
    }
  }, [state.sample]);

  const loadSample = useCallback(() => setState({ sample: true, data: { ...blank().data, ...SAMPLE } }), []);
  const clearAll = useCallback(() => setState(blank()), []);

  const completeness = useMemo(() => {
    const bySection = {};
    SECTIONS.forEach((sec) => {
      bySection[sec.id] = completion(sec, state.data[sec.id] || {});
    });
    const overall = Math.round(
      SECTIONS.reduce((sum, sec) => sum + bySection[sec.id].pct, 0) / SECTIONS.length
    );
    return { overall, bySection };
  }, [state.data]);

  const getAgentContext = useCallback(() => {
    const profile = {};
    SECTIONS.forEach((sec) => {
      const lines = describeSection(sec, state.data[sec.id] || {});
      if (lines.length) profile[sec.title] = lines;
    });
    const header = [
      `Company and platform: ${state.data.overview?.companyName || COMPANY_NAME}`,
      state.sample ? 'Warning: profile contains sample placeholder data.' : null,
      DEMO_COMPETITOR_NOTE,
      'External competitors (OpenAI, Google, Anthropic, Microsoft, Meta, NVIDIA) are not part of this profile.',
      `Profile completeness: ${completeness.overall}%`,
    ].filter(Boolean);
    const body = Object.entries(profile).map(([title, lines]) => `## ${title}\n${lines.join('\n')}`);
    return {
      company: state.data.overview?.companyName || COMPANY_NAME,
      isSampleData: state.sample,
      completeness,
      profile,
      promptText: [...header, '', ...body].join('\n'),
    };
  }, [state, completeness]);

  const value = useMemo(
    () => ({
      data: state.data,
      isSample: state.sample,
      completeness,
      saveSection,
      loadSample,
      clearAll,
      getAgentContext,
      backendReady,
      backendError,
      loading,
    }),
    [state, completeness, saveSection, loadSample, clearAll, getAgentContext, backendReady, backendError, loading]
  );

  return <CompanyContext.Provider value={value}>{children}</CompanyContext.Provider>;
}

export function useCompany() {
  const ctx = useContext(CompanyContext);
  if (!ctx) throw new Error('useCompany must be used inside <CompanyProvider>');
  return ctx;
}
