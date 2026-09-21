import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { Globe, ArrowUpRight, TrendingUp } from 'lucide-react';
import { api } from '../services/api';
import { Project, PaginatedResponse } from '../types';

interface OpportunityCardProps {
  project: Project;
}

const RussiaOpportunities = () => {
  const { data, isLoading } = useQuery('russia-opportunities', () =>
    api.get<PaginatedResponse<Project>>('/api/projects/russia-opportunities', { params: { min_score: 60, limit: 50 } })
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Загрузка...</div>
      </div>
    );
  }

  const projects = data?.data?.items || [];

  const greenProjects = projects.filter((p: Project) => p.gap_status === 'green');
  const yellowProjects = projects.filter((p: Project) => p.gap_status === 'yellow');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <Globe className="w-8 h-8 text-green-400" />
        <div>
          <h1 className="text-2xl font-bold text-white">Возможности для России</h1>
          <p className="text-slate-400">Проекты с высоким потенциалом локализации</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="text-3xl font-bold text-white mb-1">{projects.length}</div>
          <div className="text-sm text-slate-400">Всего возможностей</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6 border border-green-500/30">
          <div className="text-3xl font-bold text-green-400 mb-1">{greenProjects.length}</div>
          <div className="text-sm text-slate-400">🟢 Аналогов нет</div>
        </div>
        <div className="bg-slate-800 rounded-xl p-6 border border-yellow-500/30">
          <div className="text-3xl font-bold text-yellow-400 mb-1">{yellowProjects.length}</div>
          <div className="text-sm text-slate-400">🟡 Слабые аналоги</div>
        </div>
      </div>

      {greenProjects.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">🟢 Лучшие возможности (аналогов нет)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {greenProjects.map((project: Project) => (
              <OpportunityCard key={project.id} project={project} />
            ))}
          </div>
        </div>
      )}

      {yellowProjects.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">🟡 Есть слабые аналоги (можно конкурировать)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {yellowProjects.map((project: Project) => (
              <OpportunityCard key={project.id} project={project} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const OpportunityCard = ({ project }: OpportunityCardProps) => {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="block bg-slate-700 rounded-lg p-4 hover:bg-slate-600 transition-colors"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-white truncate">{project.name}</h3>
        <ArrowUpRight className="w-4 h-4 text-slate-400" />
      </div>

      <p className="text-sm text-slate-400 mb-3 line-clamp-2">{project.description}</p>

      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1">
          <TrendingUp className="w-4 h-4 text-blue-400" />
          <span className="text-sm text-blue-400">{project.startup_score}/100</span>
        </div>
        <div className="flex items-center gap-1">
          <Globe className="w-4 h-4 text-green-400" />
          <span className="text-sm text-green-400">{project.russia_opportunity_score}/100</span>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        {project.github_stars > 0 && <span>⭐ {project.github_stars}</span>}
        {project.likes > 0 && <span>👍 {project.likes}</span>}
        <span className="bg-slate-600 px-2 py-1 rounded">{project.category}</span>
      </div>
    </Link>
  );
};

export default RussiaOpportunities;
