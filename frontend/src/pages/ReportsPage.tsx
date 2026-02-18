import { useEffect, useState, useCallback } from "react";
import {
  reportsApi,
  type FolderNode,
  type ReportSummary,
  type ReportDetail,
  type ReportListResponse,
  type ReportListParams,
} from "../services/api";
import {
  FolderTree,
  FileText,
  ChevronRight,
  ChevronDown,
  Search,
  ChevronLeft,
  ChevronsLeft,
  ChevronsRight,
  Loader2,
  AlertCircle,
  Lock,
  Eye,
  Tag,
} from "lucide-react";

// ─── Folder Tree Node ────────────────────────────────────────────────────

function TreeNode({
  node,
  selectedPath,
  onSelect,
  depth = 0,
}: {
  node: FolderNode;
  selectedPath: string | null;
  onSelect: (path: string, category: string, subcategory?: string) => void;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(depth === 0);
  const hasChildren = node.children.length > 0;
  const isSelected = selectedPath === node.path;

  const parts = node.path.split("/");
  const category = parts[0];
  const subcategory = parts.length > 1 ? parts[1] : undefined;

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) setExpanded(!expanded);
          onSelect(node.path, category, subcategory);
        }}
        className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
          isSelected
            ? "bg-cyan-500/15 text-cyan-400"
            : "text-gray-400 hover:bg-gray-800 hover:text-white"
        }`}
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
      >
        {hasChildren ? (
          expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0" />
          )
        ) : (
          <FileText className="h-4 w-4 shrink-0" />
        )}
        <span className="truncate">{node.name}</span>
        <span className="ml-auto shrink-0 rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-500">
          {node.report_count}
        </span>
      </button>
      {expanded &&
        hasChildren &&
        node.children.map((child) => (
          <TreeNode
            key={child.path}
            node={child}
            selectedPath={selectedPath}
            onSelect={onSelect}
            depth={depth + 1}
          />
        ))}
    </div>
  );
}

// ─── Access Level Badge ──────────────────────────────────────────────────

function AccessBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    public: "bg-green-500/15 text-green-400",
    registered: "bg-blue-500/15 text-blue-400",
    premium: "bg-amber-500/15 text-amber-400",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[level] ?? "bg-gray-700 text-gray-300"
      }`}
    >
      {level === "premium" && <Lock className="h-3 w-3" />}
      {level === "registered" && <Eye className="h-3 w-3" />}
      {level}
    </span>
  );
}

// ─── Report Card ─────────────────────────────────────────────────────────

function ReportCard({
  report,
  onSelect,
}: {
  report: ReportSummary;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      onClick={() => onSelect(report.id)}
      className="flex w-full flex-col gap-2 rounded-xl border border-gray-800 bg-gray-900/50 p-4 text-left transition-colors hover:border-cyan-500/30 hover:bg-gray-900"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-white">{report.title}</h3>
        <AccessBadge level={report.access_level} />
      </div>
      {report.summary && (
        <p className="text-sm text-gray-400 line-clamp-2">{report.summary}</p>
      )}
      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
        {report.symbol && (
          <span className="rounded bg-gray-800 px-2 py-0.5 font-mono">
            {report.symbol}
          </span>
        )}
        {report.category && (
          <span>
            {report.category}
            {report.subcategory && ` / ${report.subcategory}`}
          </span>
        )}
        {report.tags.length > 0 && (
          <span className="flex items-center gap-1">
            <Tag className="h-3 w-3" />
            {report.tags.slice(0, 3).join(", ")}
          </span>
        )}
      </div>
    </button>
  );
}

// ─── Report Detail Panel ─────────────────────────────────────────────────

