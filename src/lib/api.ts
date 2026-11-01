import type { AdminConfig, City, Cost, Estimate, Job, JobCreate, Lead, Me, Markets, Stats, User } from "./types";

export class ApiError extends Error {
  status: number; code?: string;
  constructor(message: string, status: number, code?: string) { super(message); this.status = status; this.code = code; }
}

async function call<T>(path: string, init: RequestInit = {}, timeoutMs = 30000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(path, { ...init, signal: ctrl.signal, cache: "no-store", credentials: "same-origin" });
    const data: unknown = await res.json().catch(() => ({}));
    if (!res.ok) {
      const d = data as { detail?: unknown; code?: string };
      const msg = typeof d.detail === "string" ? d.detail : Array.isArray(d.detail) ? "Please check the form values." : `Request failed (${res.status})`;
      throw new ApiError(msg, res.status, d.code);
    }
    return data as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e instanceof DOMException && e.name === "AbortError") throw new ApiError("The request timed out. Please try again.", 504);
    throw new ApiError("Could not reach the server. Check your connection.", 0);
  } finally { clearTimeout(timer); }
}

const body = (method: string, data?: unknown, headers: Record<string, string> = {}): RequestInit => ({
  method, headers: { "Content-Type": "application/json", ...headers }, body: data === undefined ? undefined : JSON.stringify(data),
});

export const me = () => call<Me>("/api/auth/me");
export const login = (email: string, password: string) => call<{ user: User }>("/api/auth/login", body("POST", { email, password }));
export const register = (email: string, password: string) => call<{ user: User }>("/api/auth/register", body("POST", { email, password }));
export const logout = () => call<{ ok: boolean }>("/api/auth/logout", body("POST", {}));

export const markets = () => call<Markets>("/api/markets");
export const cities = (cc: string) => call<{ items: City[]; admin1: string[] }>(`/api/markets/${cc}/cities?limit=2000`);
export const estimate = (country: string, niche: string, n: number) => call<Estimate>(`/api/estimate?country=${country}&niche=${niche}&lead_count=${n}`);

export const createJob = (j: JobCreate, key: string) => call<{ id: string; status: string; estimate: Estimate }>("/api/jobs", body("POST", j, { "Idempotency-Key": key }));
export const jobs = () => call<{ items: Job[] }>("/api/jobs");
export const job = (id: string) => call<Job>(`/api/jobs/${id}`);
export const jobLeads = (id: string) => call<{ items: Lead[] }>(`/api/jobs/${id}/leads`);
export const cancelJob = (id: string) => call<{ cancelled: boolean }>(`/api/jobs/${id}/cancel`, body("POST", {}));
export const resumeJob = (id: string) => call<{ resumed: boolean }>(`/api/jobs/${id}/resume`, body("POST", {}));
export const rerunJob = (id: string) => call<{ id: string }>(`/api/jobs/${id}/rerun`, body("POST", {}));
export const exportUrl = (id: string, format: "csv" | "xlsx") => `/api/jobs/${id}/export?format=${format}`;

export const sendFeedback = (id: string, value: string) => call<{ feedback: string }>(`/api/leads/${id}/feedback`, body("POST", { value }));
export const saveLead = (id: string) => call<{ saved: boolean }>(`/api/leads/${id}/save`, body("POST", {}));
export const unsaveLead = (id: string) => call<{ saved: boolean }>(`/api/leads/${id}/save`, body("DELETE"));
export const saved = () => call<{ items: Lead[] }>("/api/saved");
export const stats = () => call<Stats>("/api/stats");
export const health = () => call<{ status: string; database: string; live_discovery_configured: boolean }>("/api/health");

export const adminConfig = () => call<AdminConfig>("/api/admin/config");
export const adminCost = () => call<Cost>("/api/admin/cost");
export const adminPut = (path: string, data: unknown) => call<{ ok: boolean }>(`/api/admin/${path}`, body("PUT", data));
export const adminPost = (path: string, data: unknown) => call<{ ok: boolean }>(`/api/admin/${path}`, body("POST", data));
export const adminDelete = (path: string) => call<{ ok: boolean }>(`/api/admin/${path}`, body("DELETE"));
