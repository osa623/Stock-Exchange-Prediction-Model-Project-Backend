import axios from "axios";
import { auth } from "../config/firebase";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// Attach Firebase ID token to every request
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle common response errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid — sign out
      auth.signOut();
    }
    return Promise.reject(error);
  }
);

// ── Admin endpoints ─────────────────────────────────────────────────────────

export interface DashboardStats {
  total_users: number;
  premium_users: number;
  free_users: number;
  total_portfolios: number;
  total_positions: number;
  total_watchlist_items: number;
  total_security_events: number;
  recent_signups_30d: number;
}

export interface UserSummary {
  id: number;
  firebase_uid: string;
  first_name: string;
  last_name: string;
  username: string;
  email: string | null;
  phone_number: string | null;
  avatar_url: string | null;
  pin_is_set: boolean;
  subscription_status: string;
  created_at: string;
  updated_at: string;
}

export interface UserDetail extends UserSummary {
  onboarding: {
    experience_level: string | null;
    primary_goal: string | null;
    investor_type: string | null;
    portfolio_size: string | null;
  } | null;
}

export interface PortfolioPosition {
  id: number;
  symbol: string;
  qty: string;
  avg_price: string;
  total_cost: string | null;
  bes: string | null;
  currency: string | null;
}

export interface Portfolio {
  id: number;
  name: string;
  base_currency: string | null;
  source_type: string | null;
  created_at: string;
  updated_at: string;
  positions: PortfolioPosition[];
}

export interface WatchlistItem {
  id: number;
  symbol: string;
  display_name: string | null;
  created_at: string;
}

export interface SecurityEvent {
  id: number;
  event_type: string | null;
  ip_address: string | null;
  detail: string | null;
  created_at: string;
}

export interface PaginatedUsers {
  total: number;
  skip: number;
  limit: number;
  users: UserSummary[];
}

export interface PaginatedSecurityEvents {
  total: number;
  events: SecurityEvent[];
}

// ── API calls ─────────────────────────────────────────────────────────────

export const adminApi = {
  getStats: () => api.get<DashboardStats>("/admin/stats"),

  getUsers: (params: { skip?: number; limit?: number; search?: string }) =>
    api.get<PaginatedUsers>("/admin/users", { params }),

  getUser: (userId: number) => api.get<UserDetail>(`/admin/users/${userId}`),

  deleteUser: (userId: number) => api.delete(`/admin/users/${userId}`),

  getUserPortfolios: (userId: number) =>
    api.get<Portfolio[]>(`/admin/users/${userId}/portfolios`),

  getUserWatchlist: (userId: number) =>
    api.get<WatchlistItem[]>(`/admin/users/${userId}/watchlist`),

  getUserSecurityEvents: (userId: number, params?: { skip?: number; limit?: number }) =>
    api.get<PaginatedSecurityEvents>(`/admin/users/${userId}/security-events`, { params }),

  deletePortfolio: (portfolioId: number) =>
    api.delete(`/admin/portfolios/${portfolioId}`),
};

// ── Admin Auth / Registration ───────────────────────────────────────────

export interface AdminProfile {
  id: number;
  firebase_uid: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string | null;
  avatar_url: string | null;
  role: "super_admin" | "admin";
  is_active: boolean;
  invited_by_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface RegistrationStatus {
  registration_open: boolean;
  admin_count: number;
}

export const adminAuthApi = {
  /** Check if self-registration is open (0 admins exist) */
  getRegistrationStatus: () =>
    api.get<RegistrationStatus>("/admin/auth/status"),

  /** Self-register as first admin (super_admin) */
  register: (data: {
    first_name: string;
    last_name: string;
    email: string;
    phone_number?: string;
  }) => api.post<AdminProfile>("/admin/auth/register", data),

  /** Get current admin profile */
  getMe: () => api.get<AdminProfile>("/admin/auth/me"),

  /** Update current admin profile */
  updateMe: (data: {
    first_name?: string;
    last_name?: string;
    phone_number?: string;
    avatar_url?: string;
  }) => api.patch<AdminProfile>("/admin/auth/me", data),

  /** List all admins */
  listAdmins: () =>
    api.get<{ admins: AdminProfile[]; total: number }>("/admin/auth/admins"),

  /** Invite a new admin */
  invite: (data: {
    firebase_uid: string;
    first_name: string;
    last_name: string;
    email: string;
    phone_number?: string;
    role?: "admin" | "super_admin";
  }) => api.post<AdminProfile>("/admin/auth/invite", data),

  /** Deactivate an admin */
  deactivateAdmin: (adminId: number) =>
    api.patch(`/admin/auth/admins/${adminId}/deactivate`),

  /** Delete an admin */
  deleteAdmin: (adminId: number) =>
    api.delete(`/admin/auth/admins/${adminId}`),
};

// ── Report types ────────────────────────────────────────────────────────

export interface ReportSummary {
  id: string;
  category: string;
  subcategory: string | null;
  title: string;
  symbol: string | null;
  access_level: "public" | "registered" | "premium";
  summary: string | null;
  tags: string[];
  created_at: string | null;
}

export interface ReportDetail extends ReportSummary {
  data: Record<string, unknown>;
  updated_at: string | null;
}

export interface ReportFull extends ReportDetail {
  raw_data: Record<string, unknown> | null;
  methodology: string | null;
  metadata: Record<string, unknown> | null;
}

export interface ReportListResponse {
  reports: ReportSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FolderNode {
  name: string;
  path: string;
  children: FolderNode[];
  report_count: number;
}

export interface FolderTreeResponse {
  tree: FolderNode[];
  total_reports: number;
}

export interface ReportListParams {
  category?: string;
  subcategory?: string;
  symbol?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

// ── Report API calls ────────────────────────────────────────────────────

export const reportsApi = {
  // Public (no auth needed)
  getPublicReports: (params: ReportListParams) =>
    api.get<ReportListResponse>("/reports/public", { params }),

  getPublicReport: (reportId: string) =>
    api.get<ReportSummary>(`/reports/public/${reportId}`),

  // Folder tree (works with or without auth)
  getFolderTree: () => api.get<FolderTreeResponse>("/reports/tree"),

  // Registered (auth required)
  getReports: (params: ReportListParams) =>
    api.get<ReportListResponse>("/reports/list", { params }),

  getReportDetail: (reportId: string) =>
    api.get<ReportDetail>(`/reports/detail/${reportId}`),

  // Premium
  getPremiumReports: (params: ReportListParams) =>
    api.get<ReportListResponse>("/reports/premium/list", { params }),

  getPremiumReport: (reportId: string) =>
    api.get<ReportFull>(`/reports/premium/${reportId}`),

  exportReport: (reportId: string) =>
    api.get<{ export_format: string; report: ReportFull }>(
      `/reports/premium/${reportId}/export`
    ),
};

export default api;
