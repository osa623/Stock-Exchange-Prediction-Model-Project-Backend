import { useEffect, useState } from "react";
import {
  dataApi,
  type SectorStructure,
  type CompanyStructure,
  type YearStructure,
  type FileReference,
  type ExtractedDataRecord,
} from "../services/api";
import {
  FolderTree,
  FileText,
  ChevronRight,
  ChevronDown,
  Building2,
  Calendar,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Database,
  FileBarChart,
  FileSpreadsheet,
  GitBranch,
  File,
} from "lucide-react";

// ─── Type label / icon helpers ───────────────────────────────────────────

const TYPE_META: Record<string, { label: string; color: string }> = {
  financial_statements: {
    label: "Financial Statements",
    color: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  },
  investor_relations: {
    label: "Investor Relations",
    color: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  },
  subsidiary_chart: {
    label: "Subsidiary Chart",
    color: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  },
  other: {
    label: "Other",
    color: "bg-gray-500/15 text-gray-400 border-gray-500/30",
  },
};

function typeLabel(type: string) {
  return TYPE_META[type]?.label ?? type.replace(/_/g, " ");
}

function typeColor(type: string) {
  return TYPE_META[type]?.color ?? "bg-gray-500/15 text-gray-400 border-gray-500/30";
}

function TypeIcon({ type, className }: { type: string; className?: string }) {
  const cls = className ?? "h-5 w-5";
  switch (type) {
    case "financial_statements":
      return <FileSpreadsheet className={cls} />;
    case "investor_relations":
      return <FileBarChart className={cls} />;
    case "subsidiary_chart":
      return <GitBranch className={cls} />;
    default:
      return <File className={cls} />;
  }
}

// ─── Sidebar: Sector Tree ────────────────────────────────────────────────

