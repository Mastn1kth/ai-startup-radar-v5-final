import React from 'react';
import { useQuery } from 'react-query';
import { FileText, Loader } from 'lucide-react';
import { api } from '../services/api';
import { Report, ReportsResponse } from '../types';

const Reports = () => {
  const { data, isLoading } = useQuery('daily-reports', () => api.get<ReportsResponse>('/api/reports/daily', { params: { limit: 14 } }));
  const reports = data?.data?.reports || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Отчеты</h1>
        <p className="text-slate-400">Ежедневные дайджесты проектов</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Loader className="w-8 h-8 text-slate-400 animate-spin" /></div>
      ) : reports.length === 0 ? (
        <div className="bg-slate-800 rounded-xl p-12 text-center">
          <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">Отчетов пока нет</h3>
          <p className="text-slate-400">Первый отчет появится через 24 часа после запуска</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((r: Report, i: number) => (
            <div key={i} className="bg-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">{new Date(r.date).toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</h3>
                <span className={`px-2 py-1 rounded text-xs ${r.sent_to_telegram ? 'bg-green-500/20 text-green-400' : 'bg-slate-600 text-slate-300'}`}>
                  {r.sent_to_telegram ? 'Отправлен' : 'Не отправлен'}
                </span>
              </div>
              {r.top_projects && r.top_projects.length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">Топ проектов:</p>
                  <div className="flex flex-wrap gap-2">
                    {r.top_projects.map((p: { name?: string } | string, j: number) => (
                      <span key={j} className="bg-slate-700 text-slate-300 px-3 py-1 rounded text-sm">{(typeof p === 'object' ? p.name : p) || p}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Reports;
