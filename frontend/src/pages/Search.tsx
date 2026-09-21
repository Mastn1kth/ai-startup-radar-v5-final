import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Link } from 'react-router-dom';
import { Search, ArrowUpRight, Loader, Filter } from 'lucide-react';
import { api } from '../services/api';
import { Project, SearchResponse, GapStatus } from '../types';

interface SearchResultCardProps {
  project: Project;
}

const CATEGORIES = [
  '', 'ai_saas', 'ai_models', 'ai_agents', 'open_source',
  'mobile_apps', 'chrome_extensions', 'telegram', 'api_tools'
];

const SORT_OPTIONS = [
  { value: 'coolness_score', label: 'Крутость' },
  { value: 'startup_score', label: 'Стартап скор' },
  { value: 'viral_score', label: 'Вирусность' },
  { value: 'relevance', label: 'Релевантность' },
];

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('');
  const [sortBy, setSortBy] = useState('coolness_score');

  const { data, isLoading } = useQuery(
    ['search', searchQuery, category, sortBy],
    () => api.get<SearchResponse<Project>>('/api/search', {
      params: {
        q: searchQuery,
        category: category || undefined,
        sort_by: sortBy,
      }
    }),
    {
      enabled: searchQuery.length >= 2,
    }
  );

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(query);
  };

  const results = data?.data?.results || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Поиск проектов</h1>

      <form onSubmit={handleSearch} className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Поиск по названию, описанию, категории..."
          value={query}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-400"
        />
        <button
          type="submit"
          disabled={query.length < 2}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-2 bg-blue-600 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Найти
        </button>
      </form>

      {searchQuery && (
        <div className="flex flex-wrap items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={category}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setCategory(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="">Все категории</option>
            {CATEGORIES.filter(Boolean).map((cat: string) => (
              <option key={cat} value={cat}>{cat.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSortBy(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader className="w-8 h-8 text-slate-400 animate-spin" />
        </div>
      )}

      {searchQuery && !isLoading && (
        <div className="space-y-4">
          <div className="text-slate-400">
            Найдено {results.length} результатов по запросу &quot;{searchQuery}&quot;
          </div>

          {results.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              Ничего не найдено. Попробуйте другой запрос.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.map((project: Project) => (
                <SearchResultCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const SearchResultCard = ({ project }: SearchResultCardProps) => {
  const gapColors: Record<GapStatus, string> = {
    green: 'border-green-500/50',
    yellow: 'border-yellow-500/50',
    red: 'border-red-500/50',
  };

  return (
    <Link
      to={`/projects/${project.id}`}
      className={`block bg-slate-800 rounded-xl p-6 border ${gapColors[project.gap_status] || gapColors.yellow} hover:bg-slate-700 transition-colors`}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-white">{project.name}</h3>
        <ArrowUpRight className="w-5 h-5 text-slate-400" />
      </div>

      <p className="text-sm text-slate-400 mb-4 line-clamp-2">{project.description}</p>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs">
            🎯 {project.startup_score}
          </span>
          <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs">
            🇷🇺 {project.russia_opportunity_score}
          </span>
        </div>
        <span className="text-xs text-slate-500">{project.category}</span>
      </div>
    </Link>
  );
};

export default SearchPage;
