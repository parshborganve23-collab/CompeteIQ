// CompeteIQ company information schema.
// Every section is data-driven: add a field here and the form, the summary
// cards, the completion rings and the agent context all pick it up.

export const PLATFORM_NAME = 'CompeteIQ';

export const CONCEPT =
  'CompeteIQ is an AI-powered competitive intelligence company and platform that continuously monitors competitors, learns from historical events using Hindsight memory, and coordinates specialized AI agents through BAND AI to generate strategic business recommendations.';

export const DEMO_COMPETITOR_NOTE =
  'MINTY-GPT is a simulated company used for demonstration only. It is not a real company.';

const t = (key, label, extra = {}) => ({ key, label, type: 'text', ...extra });
const a = (key, label, extra = {}) => ({ key, label, type: 'area', ...extra });
const d = (key, label, extra = {}) => ({ key, label, type: 'date', ...extra });
const n = (key, label, extra = {}) => ({ key, label, type: 'number', ...extra });
const s = (key, label, options, extra = {}) => ({ key, label, type: 'select', options, ...extra });

const STATUS = ['Idea', 'In development', 'Beta', 'Live', 'Deprecated'];

export const SECTIONS = [
  {
    id: 'overview',
    title: 'Company overview',
    blurb: 'Who CompeteIQ is and what it stands for.',
    groups: [
      {
        kind: 'fields',
        fields: [
          t('companyName', 'Company name'),
          { key: 'logo', label: 'Company logo', type: 'logo' },
          a('description', 'Company description', { wide: true }),
          a('mission', 'Mission', { wide: true }),
          a('vision', 'Vision', { wide: true }),
          d('founded', 'Founded date'),
          t('headquarters', 'Headquarters'),
          t('website', 'Website', { placeholder: 'https://' }),
          { key: 'contactEmail', label: 'Contact email', type: 'email' },
        ],
      },
    ],
  },
  {
    id: 'business',
    title: 'Business information',
    blurb: 'Industry, model, size and stage.',
    groups: [
      {
        kind: 'fields',
        fields: [
          t('industry', 'Industry'),
          s('businessModel', 'Business model', ['B2B', 'B2C', 'B2B2C', 'Platform / SaaS', 'Marketplace', 'Other']),
          s('companySize', 'Company size', ['1-10', '11-50', '51-200', '201-1,000', '1,000+']),
          n('employees', 'Number of employees'),
          t('regions', 'Operating regions'),
          t('targetMarkets', 'Target markets'),
          t('revenue', 'Annual revenue', { optional: true, placeholder: 'Optional' }),
          s('stage', 'Business stage', ['Idea', 'Prototype / MVP', 'Early traction', 'Growth', 'Scale', 'Mature']),
        ],
      },
    ],
  },
  {
    id: 'products',
    title: 'Products and services',
    blurb: 'Everything CompeteIQ sells or plans to sell.',
    groups: [
      {
        kind: 'list',
        key: 'products',
        label: 'Products and services',
        itemName: 'product',
        titleKey: 'name',
        fields: [
          t('name', 'Product name'),
          t('category', 'Product category'),
          a('description', 'Description', { wide: true }),
          a('features', 'Main features', { wide: true }),
          t('customers', 'Target customers'),
          s('status', 'Product status', STATUS),
          d('launchDate', 'Launch date'),
          a('roadmap', 'Roadmap', { wide: true }),
        ],
      },
    ],
  },
  {
    id: 'tech',
    title: 'AI and technology',
    blurb: 'Models, integrations and the stack behind them.',
    groups: [
      {
        kind: 'list',
        key: 'aiModels',
        label: 'AI models',
        itemName: 'AI model',
        titleKey: 'name',
        fields: [
          t('name', 'Model name'),
          a('capabilities', 'Model capabilities', { wide: true }),
          s('status', 'Development status', STATUS),
        ],
      },
      {
        kind: 'list',
        key: 'integrations',
        label: 'APIs and integrations',
        itemName: 'API or integration',
        titleKey: 'name',
        fields: [
          t('name', 'Name'),
          s('kind', 'Type', ['API', 'Integration', 'SDK', 'Webhook', 'Other']),
          a('notes', 'Notes', { wide: true }),
        ],
      },
      {
        kind: 'fields',
        fields: [
          a('stack', 'Technology stack', { wide: true }),
          a('research', 'AI research', { wide: true }),
          s('devStatus', 'Overall development status', STATUS),
        ],
      },
    ],
  },
  {
    id: 'pricing',
    title: 'Pricing and revenue',
    blurb: 'How CompeteIQ charges and earns.',
    groups: [
      {
        kind: 'list',
        key: 'plans',
        label: 'Pricing plans',
        itemName: 'pricing plan',
        titleKey: 'name',
        fields: [
          t('name', 'Plan name'),
          t('price', 'Price', { placeholder: 'e.g. amount and currency' }),
          s('billing', 'Billing', ['Free', 'Monthly', 'Annual', 'Usage-based', 'Custom']),
          a('includes', 'What is included', { wide: true }),
        ],
      },
      {
        kind: 'fields',
        fields: [
          a('subscriptionModels', 'Subscription models', { wide: true }),
          a('strategy', 'Pricing strategy', { wide: true }),
          a('revenueStreams', 'Revenue streams', { wide: true }),
          a('enterprise', 'Enterprise pricing', { wide: true }),
          a('freePaid', 'Free and paid offerings', { wide: true }),
        ],
      },
    ],
  },
  {
    id: 'customers',
    title: 'Customers and markets',
    blurb: 'Who you serve and the problems you solve.',
    groups: [
      {
        kind: 'fields',
        fields: [
          a('segments', 'Customer segments', { wide: true }),
          t('industries', 'Target industries'),
          t('geoMarkets', 'Geographic markets'),
          a('icp', 'Ideal customer profile', { wide: true }),
          a('problems', 'Customer problems solved', { wide: true }),
        ],
      },
    ],
  },
  {
    id: 'infra',
    title: 'Infrastructure',
    blurb: 'Where CompeteIQ runs.',
    groups: [
      {
        kind: 'fields',
        fields: [
          t('cloud', 'Cloud providers'),
          t('gpu', 'GPU resources'),
          t('compute', 'Computing capacity'),
          t('servers', 'Servers'),
          t('databases', 'Databases'),
          t('storage', 'Storage'),
          a('architecture', 'Deployment architecture', { wide: true }),
        ],
      },
    ],
  },
  {
    id: 'partners',
    title: 'Partnerships',
    blurb: 'The companies CompeteIQ depends on and works with.',
    groups: [
      ...[
        ['techPartners', 'Technology partners', 'technology partner'],
        ['suppliers', 'Suppliers', 'supplier'],
        ['partnerIntegrations', 'Integrations', 'integration partner'],
        ['strategicPartners', 'Strategic partnerships', 'strategic partner'],
      ].map(([key, label, itemName]) => ({
        kind: 'list',
        key,
        label,
        itemName,
        titleKey: 'name',
        fields: [t('name', 'Partner name'), a('notes', 'Scope and notes', { wide: true })],
      })),
    ],
  },
  {
    id: 'team',
    title: 'Team and organization',
    blurb: 'People, departments and open roles.',
    groups: [
      {
        kind: 'list',
        key: 'leadership',
        label: 'Leadership',
        itemName: 'leader',
        titleKey: 'name',
        fields: [t('name', 'Name'), t('role', 'Title'), a('focus', 'Focus area', { wide: true })],
      },
      {
        kind: 'list',
        key: 'keyRoles',
        label: 'Key roles',
        itemName: 'role',
        titleKey: 'role',
        fields: [t('role', 'Role'), a('responsibility', 'Responsibility', { wide: true })],
      },
      {
        kind: 'fields',
        fields: [
          n('teamSize', 'Team size'),
          a('departments', 'Departments', { wide: true }),
          a('hiring', 'Hiring requirements', { wide: true }),
        ],
      },
    ],
  },
  {
    id: 'strategy',
    title: 'Business strategy',
    blurb: 'Where CompeteIQ is going and how it gets there.',
    groups: [
      {
        kind: 'fields',
        fields: [
          a('shortGoals', 'Short-term goals', { wide: true }),
          a('longGoals', 'Long-term goals', { wide: true }),
          a('growth', 'Growth strategy', { wide: true }),
          a('positioning', 'Competitive positioning', { wide: true }),
          a('priorities', 'Strategic priorities', { wide: true }),
          a('expansion', 'Expansion plans', { wide: true }),
        ],
      },
    ],
  },
  {
    id: 'swot',
    title: 'SWOT analysis',
    blurb: 'Honest strengths and gaps. Agents weigh competitor moves against these.',
    groups: [
      ['strengths', 'Strengths', 'strength'],
      ['weaknesses', 'Weaknesses', 'weakness'],
      ['opportunities', 'Opportunities', 'opportunity'],
      ['threats', 'Threats', 'threat'],
    ].map(([key, label, itemName]) => ({
      kind: 'list',
      key,
      label,
      itemName,
      titleKey: 'text',
      fields: [a('text', label.replace(/s$/, ''), { wide: true })],
    })),
  },
  {
    id: 'positioning',
    title: 'Competitive positioning',
    blurb: 'How CompeteIQ stands against the market.',
    groups: [
      {
        kind: 'fields',
        fields: [
          a('advantages', 'Competitive advantages', { wide: true }),
          a('differentiators', 'Differentiators', { wide: true }),
          a('mainCompetitors', 'Main competitors', {
            wide: true,
            placeholder: 'External companies only, e.g. OpenAI, Google, Anthropic, Microsoft, Meta, NVIDIA',
          }),
          a('marketPositioning', 'Market positioning', { wide: true }),
          a('improvements', 'Areas requiring improvement', { wide: true }),
        ],
      },
    ],
  },
];