function DetailPanel({
  report,
  onClose,
}: {
  report: ReportDetail;
  onClose: () => void;
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">{report.title}</h2>
          <div className="mt-1 flex items-center gap-3 text-sm text-gray-500">
            {report.symbol && (
              <span className="rounded bg-gray-800 px-2 py-0.5 font-mono">
                {report.symbol}
              </span>
            )}
            <span>
              {report.category}
              {report.subcategory && ` / ${report.subcategory}`}
            </span>
            <AccessBadge level={report.access_level} />
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg px-3 py-1.5 text-sm text-gray-400 hover:bg-gray-800 hover:text-white"
        >
          Close
        </button>
      </div>

      {report.summary && (
        <p className="mb-4 text-sm text-gray-400">{report.summary}</p>
      )}

      {/* Tags */}
      {report.tags.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {report.tags.map((t) => (
            <span
              key={t}
              className="rounded-full bg-gray-800 px-2.5 py-0.5 text-xs text-gray-400"
            >
              {t}
            </span>
          ))}
        </div>
      )}

      {/* Data Table */}
      {report.data && Object.keys(report.data).length > 0 && (
        <div className="overflow-hidden rounded-lg border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-800/50">
                <th className="px-4 py-2.5 text-left font-medium text-gray-400">
                  Metric
                </th>
                <th className="px-4 py-2.5 text-right font-medium text-gray-400">
                  Value
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(report.data).map(([key, val]) => (
                <tr key={key} className="border-t border-gray-800/50">
                  <td className="px-4 py-2 text-gray-300">
                    {key.replace(/_/g, " ")}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-white">
                    {typeof val === "number"
                      ? val < 1 && val > -1
                        ? `${(val * 100).toFixed(1)}%`
                        : val.toLocaleString()
                      : typeof val === "object"
                      ? JSON.stringify(val)
                      : String(val)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Timestamps */}
      <div className="mt-4 flex gap-4 text-xs text-gray-600">
        {report.created_at && (
          <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
        )}
        {report.updated_at && (
          <span>Updated: {new Date(report.updated_at).toLocaleDateString()}</span>
        )}
      </div>
    </div>
  );
}

// ─── Pagination ──────────────────────────────────────────────────────────

function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-2">
      <button
        disabled={page <= 1}
        onClick={() => onPageChange(1)}
        className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white disabled:opacity-30"
      >
        <ChevronsLeft className="h-4 w-4" />
      </button>
      <button
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white disabled:opacity-30"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <span className="px-3 text-sm text-gray-400">
        Page {page} of {totalPages}
      </span>
      <button
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white disabled:opacity-30"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
      <button
        disabled={page >= totalPages}
        onClick={() => onPageChange(totalPages)}
        className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white disabled:opacity-30"
      >
        <ChevronsRight className="h-4 w-4" />
      </button>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═════════════════════════════════════════════════════════════════════════

export default function ReportsPage() {
  // Folder tree
  const [tree, setTree] = useState<FolderNode[]>([]);
  const [totalReports, setTotalReports] = useState(0);
  const [treeLoading, setTreeLoading] = useState(true);

  // Report list
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [listLoading, setListLoading] = useState(false);

  // Filters
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<string | undefined>();
  const [filterSubcategory, setFilterSubcategory] = useState<string | undefined>();
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Detail view
  const [selectedReport, setSelectedReport] = useState<ReportDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Error
  const [error, setError] = useState<string | null>(null);
  const [mongoUnavailable, setMongoUnavailable] = useState(false);

  // ── Load folder tree ──────────────────────────────────────────────────

  useEffect(() => {
    const load = async () => {
      try {
        setTreeLoading(true);
        const res = await reportsApi.getFolderTree();
        setTree(res.data.tree);
        setTotalReports(res.data.total_reports);
      } catch (err: unknown) {
        console.error("Failed to load folder tree", err);
      } finally {
        setTreeLoading(false);
      }
    };
    load();
  }, []);

  // ── Debounce search input ─────────────────────────────────────────────

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchTerm), 400);
    return () => clearTimeout(t);
  }, [searchTerm]);

  // ── Load reports ──────────────────────────────────────────────────────

  const loadReports = useCallback(async () => {
    try {
      setListLoading(true);
      setError(null);

      const params: ReportListParams = {
        page,
        page_size: pageSize,
        category: filterCategory,
        subcategory: filterSubcategory,
        search: debouncedSearch || undefined,
      };

      let res: { data: ReportListResponse };
      try {
        // Try authenticated endpoint first
        res = await reportsApi.getReports(params);
      } catch {
        // Fall back to public endpoint
        res = await reportsApi.getPublicReports({
          ...params,
          page_size: Math.min(pageSize, 10),
        });
      }

      setReports(res.data.reports);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);

      // Check if backend signalled MongoDB is down
      const anyData = res.data as Record<string, unknown>;
      if (anyData.mongo_status === "unavailable") {
        setMongoUnavailable(true);
      } else {
        setMongoUnavailable(false);
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load reports";
      setError(msg);
    } finally {
      setListLoading(false);
    }
  }, [page, pageSize, filterCategory, filterSubcategory, debouncedSearch]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  // ── Folder selection handler ──────────────────────────────────────────

  const handleFolderSelect = (
    path: string,
    category: string,
    subcategory?: string
  ) => {
    if (selectedPath === path) {
      // Deselect
      setSelectedPath(null);
      setFilterCategory(undefined);
      setFilterSubcategory(undefined);
    } else {
      setSelectedPath(path);
      setFilterCategory(category);
      setFilterSubcategory(subcategory);
    }
    setPage(1);
    setSelectedReport(null);
  };

  // ── Report detail handler ─────────────────────────────────────────────

  const handleReportSelect = async (reportId: string) => {
    try {
      setDetailLoading(true);
      let res;
      try {
        res = await reportsApi.getReportDetail(reportId);
      } catch {
        // Fallback: use the summary we already have
        const found = reports.find((r) => r.id === reportId);
        if (found) {
          setSelectedReport(found as ReportDetail);
          return;
        }
        throw new Error("Report not found");
      }
      setSelectedReport(res.data);
    } catch (err: unknown) {
      console.error("Failed to load report detail", err);
    } finally {
      setDetailLoading(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="flex h-full gap-6">
      {/* ── Sidebar: Folder Tree ─────────────────────────────────────── */}
      <aside className="hidden w-72 shrink-0 flex-col overflow-y-auto rounded-xl border border-gray-800 bg-gray-900/30 lg:flex">
        <div className="flex items-center gap-2 border-b border-gray-800 px-4 py-3">
          <FolderTree className="h-5 w-5 text-cyan-400" />
          <h2 className="font-semibold text-white">Categories</h2>
          <span className="ml-auto rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-500">
            {totalReports}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {treeLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
            </div>
          ) : tree.length === 0 ? (
            <p className="px-3 py-4 text-sm text-gray-600">No categories found</p>
          ) : (
            <>
              {/* All Reports entry */}
              <button
                onClick={() => {
                  setSelectedPath(null);
                  setFilterCategory(undefined);
                  setFilterSubcategory(undefined);
                  setPage(1);
                  setSelectedReport(null);
                }}
                className={`mb-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${
                  selectedPath === null
                    ? "bg-cyan-500/15 text-cyan-400"
                    : "text-gray-400 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <FileText className="h-4 w-4" />
                All Reports
              </button>
              {tree.map((node) => (
                <TreeNode
                  key={node.path}
                  node={node}
                  selectedPath={selectedPath}
                  onSelect={handleFolderSelect}
                />
              ))}
            </>
          )}
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col gap-4 overflow-hidden">
        {/* Search Bar */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              placeholder="Search reports by title, symbol, or tag…"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-gray-800 bg-gray-900/50 py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-600 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30"
            />
          </div>
          {/* Mobile category selector */}
          <select
            aria-label="Filter by category"
            value={selectedPath ?? ""}
            onChange={(e) => {
              const val = e.target.value;
              if (!val) {
                setSelectedPath(null);
                setFilterCategory(undefined);
                setFilterSubcategory(undefined);
              } else {
                const parts = val.split("/");
                setSelectedPath(val);
                setFilterCategory(parts[0]);
                setFilterSubcategory(parts.length > 1 ? parts[1] : undefined);
              }
              setPage(1);
            }}
            className="rounded-lg border border-gray-800 bg-gray-900 px-3 py-2.5 text-sm text-gray-300 lg:hidden"
          >
            <option value="">All Categories</option>
            {tree.map((n) => (
              <option key={n.path} value={n.path}>
                {n.name}
              </option>
            ))}
          </select>
          <div className="text-sm text-gray-500">
            {total} report{total !== 1 ? "s" : ""}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* MongoDB unavailable banner */}
        {mongoUnavailable && !error && (
          <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            Report database is currently unavailable. Check your MongoDB connection credentials.
          </div>
        )}

        {/* Detail View */}
        {selectedReport && !detailLoading && (
          <DetailPanel
            report={selectedReport}
            onClose={() => setSelectedReport(null)}
          />
        )}
        {detailLoading && (
          <div className="flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900/50 py-12">
            <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
          </div>
        )}

        {/* Report List */}
        <div className="flex-1 overflow-y-auto">
          {listLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-gray-600" />
            </div>
          ) : reports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-600">
              <FileText className="mb-3 h-10 w-10" />
              <p className="text-sm">No reports found</p>
              {(filterCategory || debouncedSearch) && (
                <button
                  onClick={() => {
                    setSelectedPath(null);
                    setFilterCategory(undefined);
                    setFilterSubcategory(undefined);
                    setSearchTerm("");
                    setPage(1);
                  }}
                  className="mt-2 text-sm text-cyan-400 hover:underline"
                >
                  Clear filters
                </button>
              )}
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-1 lg:grid-cols-2">
              {reports.map((r) => (
                <ReportCard
                  key={r.id}
                  report={r}
                  onSelect={handleReportSelect}
                />
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </div>
  );
}
