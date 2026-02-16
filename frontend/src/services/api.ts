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

export default api;