const filled = (v) => (typeof v === 'string' ? v.trim() !== '' : v !== undefined && v !== null && v !== '');

// Returns { done, total, pct } for one section. Optional fields are not counted.
// A list group counts as one item and is complete when it has at least one entry.
export function completion(section, data = {}) {
  let done = 0;
  let total = 0;
  section.groups.forEach((g) => {
    if (g.kind === 'fields') {
      g.fields.forEach((f) => {
        if (f.optional) return;
        total += 1;
        if (filled(data[f.key])) done += 1;
      });
    } else {
      total += 1;
      const items = data[g.key] || [];
      if (items.some((it) => g.fields.some((f) => filled(it[f.key])))) done += 1;
    }
  });
  return { done, total, pct: total ? Math.round((done / total) * 100) : 0 };
}

// Clearly marked sample data for demos. Nothing here is a real company fact.
export const SAMPLE = {
  overview: {
    companyName: PLATFORM_NAME,
    description: '[Sample] Replace with your real company description.',
  },
  products: {
    products: [
      {
        id: 'sample-1',
        name: '[Sample] CompeteIQ Platform',
        category: 'Competitive intelligence',
        description: '[Sample] Monitors competitors and recommends strategic actions.',
        status: 'Beta',
      },
    ],
  },
  tech: {
    aiModels: [
      {
        id: 'sample-2',
        name: '[Sample] Strategy analysis model',
        capabilities: '[Sample] Compares competitor developments with company data.',
        status: 'In development',
      },
    ],
  },
  swot: {
    strengths: [{ id: 'sample-3', text: '[Sample] Memory of past competitor events through Hindsight.' }],
    weaknesses: [{ id: 'sample-4', text: '[Sample] Edit this to reflect real weaknesses.' }],
  },
};