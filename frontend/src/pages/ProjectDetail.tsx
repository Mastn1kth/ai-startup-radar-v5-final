import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import { ArrowLeft, ExternalLink, Github, Star, Heart, TrendingUp, Globe, AlertTriangle, CheckCircle, XCircle, LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Project, GapStatus } from '../types';

interface ScoreBarProps {
  label: string;
  value: number;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'orange';
}

interface RussiaCheckProps {
  label: string;
  value: boolean;
  isWarning?: boolean;
}

interface MetricItemProps {
  icon: LucideIcon;
  label: string;
  value: number | string;
}

const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading } = useQuery(['project', id], () => api.get<Project>(`/api/projects/${id}`));

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Загрузка...</div>
      </div>
    );
  }

  const project = data?.data;
  if (!project) {
    return <div className="text-center py-12 text-slate-400">Проект не найден</div>;
  }

  const gapColors: Record<GapStatus, string> = {
    green: 'bg-green-500/20 text-green-400 border-green-500/50',
    yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    red: 'bg-red-500/20 text-red-400 border-red-500/50',
  };

  const gapLabels: Record<GapStatus, string> = {
    green: '🟢 Аналогов нет - отличная возможность!',
    yellow: '🟡 Есть слабые аналоги - можно конкурировать',
    red: '🔴 Рынок занят - сложно войти',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <Link to="/projects" className="text-slate-400 hover:text-white">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <h1 className="text-3xl font-bold text-white">{project.name}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="bg-slate-700 px-3 py-1 rounded-full text-sm text-slate-300">{project.category}</span>
              <span className={`px-3 py-1 rounded-full text-sm border ${gapColors[project.gap_status] || gapColors.yellow}`}>
                {gapLabels[project.gap_status] || gapLabels.yellow}
              </span>
            </div>

            <p className="text-slate-300 mb-4">{project.description}</p>

            {project.ai_summary && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">🤖 AI Анализ</h3>
                <p className="text-slate-400">{project.ai_summary}</p>
              </div>
            )}

            {project.problem_solved && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">🎯 Решаемая проблема</h3>
                <p className="text-slate-400">{project.problem_solved}</p>
              </div>
            )}

            {project.target_audience && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-white mb-2">👥 Целевая аудитория</h3>
                <p className="text-slate-400">{project.target_audience}</p>
              </div>
            )}

            <div className="flex items-center gap-4">
              {project.website && (
                <a
                  href={project.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-blue-400 hover:text-blue-300"
                >
                  <ExternalLink className="w-4 h-4" />
                  Website
                </a>
              )}
              {project.github_url && (
                <a
                  href={project.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-slate-400 hover:text-white"
                >
                  <Github className="w-4 h-4" />
                  GitHub
                </a>
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-semibold text-white mb-4">🇷🇺 Возможность для России</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <RussiaCheck label="Аналог в России" value={project.has_russia_analog} />
              <RussiaCheck label="Аналог в СНГ" value={project.has_cis_analog} />
              <RussiaCheck label="Сильный конкурент" value={project.has_strong_competitor} />
              <RussiaCheck label="Слабый конкурент" value={project.has_weak_competitor} />
              <RussiaCheck label="Можно локализовать" value={project.can_localize} />
              <RussiaCheck label="Быстрый запуск" value={project.can_quick_launch} />
              <RussiaCheck label="Юр. ограничения" value={project.legal_restrictions} isWarning />
            </div>

            {project.estimated_budget && (
              <div className="mt-4 p-4 bg-slate-700 rounded-lg">
                <div className="text-sm text-slate-400">Примерный бюджет запуска аналога:</div>
                <div className="text-xl font-bold text-green-400">{project.estimated_budget}</div>
              </div>
            )}

            {project.estimated_timeline && (
              <div className="mt-4 p-4 bg-slate-700 rounded-lg">
                <div className="text-sm text-slate-400">Примерный срок разработки MVP:</div>
                <div className="text-xl font-bold text-blue-400">{project.estimated_timeline}</div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">📊 Скоринг</h3>

            <div className="space-y-4">
              <ScoreBar label="Startup Score" value={project.startup_score} color="blue" />
              <ScoreBar label="Russia Opportunity" value={project.russia_opportunity_score} color="green" />
              <ScoreBar label="Money Score" value={project.money_score} color="yellow" />
              <ScoreBar label="Viral Score" value={project.viral_score} color="purple" />
              <ScoreBar label="Copy Score" value={project.copy_score} color="orange" />
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">📈 Метрики</h3>

            <div className="space-y-3">
              <MetricItem icon={Star} label="GitHub Stars" value={project.github_stars} />
              <MetricItem icon={Heart} label="Likes" value={project.likes} />
              <MetricItem icon={TrendingUp} label="Growth Potential" value={`${project.growth_potential}/100`} />
              <MetricItem icon={Globe} label="Market Size" value={project.market_size} />
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">💰 Монетизация</h3>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Тип:</span>
                <span className="text-white">{project.monetization_type || 'Unknown'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Подписка:</span>
                <span className={project.has_subscription ? 'text-green-400' : 'text-red-400'}>
                  {project.has_subscription ? '✅' : '❌'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Freemium:</span>
                <span className={project.has_freemium ? 'text-green-400' : 'text-red-400'}>
                  {project.has_freemium ? '✅' : '❌'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-white mb-4">👥 Команда</h3>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Один founder:</span>
                <span className={project.solo_founder_possible ? 'text-green-400' : 'text-red-400'}>
                  {project.solo_founder_possible ? '✅ Возможно' : '❌ Сложно'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Маленькая команда:</span>
                <span className={project.small_team_possible ? 'text-green-400' : 'text-red-400'}>
                  {project.small_team_possible ? '✅ Возможно' : '❌ Сложно'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Сложность:</span>
                <span className="text-white">{project.implementation_complexity}/100</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ScoreBar = ({ label, value, color }: ScoreBarProps) => {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
  };

  const percentage = value || 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-400">{label}</span>
        <span className="text-sm font-semibold text-white">{percentage}</span>
      </div>
      <div className="w-full bg-slate-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const RussiaCheck = ({ label, value, isWarning }: RussiaCheckProps) => {
  if (isWarning) {
    return (
      <div className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
        <span className="text-slate-300">{label}</span>
        <span className={value ? 'text-red-400' : 'text-green-400'}>
          {value ? <AlertTriangle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
      <span className="text-slate-300">{label}</span>
      <span className={value ? 'text-green-400' : 'text-red-400'}>
        {value ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
      </span>
    </div>
  );
};

const MetricItem = ({ icon: Icon, label, value }: MetricItemProps) => (
  <div className="flex items-center justify-between">
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4 text-slate-400" />
      <span className="text-slate-400">{label}</span>
    </div>
    <span className="text-white font-semibold">{value || 0}</span>
  </div>
);

export default ProjectDetail;
