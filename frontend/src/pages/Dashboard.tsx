import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { TrendingUp, Globe, Zap, Clock, Star, AlertTriangle, LucideIcon } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { api } from '../services/api';
import { Project, Trend, DashboardStats, CategoryData } from '../types';

interface StatCardProps {
  icon: LucideIcon;
  title: string;
  value: number;
  color: 'blue' | 'green' | 'yellow' | 'purple';
}

interface ProjectCardProps {
  project: Project;
}

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useQuery('dashboard-stats', () => api.get<DashboardStats>('/api/dashboard/stats'));
  const { data: categories, isLoading: catLoading } = useQuery('top-categories', () => api.get<{ categories: CategoryData[] }>('/api/dashboard/top-categories'));
  const { data: featured, isLoading: featLoading } = useQuery('featured-projects', () => api.get<{ items: Project[] }>('/api/projects/featured'));
  const { data: trends, isLoading: trendsLoading } = useQuery('exploding-trends', () => api.get<{ items: Trend[] }>('/api/trends/exploding'));

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

  if (statsLoading || catLoading || featLoading || trendsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Загрузка...</div>
      </div>
    );
  }

  const statsData = stats?.data || {} as DashboardStats;
  const categoriesData = categories?.data?.categories || [];
  const featuredProjects = featured?.data?.items || [];
  const explodingTrends = trends?.data?.items || [];

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">AI Startup Radar Dashboard</h1>
        <p className="text-slate-400">Обнаружение перспективных стартапов и AI-продуктов раньше рынка</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Zap} title="Всего проектов" value={statsData.total_projects || 0} color="blue" />
        <StatCard icon={Star} title="Высокий потенциал" value={statsData.high_potential || 0} color="green" />
        <StatCard icon={Globe} title="Возможности РФ" value={statsData.russia_opportunities || 0} color="yellow" />
        <StatCard icon={Clock} title="Новые за 24ч" value={statsData.new_24h || 0} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Распределение по категориям</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoriesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Bar dataKey="count" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Топ категории</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoriesData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: { name: string; percent: number }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {categoriesData.map((_entry: CategoryData, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Топ проекты</h3>
          <Link to="/projects" className="text-blue-400 hover:text-blue-300 text-sm">Все проекты →</Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {featuredProjects.map((project: Project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Взрывные тренды</h3>
          <Link to="/trends" className="text-blue-400 hover:text-blue-300 text-sm">Все тренды →</Link>
        </div>
        <div className="space-y-3">
          {explodingTrends.map((trend: Trend) => (
            <div key={trend.id} className="flex items-center justify-between p-4 bg-slate-700 rounded-lg">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <div>
                  <div className="font-medium text-white">{trend.name}</div>
                  <div className="text-sm text-slate-400">{trend.category}</div>
                </div>
              </div>
              <div className="text-green-400 font-bold">+{trend.growth_percent}%</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ icon: Icon, title, value, color }: StatCardProps) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500/20 text-blue-400',
    green: 'bg-green-500/20 text-green-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    purple: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <div className="text-2xl font-bold text-white">{value}</div>
          <div className="text-sm text-slate-400">{title}</div>
        </div>
      </div>
    </div>
  );
};

const ProjectCard = ({ project }: ProjectCardProps) => {
  const gapColors: Record<string, string> = {
    green: 'bg-green-500/20 text-green-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    red: 'bg-red-500/20 text-red-400',
  };

  return (
    <Link to={`/projects/${project.id}`} className="block bg-slate-700 rounded-lg p-4 hover:bg-slate-600 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium text-white truncate">{project.name}</h4>
        <span className={`px-2 py-1 rounded text-xs ${gapColors[project.gap_status] || gapColors.yellow}`}>
          {project.gap_status === 'green' ? '🟢' : project.gap_status === 'red' ? '🔴' : '🟡'}
        </span>
      </div>
      <p className="text-sm text-slate-400 mb-3 line-clamp-2">{project.description}</p>
      <div className="flex items-center justify-between text-sm">
        <div className="text-blue-400">🎯 {project.startup_score}/100</div>
        <div className="text-green-400">🇷🇺 {project.russia_opportunity_score}/100</div>
      </div>
      <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
        {project.github_stars > 0 && <span>⭐ {project.github_stars}</span>}
        {project.likes > 0 && <span>👍 {project.likes}</span>}
      </div>
    </Link>
  );
};

export default Dashboard;
