import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Settings, Cpu, BarChart3, RefreshCw, MessageCircle } from 'lucide-react';
import { api } from '../services/api';
import { AdminStats, AdminSetting, AdminSettingsResponse } from '../types';

interface StatItemProps {
  label: string;
  value: number;
}

const Admin = () => {
  const queryClient = useQueryClient();

  const { data: stats, isLoading: statsLoading } = useQuery('admin-stats', () => api.get<AdminStats>('/api/admin/stats'));
  const { data: settingsData, isLoading: settingsLoading } = useQuery('admin-settings', () => api.get<AdminSettingsResponse>('/api/admin/settings'));

  const settings = settingsData?.data?.settings || [];
  const statsData = stats?.data || {} as AdminStats;

  const aiSetting = settings.find((s: AdminSetting) => s.key === 'ai_analysis_enabled');
  const [isAiEnabled, setIsAiEnabled] = useState(aiSetting ? aiSetting.value === 'true' : true);

  const updateMutation = useMutation(
    (data: { key: string; value: string }) => api.put('/api/admin/settings', data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('admin-settings');
        queryClient.invalidateQueries('admin-stats');
      },
    }
  );

  const toggleAi = () => {
    const newValue = isAiEnabled ? 'false' : 'true';
    setIsAiEnabled(!isAiEnabled);
    updateMutation.mutate({ key: 'ai_analysis_enabled', value: newValue });
  };

  if (statsLoading || settingsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-slate-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Администрирование</h1>
          <p className="text-slate-400">Управление системой</p>
        </div>
      </div>

      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <div className="flex items-center gap-3">
          <MessageCircle className="w-5 h-5 text-blue-400" />
          <p className="text-sm text-slate-400">
            Администрирование через Telegram бота: отправьте <code className="text-blue-400">/toggle_ai</code> чтобы вкл/выкл AI анализ, <code className="text-blue-400">/status</code> для статуса
          </p>
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-purple-500/20">
              <Cpu className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">AI Анализ проектов</h3>
              <p className="text-sm text-slate-400">
                {isAiEnabled
                  ? 'AI анализ включен — все новые проекты проходят полный AI анализ через Ollama'
                  : 'AI анализ выключен — проекты оцениваются только алгоритмически (метрики, GitHub, категории)'}
              </p>
            </div>
          </div>
          <button
            onClick={toggleAi}
            disabled={updateMutation.isLoading}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
              isAiEnabled ? 'bg-green-500' : 'bg-slate-600'
            }`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                isAiEnabled ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
        {updateMutation.isLoading && (
          <p className="text-sm text-blue-400 mt-2">Сохранение...</p>
        )}
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Статистика системы</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatItem label="Всего проектов" value={statsData.total_projects || 0} />
          <StatItem label="Активных" value={statsData.active_projects || 0} />
          <StatItem label="Проанализировано AI" value={statsData.analyzed_by_ai || 0} />
          <StatItem label="Оценено (скор)" value={statsData.scored || 0} />
          <StatItem label="Источников" value={statsData.sources_count || 0} />
          <StatItem label="Активных источников" value={statsData.active_sources || 0} />
        </div>
      </div>

      <div className="bg-slate-800 rounded-xl p-6">
        <div className="flex items-center gap-3 mb-6">
          <Settings className="w-5 h-5 text-slate-400" />
          <h3 className="text-lg font-semibold text-white">Настройки</h3>
        </div>
        <div className="space-y-3">
          {settings.length === 0 ? (
            <p className="text-slate-400">Настроек пока нет</p>
          ) : (
            settings.map((s: AdminSetting) => (
              <div key={s.key} className="flex items-center justify-between p-4 bg-slate-700 rounded-lg">
                <div>
                  <div className="text-sm font-medium text-white">{s.key}</div>
                  <div className="text-xs text-slate-400 mt-1">{s.value}</div>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${
                  s.value === 'true' ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-300'
                }`}>
                  {s.value}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const StatItem = ({ label, value }: StatItemProps) => (
  <div className="bg-slate-700 rounded-lg p-4">
    <div className="text-2xl font-bold text-white">{value}</div>
    <div className="text-sm text-slate-400">{label}</div>
  </div>
);

export default Admin;
