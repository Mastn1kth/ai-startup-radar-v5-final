import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Radar, TrendingUp, Globe, Eye, Search, Settings, FileText, Code, Map, Menu, X, LucideIcon } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

interface NavItem {
  path: string;
  icon: LucideIcon;
  label: string;
}

const Layout = ({ children }: LayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const location = useLocation();

  const navItems: NavItem[] = [
    { path: '/', icon: Radar, label: 'Dashboard' },
    { path: '/projects', icon: TrendingUp, label: 'Projects' },
    { path: '/trends', icon: TrendingUp, label: 'Trends' },
    { path: '/russia-opportunities', icon: Globe, label: 'Russia Opportunities' },
    { path: '/watchlist', icon: Eye, label: 'Watchlist' },
    { path: '/search', icon: Search, label: 'Search' },
    { path: '/clone-specs', icon: Code, label: 'Clone Specs' },
    { path: '/reports', icon: FileText, label: 'Reports' },
    { path: '/cis-opportunities', icon: Map, label: 'CIS Opp.' },
    { path: '/admin', icon: Settings, label: 'Admin' },
  ];

  return (
    <div className="flex h-screen bg-slate-900">
      <div className={`${sidebarOpen ? 'block' : 'hidden'} md:block w-64 bg-slate-800 border-r border-slate-700`}>
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <Radar className="w-8 h-8 text-blue-400" />
            <div>
              <h1 className="text-xl font-bold text-white">AI Startup Radar</h1>
              <p className="text-xs text-slate-400">2026 Edition</p>
            </div>
          </div>

          <nav className="space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                  }`}
                  onClick={() => setSidebarOpen(false)}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-slate-800 border-b border-slate-700 p-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="md:hidden text-slate-300 hover:text-white"
            >
              {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
            <div className="flex items-center gap-4">
              <div className="text-sm text-slate-400">
                Система активна | Обновление каждые 2 часа
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
