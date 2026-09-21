-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Таблица источников данных
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(500),
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    scrape_interval_minutes INTEGER DEFAULT 120,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица проектов/стартапов
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    source_id UUID REFERENCES sources(id),
    source_url VARCHAR(1000),
    website VARCHAR(500),
    author VARCHAR(255),
    author_url VARCHAR(500),
    
    -- Метрики
    rating DECIMAL(3,2),
    likes INTEGER DEFAULT 0,
    reviews_count INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    users_count INTEGER DEFAULT 0,
    
    -- GitHub метрики
    github_url VARCHAR(500),
    github_stars INTEGER DEFAULT 0,
    github_forks INTEGER DEFAULT 0,
    github_language VARCHAR(100),
    
    -- Инвестиции
    investment_amount DECIMAL(15,2),
    investment_stage VARCHAR(50),
    investors TEXT,
    
    -- Даты
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- AI Аналитика
    ai_summary TEXT,
    problem_solved TEXT,
    target_audience TEXT,
    monetization_type VARCHAR(100),
    has_subscription BOOLEAN DEFAULT false,
    has_freemium BOOLEAN DEFAULT false,
    growth_potential INTEGER CHECK (growth_potential BETWEEN 0 AND 100),
    viral_potential INTEGER CHECK (viral_potential BETWEEN 0 AND 100),
    money_potential INTEGER CHECK (money_potential BETWEEN 0 AND 100),
    failure_probability INTEGER CHECK (failure_probability BETWEEN 0 AND 100),
    competition_level INTEGER CHECK (competition_level BETWEEN 0 AND 100),
    market_size VARCHAR(255),
    implementation_complexity INTEGER CHECK (implementation_complexity BETWEEN 0 AND 100),
    required_team VARCHAR(255),
    required_investment VARCHAR(255),
    solo_founder_possible BOOLEAN DEFAULT false,
    small_team_possible BOOLEAN DEFAULT false,
    mvp_timeline VARCHAR(100),
    profit_timeline VARCHAR(100),
    scaling_potential INTEGER CHECK (scaling_potential BETWEEN 0 AND 100),
    
    -- Скоринг
    copy_score INTEGER CHECK (copy_score BETWEEN 0 AND 100),
    money_score INTEGER CHECK (money_score BETWEEN 0 AND 100),
    viral_score INTEGER CHECK (viral_score BETWEEN 0 AND 100),
    startup_score INTEGER CHECK (startup_score BETWEEN 0 AND 100),
    russia_opportunity_score INTEGER CHECK (russia_opportunity_score BETWEEN 0 AND 100),
    coolness_score INTEGER CHECK (coolness_score BETWEEN 0 AND 100),
    market_saturation_score INTEGER CHECK (market_saturation_score BETWEEN 0 AND 100),
    rotation_priority INTEGER DEFAULT 50,
    is_rotated BOOLEAN DEFAULT false,
    rotated_at TIMESTAMP,
    
    -- Russia Opportunity
    has_russia_analog BOOLEAN DEFAULT false,
    has_cis_analog BOOLEAN DEFAULT false,
    has_strong_competitor BOOLEAN DEFAULT false,
    has_weak_competitor BOOLEAN DEFAULT false,
    can_localize BOOLEAN DEFAULT false,
    can_quick_launch BOOLEAN DEFAULT false,
    legal_restrictions BOOLEAN DEFAULT false,
    
    -- AI Gap Detector
    gap_status VARCHAR(20) DEFAULT 'unknown', -- 'green', 'yellow', 'red'
    
    -- Founder Detector
    founder_history_score INTEGER DEFAULT 0,
    
    -- Статус
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'graveyard', 'frozen', 'acquired'
    
    -- Уникальность
    is_duplicate BOOLEAN DEFAULT false,
    duplicate_of_id UUID REFERENCES projects(id),
    similarity_score DECIMAL(5,4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица трендов
CREATE TABLE IF NOT EXISTS trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    source VARCHAR(100),
    
    -- Метрики роста
    initial_mentions INTEGER DEFAULT 0,
    current_mentions INTEGER DEFAULT 0,
    growth_percent DECIMAL(10,2),
    
    -- Источники тренда
    google_trends_score INTEGER,
    reddit_mentions INTEGER DEFAULT 0,
    twitter_mentions INTEGER DEFAULT 0,
    youtube_mentions INTEGER DEFAULT 0,
    
    -- Статус
    is_exploding BOOLEAN DEFAULT false,
    explosion_detected_at TIMESTAMP,
    
    -- Связанные проекты
    related_projects_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица связи проектов и трендов
CREATE TABLE IF NOT EXISTS project_trends (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    trend_id UUID REFERENCES trends(id) ON DELETE CASCADE,
    relevance_score DECIMAL(5,4),
    PRIMARY KEY (project_id, trend_id)
);

-- Таблица инвестиций
CREATE TABLE IF NOT EXISTS investments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    amount DECIMAL(15,2),
    currency VARCHAR(10) DEFAULT 'USD',
    stage VARCHAR(50), -- 'seed', 'angel', 'series_a', 'series_b', 'series_c', 'ipo'
    investors TEXT,
    investment_date DATE,
    source_url VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица Watchlist
CREATE TABLE IF NOT EXISTS watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    notes TEXT,
    alerts_enabled BOOLEAN DEFAULT true,
    score_change_threshold INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id)
);

