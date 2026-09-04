import { Link, useLocation } from 'react-router-dom';
import { LogOut, LayoutDashboard, PlusSquare, Hexagon } from 'lucide-react';

interface NavbarProps {
  onLogout: () => void;
}

export default function Navbar({ onLogout }: NavbarProps) {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path 
      ? "bg-gray-100 text-gray-900 shadow-sm ring-1 ring-gray-900/5" 
      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900";
  };

  return (
    <nav className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          
          {/* Logo & Brand */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 shadow-lg shadow-blue-500/30">
              <Hexagon className="text-white" size={22} strokeWidth={2.5} />
            </div>
            <span className="font-bold text-xl tracking-tight text-gray-900">
              Antigravity <span className="text-blue-600">3D</span>
            </span>
          </div>

          {/* Center Nav Links */}
          <div className="hidden md:flex items-center gap-2 px-1">
            <Link 
              to="/" 
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${isActive('/')}`}
            >
              <LayoutDashboard size={18} />
              Dashboard
            </Link>
            <Link 
              to="/new" 
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${isActive('/new')}`}
            >
              <PlusSquare size={18} />
              New Design
            </Link>
          </div>

          {/* Right side - Profile/Logout */}
          <div className="flex items-center gap-4">
            <button 
              onClick={onLogout}
              className="group flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-red-600 hover:bg-red-50 transition-all duration-200"
            >
              <span>Sign Out</span>
              <LogOut size={18} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
          
        </div>
      </div>
    </nav>
  );
}
