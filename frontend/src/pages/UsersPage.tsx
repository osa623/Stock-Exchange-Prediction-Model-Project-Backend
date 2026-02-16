import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  adminApi,
  type UserSummary,
} from "../services/api";
import {
  Search,
  Trash2,
  Eye,
  ChevronLeft,
  ChevronRight,
  Users,
  Crown,
  AlertCircle,
} from "lucide-react";

const PAGE_SIZE = 20;

export default function UsersPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<number | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await adminApi.getUsers({
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
        search,
      });
      setUsers(res.data.users);
      setTotal(res.data.total);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to load users";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleSearch = () => {
    setPage(0);
    setSearch(searchInput);
  };

  const handleDelete = async (userId: number, username: string) => {
    if (
      !window.confirm(
        `Are you sure you want to delete user "${username}" (ID: ${userId})? This will permanently remove all their data including portfolios, watchlist, and security events.`
      )
    )
      return;

    setDeleting(userId);
    try {
      await adminApi.deleteUser(userId);
      await loadUsers();
    } catch {
      alert("Failed to delete user.");
    } finally {
      setDeleting(null);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Users className="h-7 w-7 text-cyan-400" />
          <h2 className="text-2xl font-bold text-white">Users</h2>
          <span className="rounded-full bg-gray-800 px-3 py-0.5 text-xs font-medium text-gray-400">
            {total}
          </span>
        </div>

        {/* Search */}
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search name, email, username..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-72 rounded-lg border border-gray-700 bg-gray-800 py-2 pl-10 pr-4 text-sm text-white placeholder-gray-500 outline-none focus:border-cyan-500"
            />
          </div>
          <button
            onClick={handleSearch}
            className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-700"
          >
            Search
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-xl border border-gray-800 bg-gray-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs uppercase text-gray-500">
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Plan</th>
                <th className="px-4 py-3">PIN</th>
                <th className="px-4 py-3">Joined</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-gray-500">
                    <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent" />
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="py-12 text-center text-gray-500"
                  >
                    No users found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr
                    key={u.id}
                    className="border-b border-gray-800/50 transition-colors hover:bg-gray-800/30"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      {u.id}
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-white">
                          {u.first_name} {u.last_name}
                        </p>
                        <p className="text-xs text-gray-500">@{u.username}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      {u.email || "—"}
                    </td>
                    <td className="px-4 py-3">
                      {u.subscription_status === "premium" ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400">
                          <Crown className="h-3 w-3" />
                          Premium
                        </span>
                      ) : (
                        <span className="rounded-full bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-gray-400">
                          Free
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {u.pin_is_set ? (
                        <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                          Set
                        </span>
                      ) : (
                        <span className="text-xs text-gray-600">Not set</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => navigate(`/users/${u.id}`)}
                          className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-800 hover:text-cyan-400"
                          title="View details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(u.id, u.username)}
                          disabled={deleting === u.id}
                          className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
                          title="Delete user"
                        >
                          {deleting === u.id ? (
                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-red-400 border-t-transparent" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-gray-800 px-4 py-3">
            <p className="text-xs text-gray-500">
              Showing {page * PAGE_SIZE + 1}–
              {Math.min((page + 1) * PAGE_SIZE, total)} of {total}
            </p>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 disabled:opacity-30"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 disabled:opacity-30"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
