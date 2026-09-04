import {
  LogOut,
  Menu,
  X,
  LayoutDashboard,
  PlusSquare,
  Hexagon,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useState, type ReactNode } from "react";
import { useQuery } from '@tanstack/react-query';
import { fetchFusionStatus } from '../api/client';

interface Props {
  children: ReactNode;
  onLogout: () => void;
}

export default function AppLayout({ children, onLogout }: Props) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const { data: fusionStatus } = useQuery({
    queryKey: ['fusionStatus'],
    queryFn: fetchFusionStatus,
    refetchInterval: 30000,
    retry: false
  });

  const isFusionOnline = fusionStatus?.status === 'online';

  const sections = [
    {
      header: "3D Design Operations",
      items: [
        { to: "/", icon: LayoutDashboard, label: "Dashboard" },
        { to: "/new", icon: PlusSquare, label: "New Project" },
      ],
    }
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50/50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white shadow-sm sticky top-0 z-30">
        <div className="px-4 h-14 flex items-center justify-between gap-3">
          {/* Mobile menu toggle */}
          <button
            className="md:hidden p-1 rounded text-gray-500 hover:text-gray-900"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>

          {/* Brand */}
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 shadow-sm">
              <Hexagon className="text-white" size={18} strokeWidth={2.5} />
            </div>
            <span className="font-bold text-lg tracking-tight text-gray-900 hidden sm:block">
              Antigravity <span className="text-blue-600">3D</span>
            </span>
            <div className="hidden sm:flex ml-4 items-center gap-1.5 px-2 py-1 rounded-full bg-gray-50 border border-gray-200" title={fusionStatus?.reason || 'AutoFusion MCP Engine Status'}>
                <span className="relative flex h-2.5 w-2.5">
                  {isFusionOnline && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                  <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isFusionOnline ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                </span>
                <span className="text-xs font-medium text-gray-600">AutoFusion Engine {isFusionOnline ? 'Online' : 'Offline'}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            {/* Mobile status indicator */}
            <div className="sm:hidden flex items-center justify-center h-8 w-8 rounded-full border border-gray-200 bg-gray-50" title={`AutoFusion Engine ${isFusionOnline ? 'Online' : 'Offline'}`}>
                <span className={`h-2.5 w-2.5 rounded-full ${isFusionOnline ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
            </div>
            
            <button 
              onClick={onLogout}
              className="inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 border border-gray-200 bg-white hover:bg-gray-100 hover:text-gray-900 h-9 px-3"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={[
            "fixed inset-y-0 top-14 z-20 w-56 bg-white border-r border-gray-200 flex flex-col transition-transform duration-200",
            "md:static md:translate-x-0",
            sidebarOpen ? "translate-x-0" : "-translate-x-full",
          ].join(" ")}
        >
          <nav className="flex-1 py-3 overflow-y-auto" aria-label="Primary navigation">
            {sections.map((section, sectionIndex) => (
              <div key={section.header} className={sectionIndex === 0 ? "" : "mt-4"}>
                <div
                  className="px-4 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-500"
                >
                  {section.header}
                </div>
                {section.items.map(({ to, icon: Icon, label }) => (
                  <NavLink
                    key={to}
                    to={to}
                    onClick={() => setSidebarOpen(false)}
                    className={({ isActive }) =>
                      [
                        "flex items-center gap-3 px-4 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-blue-50 text-blue-600 border-r-2 border-blue-600"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100",
                      ].join(" ")
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                    {label}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        </aside>

        {/* Backdrop on mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 top-14 z-10 bg-black/30 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 overflow-y-auto md:ml-0 flex flex-col">
          <div className="flex-1 p-4 sm:p-6 lg:p-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