function SectorNode({
  sector,
  selectedSector,
  selectedCompany,
  selectedYear,
  onSelectSector,
  onSelectCompany,
  onSelectYear,
}: {
  sector: SectorStructure;
  selectedSector: string | null;
  selectedCompany: string | null;
  selectedYear: string | null;
  onSelectSector: (sector: string) => void;
  onSelectCompany: (sector: string, company: string) => void;
  onSelectYear: (sector: string, company: string, year: string) => void;
}) {
  const isExpanded = selectedSector === sector._id;
  const totalCompanies = sector.companies.length;

  return (
    <div>
      {/* Sector */}
      <button
        onClick={() => onSelectSector(sector._id)}
        className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors ${isExpanded
            ? "bg-cyan-500/15 text-cyan-400"
            : "text-gray-400 hover:bg-gray-800 hover:text-white"}`}
      >
        {isExpanded ? (
          <ChevronDown className="h-4 w-4 shrink-0" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0" />
        )}
        <Database className="h-4 w-4 shrink-0" />
        <span className="truncate font-medium">{sector._id}</span>
        <span className="ml-auto shrink-0 rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-500">
          {totalCompanies}
        </span>
      </button>

      {/* Companies */}
      {isExpanded &&
        sector.companies.map((company) => (
          <CompanyNode
            key={company.company}
            sectorId={sector._id}
            company={company}
            selectedCompany={selectedCompany}
            selectedYear={selectedYear}
            onSelectCompany={onSelectCompany}
            onSelectYear={onSelectYear}
          />
        ))}
    </div>
  );
}

function CompanyNode({
  sectorId,
  company,
  selectedCompany,
  selectedYear,
  onSelectCompany,
  onSelectYear,
}: {
  sectorId: string;
  company: CompanyStructure;
  selectedCompany: string | null;
  selectedYear: string | null;
  onSelectCompany: (sector: string, company: string) => void;
  onSelectYear: (sector: string, company: string, year: string) => void;
}) {
  const isExpanded = selectedCompany === company.company;

  return (
    <div>
      <button
        onClick={() => onSelectCompany(sectorId, company.company)}
        className={`flex w-full items-center gap-2 rounded-lg py-2 text-sm transition-colors ${isExpanded
            ? "bg-cyan-500/10 text-cyan-300"
            : "text-gray-400 hover:bg-gray-800 hover:text-white"}`}
        style={{ paddingLeft: "36px" }}
      >
        {isExpanded ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        )}
        <Building2 className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate">{company.company}</span>
        <span className="ml-auto shrink-0 rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-500">
          {company.years.length}
        </span>
      </button>

      {isExpanded &&
        company.years
          .sort((a, b) => b.year.localeCompare(a.year))
          .map((yr) => (
            <YearNode
              key={yr.year}
              sectorId={sectorId}
              companyName={company.company}
              year={yr}
              selectedYear={selectedYear}
              onSelectYear={onSelectYear}
            />
          ))}
    </div>
  );
}

function YearNode({
  sectorId,
  companyName,
  year,
  selectedYear,
  onSelectYear,
}: {
  sectorId: string;
  companyName: string;
  year: YearStructure;
  selectedYear: string | null;
  onSelectYear: (sector: string, company: string, year: string) => void;
}) {
  const isSelected = selectedYear === year.year;

  return (
    <button
      onClick={() => onSelectYear(sectorId, companyName, year.year)}
      className={`flex w-full items-center gap-2 rounded-lg py-1.5 text-sm transition-colors ${isSelected
          ? "bg-cyan-500/10 text-cyan-200"
          : "text-gray-500 hover:bg-gray-800 hover:text-gray-300"}`}
      style={{ paddingLeft: "60px" }}
    >
      <Calendar className="h-3.5 w-3.5 shrink-0" />
      <span>{year.year}</span>
      <span className="ml-auto shrink-0 rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-600">
        {year.files.length}
      </span>
    </button>
  );
}

// ─── File Type Card ──────────────────────────────────────────────────────

function FileTypeCard({
  file,
  onSelect,
}: {
  file: FileReference;
  onSelect: (id: string) => void;
}) {
  return (
    <button
      onClick={() => onSelect(file.id)}
      className={`flex items-center gap-4 rounded-xl border p-5 text-left transition-all hover:scale-[1.01] hover:shadow-lg ${typeColor(file.type)}`}
    >
      <div className="rounded-lg bg-gray-800/50 p-3">
        <TypeIcon type={file.type} className="h-6 w-6" />
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="font-medium">{typeLabel(file.type)}</h3>
        <p className="mt-0.5 truncate text-xs opacity-60 font-mono">{file.id}</p>
      </div>
      <ChevronRight className="h-5 w-5 shrink-0 opacity-40" />
    </button>
  );
}

// ─── Data Detail Panel ───────────────────────────────────────────────────

function renderValue(val: unknown, depth = 0): React.ReactNode {
  if (val === null || val === undefined) {
    return <span className="text-gray-600 italic">null</span>;
  }
  if (typeof val === "number") {
    return (
      <span className="font-mono text-white">
        {val < 1 && val > -1 && val !== 0
          ? `${(val * 100).toFixed(1)}%`
          : val.toLocaleString()}
      </span>
    );
  }
  if (typeof val === "boolean") {
    return (
      <span className={val ? "text-green-400" : "text-red-400"}>
        {val.toString()}
      </span>
    );
  }
  if (typeof val === "string") {
    return <span className="text-white">{val}</span>;
  }
  if (Array.isArray(val)) {
    if (val.length === 0)
      return <span className="text-gray-600 italic">[]</span>;
    if (depth > 1) {
      return (
        <span className="text-gray-400 text-xs font-mono">
          [{val.length} items]
        </span>
      );
    }
    if (typeof val[0] === "object" && val[0] !== null) {
      const keys = Object.keys(val[0] as Record<string, unknown>);
      return (
        <div className="overflow-x-auto rounded-lg border border-gray-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-800/50">
                {keys.map((k) => (
                  <th
                    key={k}
                    className="px-3 py-2 text-left font-medium text-gray-400 whitespace-nowrap"
                  >
                    {k.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {val.map((item, i) => (
                <tr key={i} className="border-t border-gray-800/50">
                  {keys.map((k) => (
                    <td
                      key={k}
                      className="px-3 py-1.5 text-white whitespace-nowrap"
                    >
                      {renderValue((item as Record<string, unknown>)[k], depth + 1)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }
    return (
      <span className="text-white font-mono text-xs">
        {val.map(String).join(", ")}
      </span>
    );
  }
  if (typeof val === "object") {
    if (depth > 1) {
      return (
        <span className="text-gray-400 text-xs font-mono">
          {JSON.stringify(val).slice(0, 80)}...
        </span>
      );
    }
    const entries = Object.entries(val as Record<string, unknown>);
    return (
      <div className="overflow-hidden rounded-lg border border-gray-800">
        <table className="w-full text-sm">
          <tbody>
            {entries.map(([k, v]) => (
              <tr key={k} className="border-t border-gray-800/50 first:border-0">
                <td className="px-3 py-2 text-gray-400 align-top whitespace-nowrap font-medium">
                  {k.replace(/_/g, " ")}
                </td>
                <td className="px-3 py-2">{renderValue(v, depth + 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  return <span className="text-white">{String(val)}</span>;
}

function DetailPanel({
  record,
  onClose,
}: {
  record: ExtractedDataRecord;
  onClose: () => void;
}) {
  const dataEntries = record.data ? Object.entries(record.data) : [];

  return (
    <div className="flex flex-col gap-4 overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <button
            onClick={onClose}
            className="mb-2 flex items-center gap-1 text-sm text-gray-500 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Back to files
          </button>
          <h2 className="text-xl font-semibold text-white">
            {record.company}
          </h2>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-gray-500">
            <span className="rounded bg-gray-800 px-2 py-0.5">{record.sector}</span>
            <span>{record.year}</span>
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${typeColor(record.type)}`}
            >
              <TypeIcon type={record.type} className="h-3 w-3" />
              {typeLabel(record.type)}
            </span>
          </div>
        </div>
      </div>

      {/* Data content */}
      {dataEntries.length > 0 ? (
        <div className="space-y-4">
          {dataEntries.map(([key, val]) => (
            <div
              key={key}
              className="rounded-xl border border-gray-800 bg-gray-900/50 p-4"
            >
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
                {key.replace(/_/g, " ")}
              </h3>
              {renderValue(val)}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-8 text-center text-gray-600">
          No data available
        </div>
      )}

      {/* Timestamps */}
      <div className="flex gap-4 text-xs text-gray-600">
        {record.createdAt && (
          <span>Created: {new Date(record.createdAt).toLocaleDateString()}</span>
        )}
        {record.updatedAt && (
          <span>Updated: {new Date(record.updatedAt).toLocaleDateString()}</span>
        )}
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═════════════════════════════════════════════════════════════════════════

export default function ReportsPage() {
  // Structure data
  const [sectors, setSectors] = useState<SectorStructure[]>([]);
  const [structureLoading, setStructureLoading] = useState(true);

  // Navigation state
  const [selectedSector, setSelectedSector] = useState<string | null>(null);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<string | null>(null);

  // Files for selected year
  const [currentFiles, setCurrentFiles] = useState<FileReference[]>([]);

  // Detail view
  const [selectedRecord, setSelectedRecord] = useState<ExtractedDataRecord | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Error
  const [error, setError] = useState<string | null>(null);

  // Computed totals
  const totalCompanies = sectors.reduce((sum, s) => sum + s.companies.length, 0);
  const totalFiles = sectors.reduce(
    (sum, s) =>
      sum +
      s.companies.reduce(
        (cSum, c) =>
          cSum + c.years.reduce((ySum, y) => ySum + y.files.length, 0),
        0
      ),
    0
  );

  // ── Load structure ────────────────────────────────────────────────────

  useEffect(() => {
    const load = async () => {
      try {
        setStructureLoading(true);
        setError(null);
        const res = await dataApi.getStructure();
        setSectors(res.data);
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Failed to load structure";
        setError(msg);
        console.error("Failed to load data structure", err);
      } finally {
        setStructureLoading(false);
      }
    };
    load();
  }, []);

  // ── Sidebar selection handlers ────────────────────────────────────────

  const handleSelectSector = (sector: string) => {
    if (selectedSector === sector) {
      setSelectedSector(null);
      setSelectedCompany(null);
      setSelectedYear(null);
      setCurrentFiles([]);
    } else {
      setSelectedSector(sector);
      setSelectedCompany(null);
      setSelectedYear(null);
      setCurrentFiles([]);
    }
    setSelectedRecord(null);
  };

  const handleSelectCompany = (sector: string, company: string) => {
    if (selectedCompany === company && selectedSector === sector) {
      setSelectedCompany(null);
      setSelectedYear(null);
      setCurrentFiles([]);
    } else {
      setSelectedSector(sector);
      setSelectedCompany(company);
      setSelectedYear(null);
      setCurrentFiles([]);
    }
    setSelectedRecord(null);
  };

  const handleSelectYear = (sector: string, company: string, year: string) => {
    setSelectedSector(sector);
    setSelectedCompany(company);
    setSelectedYear(year);
    setSelectedRecord(null);

    // Find files for this year
    const sectorData = sectors.find((s) => s._id === sector);
    const companyData = sectorData?.companies.find((c) => c.company === company);
    const yearData = companyData?.years.find((y) => y.year === year);
    setCurrentFiles(yearData?.files ?? []);
  };

  // ── File detail handler ───────────────────────────────────────────────

  const handleFileSelect = async (id: string) => {
    try {
      setDetailLoading(true);
      setError(null);
      const res = await dataApi.getById(id);
      setSelectedRecord(res.data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load report data";
      setError(msg);
      console.error("Failed to load record", err);
    } finally {
      setDetailLoading(false);
    }
  };

  // ── Breadcrumb ────────────────────────────────────────────────────────

  const breadcrumb: string[] = [];
  if (selectedSector) breadcrumb.push(selectedSector);
  if (selectedCompany) breadcrumb.push(selectedCompany);
  if (selectedYear) breadcrumb.push(selectedYear);

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div className="flex h-full gap-6">
      {/* ── Sidebar ──────────────────────────────────────────────────── */}
      <aside className="hidden w-72 shrink-0 flex-col overflow-y-auto rounded-xl border border-gray-800 bg-gray-900/30 lg:flex">
        <div className="flex items-center gap-2 border-b border-gray-800 px-4 py-3">
          <FolderTree className="h-5 w-5 text-cyan-400" />
          <h2 className="font-semibold text-white">Sectors</h2>
          <span className="ml-auto rounded-full bg-gray-800 px-2 py-0.5 text-xs text-gray-500">
            {sectors.length} sectors
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {structureLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
            </div>
          ) : sectors.length === 0 ? (
            <p className="px-3 py-4 text-sm text-gray-600">
              No sectors found
            </p>
          ) : (
            sectors.map((sector) => (
              <SectorNode
                key={sector._id}
                sector={sector}
                selectedSector={selectedSector}
                selectedCompany={selectedCompany}
                selectedYear={selectedYear}
                onSelectSector={handleSelectSector}
                onSelectCompany={handleSelectCompany}
                onSelectYear={handleSelectYear}
              />
            ))
          )}
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────── */}
      <div className="flex flex-1 flex-col gap-4 overflow-hidden">
        {/* Breadcrumb / top bar */}
        <div className="flex items-center gap-3">
          {/* Mobile sector selector */}
          <select
            aria-label="Select sector"
            value={selectedSector ?? ""}
            onChange={(e) => {
              const val = e.target.value;
              if (!val) {
                handleSelectSector("");
              } else {
                handleSelectSector(val);
              }
            }}
            className="rounded-lg border border-gray-800 bg-gray-900 px-3 py-2.5 text-sm text-gray-300 lg:hidden"
          >
            <option value="">All Sectors</option>
            {sectors.map((s) => (
              <option key={s._id} value={s._id}>
                {s._id}
              </option>
            ))}
          </select>

          {/* Breadcrumbs */}
          <div className="hidden items-center gap-1.5 text-sm text-gray-500 lg:flex">
            <button
              onClick={() => {
                setSelectedSector(null);
                setSelectedCompany(null);
                setSelectedYear(null);
                setCurrentFiles([]);
                setSelectedRecord(null);
              }}
              className="hover:text-cyan-400 transition-colors"
            >
              All Data
            </button>
            {breadcrumb.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1.5">
                <ChevronRight className="h-3.5 w-3.5" />
                <span className={i === breadcrumb.length - 1 ? "text-white" : ""}>
                  {crumb}
                </span>
              </span>
            ))}
          </div>

          <div className="ml-auto text-sm text-gray-500">
            {totalFiles} total records
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Loading spinner for detail */}
        {detailLoading && (
          <div className="flex items-center justify-center rounded-xl border border-gray-800 bg-gray-900/50 py-12">
            <Loader2 className="h-6 w-6 animate-spin text-cyan-400" />
          </div>
        )}

        {/* Detail View */}
        {selectedRecord && !detailLoading && (
          <div className="flex-1 overflow-y-auto rounded-xl border border-gray-800 bg-gray-900/30 p-6">
            <DetailPanel
              record={selectedRecord}
              onClose={() => setSelectedRecord(null)}
            />
          </div>
        )}

        {/* File list (when a year is selected but no detail is open) */}
        {!selectedRecord && !detailLoading && selectedYear && (
          <div className="flex-1 overflow-y-auto">
            {currentFiles.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-gray-600">
                <FileText className="mb-3 h-10 w-10" />
                <p className="text-sm">No files for this year</p>
              </div>
            ) : (
              <div className="grid gap-3 sm:grid-cols-1 md:grid-cols-2">
                {currentFiles.map((f) => (
                  <FileTypeCard
                    key={f.id}
                    file={f}
                    onSelect={handleFileSelect}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Welcome / overview (no selection) */}
        {!selectedRecord && !detailLoading && !selectedYear && (
          <div className="flex flex-1 flex-col items-center justify-center text-gray-600">
            {structureLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-gray-700" />
            ) : sectors.length === 0 ? (
              <>
                <Database className="mb-3 h-12 w-12" />
                <p className="text-lg font-medium text-gray-500">
                  No data available
                </p>
                <p className="mt-1 text-sm">
                  The database is empty or the backend is unavailable.
                </p>
              </>
            ) : (
              <>
                <Database className="mb-3 h-12 w-12" />
                <p className="text-lg font-medium text-gray-400">
                  Financial Reports
                </p>
                <p className="mt-1 text-sm text-gray-600">
                  Select a sector, company, and year from the sidebar to view
                  reports.
                </p>
                {/* Quick stats */}
                <div className="mt-6 flex gap-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-400">
                      {sectors.length}
                    </div>
                    <div className="text-xs text-gray-600">Sectors</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-400">
                      {totalCompanies}
                    </div>
                    <div className="text-xs text-gray-600">Companies</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-400">
                      {totalFiles}
                    </div>
                    <div className="text-xs text-gray-600">Records</div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
