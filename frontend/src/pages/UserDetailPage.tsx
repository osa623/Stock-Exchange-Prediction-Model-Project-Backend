import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  adminApi,
  type UserDetail,
  type Portfolio,
  type WatchlistItem,
  type SecurityEvent,
} from "../services/api";
import {
  ArrowLeft,
  Trash2,
  Crown,
  Briefcase,
  Eye as EyeIcon,
  ShieldAlert,
  User as UserIcon,
  Mail,
  Phone,
  Hash,
  Clock,
  Target,
  BarChart,
  TrendingUp,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

type Tab = "profile" | "portfolios" | "watchlist" | "security";

export default function UserDetailPage() {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const id = Number(userId);

  const [user, setUser] = useState<UserDetail | null>(null);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [secEvents, setSecEvents] = useState<SecurityEvent[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("profile");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedPortfolios, setExpandedPortfolios] = useState<Set<number>>(
    new Set()
  );

  useEffect(() => {
    if (isNaN(id)) return;
    Promise.all([
      adminApi.getUser(id),
      adminApi.getUserPortfolios(id),
      adminApi.getUserWatchlist(id),
      adminApi.getUserSecurityEvents(id, { limit: 100 }),
    ])
      .then(([uRes, pRes, wRes, sRes]) => {
        setUser(uRes.data);
        setPortfolios(pRes.data);
        setWatchlist(wRes.data);
        setSecEvents(sRes.data.events);
      })
      .catch((e) => {
        setError(e.response?.data?.detail || "Failed to load user");
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleDelete = async () => {
    if (!user) return;
    if (
      !window.confirm(
        `Permanently delete "${user.username}" and ALL associated data?`
      )
    )
      return;
    try {
      await adminApi.deleteUser(id);
      navigate("/users");
    } catch {
      alert("Failed to delete user.");
    }
  };

  const handleDeletePortfolio = async (portfolioId: number) => {
    if (!window.confirm("Delete this portfolio and all its positions?")) return;
    try {
      await adminApi.deletePortfolio(portfolioId);
      setPortfolios((prev) => prev.filter((p) => p.id !== portfolioId));
    } catch {
      alert("Failed to delete portfolio.");
    }
  };

  const togglePortfolio = (pid: number) => {
    setExpandedPortfolios((prev) => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid);
      else next.add(pid);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-cyan-400 border-t-transparent" />
      </div>
    );
  }

  if (error || !user) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-red-400">
        {error || "User not found"}
      </div>
    );
  }

  const tabs: { key: Tab; label: string; icon: typeof UserIcon; count?: number }[] = [
    { key: "profile", label: "Profile", icon: UserIcon },
    {
      key: "portfolios",
      label: "Portfolios",
      icon: Briefcase,
      count: portfolios.length,
    },
    {
      key: "watchlist",
      label: "Watchlist",
      icon: EyeIcon,
      count: watchlist.length,
    },
    {
      key: "security",
      label: "Security Events",
      icon: ShieldAlert,
      count: secEvents.length,
    },
  ];

  return (
    <div>
      {/* Back + actions */}
      <div className="mb-6 flex items-center justify-between">
        <button
          onClick={() => navigate("/users")}
          className="flex items-center gap-2 text-sm text-gray-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Users
        </button>
        <button
          onClick={handleDelete}
          className="flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-2 text-sm font-medium text-red-400 transition-colors hover:bg-red-500/20"
        >
          <Trash2 className="h-4 w-4" />
          Delete User
        </button>
      </div>

      {/* User header */}
      <div className="mb-6 rounded-xl border border-gray-800 bg-gray-900 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-cyan-500/10 text-xl font-bold text-cyan-400">
              {user.first_name[0]}
              {user.last_name[0]}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                {user.first_name} {user.last_name}
              </h2>
              <p className="text-sm text-gray-500">@{user.username}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {user.subscription_status === "premium" ? (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-sm font-medium text-amber-400">
                <Crown className="h-4 w-4" />
                Premium
              </span>
            ) : (
              <span className="rounded-full bg-gray-800 px-3 py-1 text-sm font-medium text-gray-400">
                Free
              </span>
            )}
            <span className="rounded-full bg-gray-800 px-3 py-1 text-xs text-gray-500">
              ID: {user.id}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 overflow-x-auto border-b border-gray-800">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === t.key
                ? "border-cyan-400 text-cyan-400"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
            {t.count !== undefined && (
              <span className="rounded-full bg-gray-800 px-2 py-0.5 text-xs">
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "profile" && <ProfileTab user={user} />}
      {activeTab === "portfolios" && (
        <PortfoliosTab
          portfolios={portfolios}
          expanded={expandedPortfolios}
          onToggle={togglePortfolio}
          onDelete={handleDeletePortfolio}
        />
      )}
      {activeTab === "watchlist" && <WatchlistTab items={watchlist} />}
      {activeTab === "security" && <SecurityTab events={secEvents} />}
    </div>
  );
}

/* ─── Profile Tab ────────────────────────────────────────────────────────── */

function ProfileTab({ user }: { user: UserDetail }) {
  const infoItems = [
    { icon: Mail, label: "Email", value: user.email },
    { icon: Phone, label: "Phone", value: user.phone_number },
    { icon: Hash, label: "Firebase UID", value: user.firebase_uid },
    {
      icon: Clock,
      label: "Joined",
      value: new Date(user.created_at).toLocaleString(),
    },
    {
      icon: Clock,
      label: "Last Updated",
      value: user.updated_at ? new Date(user.updated_at).toLocaleString() : null,
    },
    {
      icon: ShieldAlert,
      label: "PIN",
      value: user.pin_is_set ? "Set" : "Not set",
    },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Basic info */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
        <h3 className="mb-4 text-sm font-semibold uppercase text-gray-500">
          Account Information
        </h3>
        <div className="space-y-3">
          {infoItems.map((item) => (
            <div key={item.label} className="flex items-start gap-3">
              <item.icon className="mt-0.5 h-4 w-4 text-gray-600" />
              <div>
                <p className="text-xs text-gray-500">{item.label}</p>
                <p className="text-sm text-gray-300">
                  {item.value || <span className="text-gray-600">—</span>}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Onboarding */}
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
        <h3 className="mb-4 text-sm font-semibold uppercase text-gray-500">
          Onboarding
        </h3>
        {user.onboarding ? (
          <div className="space-y-3">
            {[
              { icon: BarChart, label: "Experience", value: user.onboarding.experience_level },
              { icon: Target, label: "Primary Goal", value: user.onboarding.primary_goal },
              { icon: UserIcon, label: "Investor Type", value: user.onboarding.investor_type },
              { icon: TrendingUp, label: "Portfolio Size", value: user.onboarding.portfolio_size },
            ].map((item) => (
              <div key={item.label} className="flex items-start gap-3">
                <item.icon className="mt-0.5 h-4 w-4 text-gray-600" />
                <div>
                  <p className="text-xs text-gray-500">{item.label}</p>
                  <p className="text-sm capitalize text-gray-300">
                    {item.value?.replace(/_/g, " ") || (
                      <span className="text-gray-600">—</span>
                    )}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-600">Not completed</p>
        )}
      </div>
    </div>
  );
}

/* ─── Portfolios Tab ─────────────────────────────────────────────────────── */

function PortfoliosTab({
  portfolios,
  expanded,
  onToggle,
  onDelete,
}: {
  portfolios: Portfolio[];
  expanded: Set<number>;
  onToggle: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  if (portfolios.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 text-center text-gray-500">
        No portfolios found.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {portfolios.map((p) => (
        <div
          key={p.id}
          className="rounded-xl border border-gray-800 bg-gray-900"
        >
          <div className="flex items-center justify-between p-4">
            <button
              onClick={() => onToggle(p.id)}
              className="flex flex-1 items-center gap-3 text-left"
            >
              {expanded.has(p.id) ? (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-500" />
              )}
              <div>
                <p className="font-medium text-white">{p.name}</p>
                <p className="text-xs text-gray-500">
                  {p.source_type} · {p.positions.length} position
                  {p.positions.length !== 1 ? "s" : ""} ·{" "}
                  {p.base_currency || "—"}
                </p>
              </div>
            </button>
            <button
              onClick={() => onDelete(p.id)}
              className="rounded-lg p-2 text-gray-500 hover:bg-red-500/10 hover:text-red-400"
              title="Delete portfolio"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>

          {expanded.has(p.id) && p.positions.length > 0 && (
            <div className="border-t border-gray-800 px-4 pb-4">
              <table className="mt-3 w-full text-left text-sm">
                <thead>
                  <tr className="text-xs uppercase text-gray-600">
                    <th className="pb-2 pr-4">Symbol</th>
                    <th className="pb-2 pr-4">Qty</th>
                    <th className="pb-2 pr-4">Avg Price</th>
                    <th className="pb-2 pr-4">Total Cost</th>
                    <th className="pb-2">Currency</th>
                  </tr>
                </thead>
                <tbody>
                  {p.positions.map((pos) => (
                    <tr
                      key={pos.id}
                      className="border-t border-gray-800/50 text-gray-300"
                    >
                      <td className="py-2 pr-4 font-mono font-medium text-cyan-400">
                        {pos.symbol}
                      </td>
                      <td className="py-2 pr-4">{pos.qty}</td>
                      <td className="py-2 pr-4">{pos.avg_price}</td>
                      <td className="py-2 pr-4">{pos.total_cost || "—"}</td>
                      <td className="py-2">{pos.currency || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ─── Watchlist Tab ──────────────────────────────────────────────────────── */

function WatchlistTab({ items }: { items: WatchlistItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 text-center text-gray-500">
        No watchlist items.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-xs uppercase text-gray-500">
            <th className="px-4 py-3">Symbol</th>
            <th className="px-4 py-3">Display Name</th>
            <th className="px-4 py-3">Added</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.id}
              className="border-b border-gray-800/50 text-gray-300"
            >
              <td className="px-4 py-3 font-mono font-medium text-cyan-400">
                {item.symbol}
              </td>
              <td className="px-4 py-3">{item.display_name || "—"}</td>
              <td className="px-4 py-3 text-xs text-gray-500">
                {new Date(item.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ─── Security Events Tab ────────────────────────────────────────────────── */

function SecurityTab({ events }: { events: SecurityEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900 p-8 text-center text-gray-500">
        No security events recorded.
      </div>
    );
  }

  const typeColors: Record<string, string> = {
    pin_set: "text-emerald-400 bg-emerald-500/10",
    pin_changed: "text-blue-400 bg-blue-500/10",
    pin_verify_success: "text-emerald-400 bg-emerald-500/10",
    pin_verify_failed: "text-red-400 bg-red-500/10",
    pin_locked: "text-red-400 bg-red-500/10",
    pin_lockout_expired: "text-amber-400 bg-amber-500/10",
    pin_rate_limited: "text-orange-400 bg-orange-500/10",
  };

  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-xs uppercase text-gray-500">
            <th className="px-4 py-3">Event</th>
            <th className="px-4 py-3">IP Address</th>
            <th className="px-4 py-3">Detail</th>
            <th className="px-4 py-3">Time</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr
              key={e.id}
              className="border-b border-gray-800/50"
            >
              <td className="px-4 py-3">
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    typeColors[e.event_type || ""] || "text-gray-400 bg-gray-800"
                  }`}
                >
                  {e.event_type?.replace(/_/g, " ") || "unknown"}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-gray-400">
                {e.ip_address || "—"}
              </td>
              <td className="max-w-xs truncate px-4 py-3 text-xs text-gray-500">
                {e.detail || "—"}
              </td>
              <td className="px-4 py-3 text-xs text-gray-500">
                {new Date(e.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
