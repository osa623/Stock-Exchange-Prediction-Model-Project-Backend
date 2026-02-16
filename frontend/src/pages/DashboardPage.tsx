import { useEffect, useState } from "react";
import { adminApi, type DashboardStats } from "../services/api";
import {
  Users,
  Crown,
  Briefcase,
  Eye,
  ShieldAlert,
  TrendingUp,
  UserPlus,
  BarChart3,
} from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    adminApi
      .getStats()
      .then((r) => setStats(r.data))
      .catch((e) => setError(e.response?.data?.detail || "Failed to load stats"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-red-400">
        {error}
      </div>
    );
  }

  if (!stats) return null;

  const cards = [
    {
      label: "Total Users",
      value: stats.total_users,
      icon: Users,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
    },
    {
      label: "Premium Users",
      value: stats.premium_users,
      icon: Crown,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      label: "Free Users",
      value: stats.free_users,
      icon: Users,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
    {
      label: "New Signups (30d)",
      value: stats.recent_signups_30d,
      icon: UserPlus,
      color: "text-violet-400",
      bg: "bg-violet-500/10",
    },
    {
      label: "Portfolios",
      value: stats.total_portfolios,
      icon: Briefcase,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      label: "Positions",
      value: stats.total_positions,
      icon: TrendingUp,
      color: "text-teal-400",
      bg: "bg-teal-500/10",
    },
    {
      label: "Watchlist Items",
      value: stats.total_watchlist_items,
      icon: Eye,
      color: "text-pink-400",
      bg: "bg-pink-500/10",
    },
    {
      label: "Security Events",
      value: stats.total_security_events,
      icon: ShieldAlert,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
    },
  ];

  return (
    <div>
      <div className="mb-8 flex items-center gap-3">
        <BarChart3 className="h-7 w-7 text-cyan-400" />
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <div
            key={c.label}
            className="rounded-xl border border-gray-800 bg-gray-900 p-5 transition-colors hover:border-gray-700"
          >
            <div className="flex items-center gap-3">
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-lg ${c.bg}`}
              >
                <c.icon className={`h-5 w-5 ${c.color}`} />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">{c.label}</p>
                <p className="text-2xl font-bold text-white">
                  {c.value.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