-- Таблица истории скоринга
CREATE TABLE IF NOT EXISTS score_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    startup_score INTEGER,
    russia_opportunity_score INTEGER,
    copy_score INTEGER,
    money_score INTEGER,
    viral_score INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица ежедневных отчетов
CREATE TABLE IF NOT EXISTS daily_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_date DATE NOT NULL UNIQUE,
    top_projects JSONB,
    top_ai_saas JSONB,
    top_mobile_apps JSONB,
    top_telegram_bots JSONB,
    top_chrome_extensions JSONB,
    top_ai_agents JSONB,
    top_mcp_tools JSONB,
    top_github_projects JSONB,
    top_investments JSONB,
    top_trends JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_to_telegram BOOLEAN DEFAULT false
);

-- Таблица Telegram публикаций
CREATE TABLE IF NOT EXISTS telegram_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    message_id BIGINT,
    channel_id VARCHAR(100),
    content TEXT,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    engagement_score INTEGER DEFAULT 0
);

-- Таблица скрапинг-логов
CREATE TABLE IF NOT EXISTS scrape_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id),
    status VARCHAR(50), -- 'success', 'error', 'partial'
    items_found INTEGER DEFAULT 0,
    items_new INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    duration_seconds INTEGER
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_projects_category ON projects(category);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_startup_score ON projects(startup_score DESC);
CREATE INDEX IF NOT EXISTS idx_projects_russia_score ON projects(russia_opportunity_score DESC);
CREATE INDEX IF NOT EXISTS idx_projects_gap_status ON projects(gap_status);
CREATE INDEX IF NOT EXISTS idx_projects_discovered_at ON projects(discovered_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_name_trgm ON projects USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_trends_growth ON trends(growth_percent DESC);
CREATE INDEX IF NOT EXISTS idx_trends_is_exploding ON trends(is_exploding);
CREATE INDEX IF NOT EXISTS idx_investments_stage ON investments(stage);
CREATE INDEX IF NOT EXISTS idx_score_history_project ON score_history(project_id, recorded_at);

-- Вставка базовых источников
INSERT INTO sources (name, url, category, scrape_interval_minutes) VALUES
('Product Hunt', 'https://www.producthunt.com', 'ai_saas', 120),
('GitHub Trending', 'https://github.com/trending', 'open_source', 120),
('Hacker News', 'https://news.ycombinator.com', 'startups', 60),
('Hugging Face', 'https://huggingface.co/models', 'ai_models', 240),
('BetaList', 'https://betalist.com', 'ai_saas', 240),
('Indie Hackers', 'https://www.indiehackers.com', 'startups', 240),
('YC Launches', 'https://www.ycombinator.com/launches', 'startups', 480),
('TechCrunch', 'https://techcrunch.com', 'startups', 120),
('Reddit r/startup', 'https://www.reddit.com/r/startups', 'startups', 120),
('Reddit r/SaaS', 'https://www.reddit.com/r/SaaS', 'ai_saas', 120),
('Chrome Web Store', 'https://chrome.google.com/webstore', 'chrome_extensions', 240),
('Exploding Topics', 'https://explodingtopics.com', 'trends', 480)
ON CONFLICT (name) DO NOTHING;

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trends_updated_at BEFORE UPDATE ON trends
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watchlist_updated_at BEFORE UPDATE ON watchlist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();