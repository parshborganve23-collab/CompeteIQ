
/**
 * CompeteIQ frontend API service layer.
 * All calls go through this module.
 * Backend API keys are never exposed here.
 */

const API_BASE = (
  import.meta.env.VITE_API_BASE ||
  "http://127.0.0.1:8000/api"
).replace(/\/+$/, "");

// ---------- Shared API Request ----------

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
      cache: "no-store",
    });

    if (!response.ok) {
      let errorMessage = `Request failed (${response.status})`;

      try {
        const body = await response.json();
        const detail = body.detail;

        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (detail && typeof detail === "object") {
          errorMessage =
            detail.detail ||
            detail.reason ||
            detail.error ||
            JSON.stringify(detail);
        } else if (body.message) {
          errorMessage = body.message;
        }
      } catch {
        // Keep the HTTP status error if JSON parsing fails.
      }

      throw new Error(errorMessage);
    }

    if (response.status === 204) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error(`[CompeteIQ API] ${path}:`, error);

    if (error instanceof TypeError) {
      throw new Error(
        `Cannot connect to backend at ${API_BASE}. ` +
        "Check that FastAPI is running and CORS is configured."
      );
    }

    throw error;
  }
}

// ---------- Company ----------

export const companyApi = {
  get: () => request("/company/"),

  update: (data) =>
    request("/company/", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  listSections: () => request("/company/sections"),

  getSection: (sectionId) =>
    request(`/company/sections/${sectionId}`),

  saveSection: (sectionId, data) =>
    request(`/company/sections/${sectionId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  patchSection: (sectionId, data) =>
    request(`/company/sections/${sectionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteSection: (sectionId) =>
    request(`/company/sections/${sectionId}`, {
      method: "DELETE",
    }),

  getProfile: () => request("/company/profile"),
};

// ---------- AI Models ----------

export const modelsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/models/${qs ? `?${qs}` : ""}`);
  },

  get: (id) => request(`/models/${id}`),

  create: (data) =>
    request("/models/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id, data) =>
    request(`/models/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id) =>
    request(`/models/${id}`, {
      method: "DELETE",
    }),
};

// ---------- Intelligence Events ----------

export const intelligenceApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/intelligence/${qs ? `?${qs}` : ""}`);
  },

  get: (id) => request(`/intelligence/${id}`),

  create: (data) =>
    request("/intelligence/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id, data) =>
    request(`/intelligence/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id) =>
    request(`/intelligence/${id}`, {
      method: "DELETE",
    }),
};

// ---------- Demo Company (MINTY-GPT) ----------
// MINTY-GPT is a fictional demo competitor.

export const demoCompanyApi = {
  update: (data, apiKey) =>
    request("/demo-company/update", {
      method: "POST",
      body: JSON.stringify(data),
      headers: apiKey
        ? { "X-Demo-API-Key": apiKey }
        : {},
    }),

  get: () => request("/demo-company/"),

  events: () => request("/demo-company/events"),
};

// ---------- Strategy / Recommendations ----------

export const strategyApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/strategy/${qs ? `?${qs}` : ""}`);
  },

  get: (id) => request(`/strategy/${id}`),

  update: (id, data) =>
    request(`/strategy/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  agents: (id) =>
    request(`/strategy/${id}/agents`),

  addAgent: (id, data) =>
    request(`/strategy/${id}/agents`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ---------- Hindsight Memory ----------

export const hindsightApi = {
  status: () =>
    request("/hindsight/status"),

  recall: (query, bankId, limit) =>
    request("/hindsight/recall", {
      method: "POST",
      body: JSON.stringify({
        query,
        bank_id: bankId || "competeiq-intelligence",
        limit: limit ?? 10,
      }),
    }),

  retain: (content, bankId, metadata) =>
    request("/hindsight/retain", {
      method: "POST",
      body: JSON.stringify({
        content,
        bank_id: bankId || "competeiq-intelligence",
        metadata: metadata || {},
      }),
    }),

  reflect: (query, bankId) =>
    request("/hindsight/reflect", {
      method: "POST",
      body: JSON.stringify({
        query,
        bank_id: bankId || "competeiq-intelligence",
      }),
    }),

  workflow: (eventId) =>
    request(`/hindsight/workflow/${eventId}`, {
      method: "POST",
    }),

  memories: (limit = 20, searchQuery = "") => {
    const qs = new URLSearchParams({
      limit: String(limit),
    });

    if (searchQuery) {
      qs.set("search_query", searchQuery);
    }

    return request(
      `/hindsight/memories?${qs.toString()}`
    );
  },

  history: () =>
    request("/hindsight/history"),
};

// ---------- BAND AI Agents ----------

export const bandApi = {
  // Force backend to recheck BAND authentication.
  status: () =>
    request("/band/status?refresh=true"),

  // Retrieve the real configured agent list.
  agents: () =>
    request("/band/agents"),

  // Send an actual message through BAND.
  message: (data, recommendationId) =>
    request("/band/message", {
      method: "POST",
      body: JSON.stringify({
        ...data,
        recommendation_id: recommendationId,
      }),
    }),

  // Start the unified multi-agent workflow.
  workflow: (eventId) =>
    request(`/band/workflow/${eventId}`, {
      method: "POST",
    }),

  // Retrieve actual messages from a BAND room.
  roomMessages: (roomId) =>
    request(
      `/band/room/${encodeURIComponent(roomId)}/messages`
    ),
};

// ---------- Unified Workflows ----------
// CompeteIQ + BAND AI + Hindsight

export const workflowsApi = {
  list: () =>
    request("/workflows"),

  detail: (workflowId, sync = true) =>
    request(
      `/workflows/${workflowId}?sync=${sync ? "true" : "false"}`
    ),

  finalize: (
    workflowId,
    userFeedback = "",
    outcome = ""
  ) =>
    request(`/workflows/${workflowId}/finalize`, {
      method: "POST",
      body: JSON.stringify({
        user_feedback: userFeedback,
        outcome,
      }),
    }),
};

// ---------- Dashboard ----------

export const dashboardApi = {
  stats: () =>
    request("/dashboard/stats"),
};

// ---------- Collection Jobs ----------

export const collectionApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();

    return request(
      `/collection/${qs ? `?${qs}` : ""}`
    );
  },

  create: (sourceName, sourceType = "public") =>
    request("/collection/", {
      method: "POST",
      body: JSON.stringify({
        source_name: sourceName,
        source_type: sourceType,
      }),
    }),

  update: (id, data) =>
    request(`/collection/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
