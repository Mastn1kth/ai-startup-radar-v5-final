export type GapStatus = 'green' | 'yellow' | 'red';

export interface Project {
  id: number;
  name: string;
  description: string;
  category: string;
  startup_score: number;
  russia_opportunity_score: number;
  money_score: number;
  viral_score: number;
  copy_score: number;
  gap_status: GapStatus;
  github_stars: number;
  likes: number;
  growth_potential: number;
  market_size: string;
  monetization_type: string;
  has_subscription: boolean;
  has_freemium: boolean;
  website: string;
  github_url: string;
  ai_summary: string;
  problem_solved: string;
  target_audience: string;
  has_russia_analog: boolean;
  has_cis_analog: boolean;
  has_strong_competitor: boolean;
  has_weak_competitor: boolean;
  can_localize: boolean;
  can_quick_launch: boolean;
  legal_restrictions: boolean;
  estimated_budget: string;
  estimated_timeline: string;
  solo_founder_possible: boolean;
  small_team_possible: boolean;
  implementation_complexity: number;
  discovered_at: string;
}

export interface Trend {
  id: number;
  name: string;
  description: string;
  category: string;
  growth_percent: number;
}

export interface WatchlistItem {
  id: number;
  project: Project;
  added_at: string;
  notes: string;
}

export interface DashboardStats {
  total_projects: number;
  high_potential: number;
  russia_opportunities: number;
  new_24h: number;
}

export interface CategoryData {
  name: string;
  count: number;
}

export interface AdminStats {
  total_projects: number;
  active_projects: number;
  analyzed_by_ai: number;
  scored: number;
  sources_count: number;
  active_sources: number;
}

export interface AdminSetting {
  key: string;
  value: string;
}

export interface Report {
  date: string;
  sent_to_telegram: boolean;
  top_projects?: Array<{ name?: string } | string>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total?: number;
}

export interface SearchResponse<T> {
  results: T[];
}

export interface ReportsResponse {
  reports: Report[];
}

export interface AdminSettingsResponse {
  settings: AdminSetting[];
}

export interface DashboardStatsResponse {
  total_projects: number;
  high_potential: number;
  russia_opportunities: number;
  new_24h: number;
}
