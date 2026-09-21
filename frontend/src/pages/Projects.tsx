import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Project, PaginatedResponse } from '../types';

interface ProjectCardProps {
  project: Project;
}

interface ScoreBadgeProps {
  label: string;
  value: number;
  color: 'blue' | 'green' | 'yellow' | 'purple';
}

const Projects = () => {
  const [category, setCategory] = useState('');
  const [gapStatus, setGapStatus] = useState('');
  const [minScore, setMinScore] = useState('');
  const [sortBy, setSortBy] = useState('startup_score');
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery(
    ['projects', category, gapStatus, minScore, sortBy, page],
    () => api.get<PaginatedResponse<Project>>('/api/projects', {
      params: {
        category: category || undefined,
        gap_status: gapStatus || undefined,
        min_score: minScore || undefined,
        sort_by: sortBy,
        limit: 50,
        offset: page * 50,
      }
    })
  );

  const projects = data?.data?.items || [];

  const categories = [
    { value: '', label: 'Все категории' },
    { value: 'ai_saas', label: 'AI SaaS' },
    { value: 'startups', label: 'Startups' },
    { value: 'open_source', label: 'Open Source' },
    { value: 'ai_models', label: 'AI Models' },
    { value: 'ai_agents', label: 'AI Agents' },
    { value: 'mcp', label: 'MCP Tools' },
    { value: 'mobile_apps', label: 'Mobile Apps' },
    { value: 'telegram', label: 'Telegram' },
    { value: 'chrome_extensions', label: 'Chrome Extensions' },
  ];

  const gapStatuses = [
    { value: '', label: 'Все статусы' },
    { value: 'green', label: '🟢 Аналогов нет' },
    { value: 'yellow', label: '🟡 Слабые аналоги' },
    { value: 'red', label: '🔴 Рынок занят' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Проекты</h1>
        <div className="text-sm text-slate-400">
          Всего: {data?.data?.total || 0}
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-4 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Категория</label>
            <select
              value={category}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategory(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Статус рынка РФ</label>
            <select
              value={gapStatus}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setGapStatus(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            >
              {gapStatuses.map((status) => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Минимальный скор</label>
            <input
              type="number"
              value={minScore}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMinScore(e.target.value)}
              placeholder="0-100"
              min="0"
              max="100"
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">Сортировка</label>
            <select
              value={sortBy}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSortBy(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
            >
              <option value="startup_score">Startup Score</option>
              <option value="russia_opportunity_score">Russia Opportunity</option>
              <option value="money_score">Money Score</option>
              <option value="viral_score">Viral Score</option>
              <option value="copy_score">Copy Score</option>
              <option value="discovered_at">Дата обнаружения</option>
            </select>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400">Загрузка...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project: Project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}

      <div className="flex items-center justify-center gap-4">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="px-4 py-2 bg-slate-700 rounded-lg text-white disabled:opacity-50"
        >
          ← Назад
        </button>
        <span className="text-white">Страница {page + 1}</span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={projects.length < 50}
          className="px-4 py-2 bg-slate-700 rounded-lg text-white disabled:opacity-50"
        >
          Вперед →
        </button>
      </div>
    </div>
  );
};

const ProjectCard = ({ project }: ProjectCardProps) => {
  const gapColors: Record<string, string> = {
    green: 'border-green-500/50',
    yellow: 'border-yellow-500/50',
    red: 'border-red-500/50',
  };

  const gapLabels: Record<string, string> = {
    green: '🟢',
    yellow: '🟡',
    red: '🔴',
  };

  return (
    <Link
      to={`/projects/${project.id}`}
      className={`block bg-slate-800 rounded-xl p-6 border ${gapColors[project.gap_status] || gapColors.yellow} hover:bg-slate-700 transition-colors`}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-white truncate">{project.name}</h3>
        <span className="text-lg">{gapLabels[project.gap_status] || gapLabels.yellow}</span>
      </div>

      <p className="text-sm text-slate-400 mb-4 line-clamp-2">{project.description}</p>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <ScoreBadge label="Startup" value={project.startup_score} color="blue" />
        <ScoreBadge label="Russia" value={project.russia_opportunity_score} color="green" />
        <ScoreBadge label="Money" value={project.money_score} color="yellow" />
        <ScoreBadge label="Viral" value={project.viral_score} color="purple" />
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          {project.github_stars > 0 && <span>⭐ {project.github_stars}</span>}
          {project.likes > 0 && <span>👍 {project.likes}</span>}
        </div>
        <span className="bg-slate-700 px-2 py-1 rounded">{project.category}</span>
      </div>
    </Link>
  );
};

const ScoreBadge = ({ label, value, color }: ScoreBadgeProps) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500/20 text-blue-400',
    green: 'bg-green-500/20 text-green-400',
    yellow: 'bg-yellow-500/20 text-yellow-400',
    purple: 'bg-purple-500/20 text-purple-400',
  };

  return (
    <div className={`px-2 py-1 rounded text-xs ${colorClasses[color]}`}>
      {label}: {value || 'N/A'}
    </div>
  );
};

export default Projects;
