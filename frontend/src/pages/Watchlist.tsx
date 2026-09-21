import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Link } from 'react-router-dom';
import { Search, ArrowUpRight, Star, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { WatchlistItem } from '../types';

interface WatchlistCardProps {
  item: WatchlistItem;
  onRemove: () => void;
}

const Watchlist = () => {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery('watchlist', () => api.get<{ items: WatchlistItem[] }>('/api/watchlist'));
  const [searchTerm, setSearchTerm] = useState('');

  const removeMutation = useMutation(
    (projectId: number) => api.delete(`/api/watchlist/${projectId}`),
    {
      onMutate: async (projectId: number) => {
        await queryClient.cancelQueries('watchlist');
        const previous = queryClient.getQueryData('watchlist');
        queryClient.setQueryData('watchlist', (old: any) => {
          if (!old) return old;
          return { ...old, data: { ...old.data, items: old.data.items.filter((i: WatchlistItem) => i.project.id !== projectId) } };
        });
        return { previous };
      },
      onError: (err: Error, _projectId: number, context: any) => {
        queryClient.setQueryData('watchlist', context.previous);
        console.error('Failed to remove from watchlist:', err);
      },
      onSettled: () => {
        queryClient.invalidateQueries('watchlist');
      },
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Загрузка...</div>
      </div>
    );
  }

  const items = data?.data?.items || [];

  const filteredItems = items.filter((item: WatchlistItem) =>
    item.project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.project.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Watchlist</h1>
        <div className="text-sm text-slate-400">{items.length} проектов</div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Поиск в watchlist..."
          value={searchTerm}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-10 pr-4 py-3 text-white placeholder-slate-400"
        />
      </div>

      {filteredItems.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          {items.length === 0 ? (
            <div>
              <Star className="w-12 h-12 mx-auto mb-4 text-slate-600" />
              <p>Ваш watchlist пуст</p>
              <p className="text-sm mt-2">Добавляйте проекты для отслеживания</p>
            </div>
          ) : (
            <p>Ничего не найдено</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((item: WatchlistItem) => (
            <WatchlistCard key={item.id} item={item} onRemove={() => removeMutation.mutate(item.project.id)} />
          ))}
        </div>
      )}
    </div>
  );
};

const WatchlistCard = ({ item, onRemove }: WatchlistCardProps) => {
  const project = item.project;

  return (
    <div className="bg-slate-800 rounded-xl p-6">
      <div className="flex items-start justify-between mb-3">
        <Link to={`/projects/${project.id}`} className="flex-1">
          <h3 className="font-semibold text-white hover:text-blue-400 transition-colors">{project.name}</h3>
        </Link>
        <button
          onClick={onRemove}
          className="text-slate-400 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-5 h-5" />
        </button>
      </div>

      <p className="text-sm text-slate-400 mb-4 line-clamp-2">{project.description}</p>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <div className="bg-slate-700 rounded-lg p-2 text-center">
          <div className="text-xs text-slate-400">Startup Score</div>
          <div className="text-lg font-bold text-blue-400">{project.startup_score}</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-2 text-center">
          <div className="text-xs text-slate-400">Russia Score</div>
          <div className="text-lg font-bold text-green-400">{project.russia_opportunity_score}</div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-500">
          Добавлен: {new Date(item.added_at).toLocaleDateString('ru-RU')}
        </span>
        <Link
          to={`/projects/${project.id}`}
          className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
        >
          Подробнее
          <ArrowUpRight className="w-4 h-4" />
        </Link>
      </div>

      {item.notes && (
        <div className="mt-3 p-3 bg-slate-700 rounded-lg text-sm text-slate-300">
          {item.notes}
        </div>
      )}
    </div>
  );
};

export default Watchlist;
