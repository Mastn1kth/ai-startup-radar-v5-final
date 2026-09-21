import React from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { Code, ArrowUpRight, Loader } from 'lucide-react';
import { api } from '../services/api';
import { Project, PaginatedResponse } from '../types';

const CloneSpecs = () => {
  const { data, isLoading } = useQuery('clone-specs', () => api.get<PaginatedResponse<Project>>('/api/projects/ranked', {
    params: { sort_by: 'copy_score', limit: 20, min_score: 70 }
  }));

  const projects = data?.data?.items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Clone Specs</h1>
        <p className="text-slate-400">Проекты, которые проще всего клонировать (высокий Copy Score)</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader className="w-8 h-8 text-slate-400 animate-spin" /></div>
      ) : projects.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center">
          <Code className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Нет проектов для клонирования</h3>
          <p className="text-slate-400">Появятся после сбора данных и AI анализа</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p: Project) => (
            <Link key={p.id} to={`/projects/${p.id}`} className="block bg-slate-800 rounded-xl p-6 border border-green-500/30 hover:bg-slate-700 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-semibold text-white">{p.name}</h3>
                <ArrowUpRight className="w-5 h-5 text-slate-400" />
              </div>
              <p className="text-sm text-slate-400 mb-4 line-clamp-2">{p.description}</p>
              <div className="flex gap-2">
                <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs">📋 {p.copy_score}</span>
                <span className="text-xs text-slate-500">{p.category}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default CloneSpecs;
