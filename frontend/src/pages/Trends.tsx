import React from 'react';
import { useQuery } from 'react-query';
import { TrendingUp, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import { Trend } from '../types';

interface TrendCardProps {
  trend: Trend;
  isExploding?: boolean;
}

const Trends = () => {
  const { data: trendsData, isLoading: trendsLoading } = useQuery('trends', () => api.get<{ items: Trend[] }>('/api/trends'));
  const { data: explodingData, isLoading: explodingLoading } = useQuery('exploding-trends', () => api.get<{ items: Trend[] }>('/api/trends/exploding'));

  if (trendsLoading || explodingLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Загрузка...</div>
      </div>
    );
  }

  const trends = trendsData?.data?.items || [];
  const exploding = explodingData?.data?.items || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Тренды</h1>

      {exploding.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-6 h-6 text-yellow-400" />
            <h2 className="text-xl font-semibold text-white">🚀 Взрывные тренды</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {exploding.map((trend: Trend) => (
              <TrendCard key={trend.id} trend={trend} isExploding />
            ))}
          </div>
        </div>
      )}

      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-6 h-6 text-blue-400" />
          <h2 className="text-xl font-semibold text-white">📈 Все тренды</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {trends.map((trend: Trend) => (
            <TrendCard key={trend.id} trend={trend} />
          ))}
        </div>
      </div>
    </div>
  );
};

const TrendCard = ({ trend, isExploding }: TrendCardProps) => {
  const growth = trend.growth_percent || 0;

  return (
    <div className={`bg-slate-700 rounded-lg p-4 ${isExploding ? 'border border-yellow-500/50' : ''}`}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-white">{trend.name}</h3>
        {isExploding && <AlertTriangle className="w-5 h-5 text-yellow-400" />}
      </div>

      <p className="text-sm text-slate-400 mb-3">{trend.description}</p>

      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-500">{trend.category}</span>
        <div className={`flex items-center gap-1 ${growth > 0 ? 'text-green-400' : 'text-red-400'}`}>
          <ArrowUpRight className="w-4 h-4" />
          <span className="font-semibold">+{growth}%</span>
        </div>
      </div>

      {isExploding && (
        <div className="mt-3 p-2 bg-yellow-500/20 rounded text-sm text-yellow-400">
          ⚡ Резкий рост интереса! Рассмотрите запуск продукта в этой нише.
        </div>
      )}
    </div>
  );
};

export default Trends;
