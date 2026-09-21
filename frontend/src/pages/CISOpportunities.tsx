import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { Globe, ArrowUpRight, Loader } from 'lucide-react';
import { api } from '../services/api';
import { Project, PaginatedResponse, GapStatus } from '../types';

const CISOpportunities = () => {
  const { data, isLoading } = useQuery('cis-opportunities', () => api.get<PaginatedResponse<Project>>('/api/projects/russia-opportunities', {
    params: { min_score: 50, limit: 30 }
  }));

  const projects = data?.data?.items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Возможности СНГ</h1>
        <p className="text-slate-400">Проекты с потенциалом для запуска на рынках СНГ</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader className="w-8 h-8 text-slate-400 animate-spin" /></div>
      ) : projects.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center">
          <Globe className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Возможности появятся после сбора данных</h3>
          <p className="text-slate-400">Как только проекты будут проанализированы, здесь появится список</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p: Project) => {
            const gapStyles: Record<GapStatus, string> = {
              green: 'bg-green-500/20 text-green-400',
              yellow: 'bg-yellow-500/20 text-yellow-400',
              red: 'bg-red-500/20 text-red-400',
            };
            return (
              <Link key={p.id} to={`/projects/${p.id}`} className="block bg-slate-800 rounded-xl p-6 border border-yellow-500/30 hover:bg-slate-700 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-white">{p.name}</h3>
                  <ArrowUpRight className="w-5 h-5 text-slate-400" />
                </div>
                <p className="text-sm text-slate-400 mb-4 line-clamp-2">{p.description}</p>
                <div className="flex gap-2">
                  <span className="bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded text-xs">🇷🇺 {p.russia_opportunity_score}</span>
                  <span className={`px-2 py-1 rounded text-xs ${gapStyles[p.gap_status] || gapStyles.yellow}`}>
                    {p.gap_status === 'green' ? '🟢' : p.gap_status === 'yellow' ? '🟡' : '🔴'}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CISOpportunities;
