import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchProjects, deleteProject } from '../api/client';
import { Link } from 'react-router-dom';
import { 
  Plus, Trash2, Activity, AlertCircle, 
  CheckCircle2, Pencil, Box
} from 'lucide-react';
import { useMemo, useState } from 'react';

const STATUS_CARD = {
  all:     { icon: Activity,     ringClass: "ring-gray-200",         iconClass: "text-gray-500" },
  generating: { icon: Activity,     ringClass: "ring-blue-200",       iconClass: "text-blue-600" },
  completed:    { icon: CheckCircle2,    ringClass: "ring-emerald-200",    iconClass: "text-emerald-600" },
  failed:   { icon: AlertCircle,  ringClass: "ring-red-200", iconClass: "text-red-500" },
};

const STATUS_LABELS: Record<string, string> = {
  generating: "Generating",
  completed: "Completed",
  failed: "Failed"
};

type StatusFilter = "all" | "generating" | "completed" | "failed";

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { data: projects, isLoading } = useQuery({ queryKey: ['projects'], queryFn: fetchProjects });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['projects'] })
  });

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const all = useMemo(() => projects ?? [], [projects]);

  const counts = useMemo(() => {
    const tally: Record<StatusFilter, number> = { all: all.length, generating: 0, completed: 0, failed: 0 };
    for (const project of all) {
      if (tally[project.status as StatusFilter] !== undefined) {
        tally[project.status as StatusFilter]++;
      }
    }
    return tally;
  }, [all]);

  const rows = useMemo(
    () => (statusFilter === "all" ? all : all.filter((p: any) => p.status === statusFilter)),
    [all, statusFilter],
  );

  function toggleFilter(next: StatusFilter) {
    setStatusFilter((current) => (current === next ? "all" : next));
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-semibold text-gray-900">Designs</h1>
          <p className="text-gray-500 mt-1">Manage and generate autonomous CAD models.</p>
        </div>
        <Link
          to="/new"
          className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-blue-600 text-white hover:bg-blue-600/90 h-10 px-4 py-2 w-full md:w-auto"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Create Design
        </Link>
      </header>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          status="all"
          count={counts.all}
          label="All designs"
          isActive={statusFilter === "all"}
          onClick={() => setStatusFilter("all")}
        />
        <StatCard
          status="generating"
          count={counts.generating}
          label="Generating"
          isActive={statusFilter === "generating"}
          onClick={() => toggleFilter("generating")}
        />
        <StatCard
          status="completed"
          count={counts.completed}
          label="Completed"
          isActive={statusFilter === "completed"}
          onClick={() => toggleFilter("completed")}
        />
        <StatCard
          status="failed"
          count={counts.failed}
          label="Failed"
          isActive={statusFilter === "failed"}
          onClick={() => toggleFilter("failed")}
        />
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}

      {!isLoading && all.length === 0 && (
        <div className="rounded-md border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
          No designs yet. Create your first one to get started.
        </div>
      )}

      {!isLoading && all.length > 0 && rows.length === 0 && (
        <div className="rounded-md border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500">
          {`No designs currently ${STATUS_LABELS[statusFilter] || statusFilter}.`}
        </div>
      )}

      {rows.length > 0 && (
        <div className="rounded-md border border-gray-200 bg-white">
          <table className="w-full caption-bottom text-sm">
            <thead className="[&_tr]:border-b">
              <tr className="border-b transition-colors hover:bg-gray-100/50 data-[state=selected]:bg-gray-100">
                <th className="h-12 px-4 text-left align-middle font-medium text-gray-500">Preview</th>
                <th className="h-12 px-4 text-left align-middle font-medium text-gray-500">Name</th>
                <th className="h-12 px-4 text-left align-middle font-medium text-gray-500 hidden md:table-cell">Description</th>
                <th className="h-12 px-4 text-left align-middle font-medium text-gray-500">Status</th>
                <th className="h-12 px-4 text-right align-middle font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody className="[&_tr:last-child]:border-0">
              {rows.map((p: any) => (
                <tr key={p.id} className="border-b transition-colors hover:bg-gray-50 data-[state=selected]:bg-gray-100">
                  <td className="p-4 align-middle">
                    <div className="w-10 h-10 rounded-md bg-gray-100 flex items-center justify-center overflow-hidden border border-gray-200">
                      {p.versions && p.versions.length > 0 && p.versions[0].imagePath ? (
                          <img src={(import.meta.env.VITE_API_URL || 'http://localhost:5045/api').replace('/api', '') + p.versions[0].imagePath} alt="preview" className="w-full h-full object-cover mix-blend-multiply" />
                      ) : (
                          <Box size={16} className="text-gray-400" />
                      )}
                    </div>
                  </td>
                  <td className="p-4 align-middle font-medium">
                    <Link to={`/project/${p.id}`} className="text-blue-600 hover:underline">
                      {p.name}
                    </Link>
                  </td>
                  <td className="p-4 align-middle hidden md:table-cell text-gray-500 max-w-xs truncate">
                    {p.description}
                  </td>
                  <td className="p-4 align-middle">
                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 ${
                        p.status === 'completed' ? 'border-transparent bg-gray-100 text-gray-900' :
                        p.status === 'generating' ? 'border-transparent bg-blue-600 text-white' :
                        p.status === 'failed' ? 'border-transparent bg-red-500 text-white' :
                        'text-foreground'
                    }`}>
                      {STATUS_LABELS[p.status] || p.status}
                    </span>
                  </td>
                  <td className="p-4 align-middle text-right">
                    <div className="flex justify-end gap-1">
                      <Link
                        to={`/project/${p.id}`}
                        className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors hover:bg-gray-100 hover:text-gray-900 h-9 w-9"
                      >
                        <Pencil className="h-4 w-4" aria-hidden="true" />
                      </Link>
                      <button
                        onClick={(e) => { e.preventDefault(); deleteMutation.mutate(p.id); }}
                        className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors hover:bg-gray-100 hover:text-red-600 h-9 w-9 text-gray-500"
                      >
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  status: StatusFilter;
  count: number;
  label: string;
  isActive: boolean;
  onClick: () => void;
}

function StatCard({ status, count, label, isActive, onClick }: StatCardProps) {
  const { icon: Icon, ringClass, iconClass } = STATUS_CARD[status];
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={isActive}
      className={[
        "text-left transition-all rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600",
        isActive ? "ring-2 ring-blue-600" : `ring-1 ${ringClass} hover:ring-blue-600/40`,
      ].join(" ")}
    >
      <div className="border-0 shadow-none bg-white rounded-md">
        <div className="p-3 md:p-4 flex items-center gap-3">
          <Icon className={`h-5 w-5 shrink-0 ${iconClass}`} aria-hidden="true" />
          <div className="min-w-0">
            <div className="text-2xl font-semibold leading-tight text-gray-900">{count}</div>
            <div className="text-xs text-gray-500 truncate">{label}</div>
          </div>
        </div>
      </div>
    </button>
  );
}
