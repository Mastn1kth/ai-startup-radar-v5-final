from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Uuid, select
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # User preferences
    telegram_notifications = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    min_startup_score_alert = Column(Integer, default=70)
    min_russia_score_alert = Column(Integer, default=60)
    
    # Relationships
    watchlist_items = relationship("Watchlist", back_populates="user")


class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    url = Column(String(500))
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    scrape_interval_minutes = Column(Integer, default=120)
    last_scraped_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    projects = relationship("Project", back_populates="source")
    scrape_logs = relationship("ScrapeLog", back_populates="source")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True)
    description = Column(Text)
    category = Column(String(100))
    subcategory = Column(String(100))
    source_id = Column(Uuid(as_uuid=True), ForeignKey("sources.id"))
    source_url = Column(String(1000))
    website = Column(String(500))
    author = Column(String(255))
    author_url = Column(String(500))
    
    # Metrics
    rating = Column(DECIMAL(3, 2))
    likes = Column(Integer, default=0)
    reviews_count = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    users_count = Column(Integer, default=0)
    
    # GitHub metrics
    github_url = Column(String(500))
    github_stars = Column(Integer, default=0)
    github_forks = Column(Integer, default=0)
    github_language = Column(String(100))
    
    # Investments
    investment_amount = Column(DECIMAL(15, 2))
    investment_stage = Column(String(50))
    investors = Column(Text)
    
    # Dates
    discovered_at = Column(DateTime, default=func.now())
    published_at = Column(DateTime)
    last_updated_at = Column(DateTime, default=func.now())
    
    # AI Analytics
    ai_summary = Column(Text)
    problem_solved = Column(Text)
    target_audience = Column(Text)
    monetization_type = Column(String(100))
    has_subscription = Column(Boolean, default=False)
    has_freemium = Column(Boolean, default=False)
    growth_potential = Column(Integer)
    viral_potential = Column(Integer)
    money_potential = Column(Integer)
    failure_probability = Column(Integer)
    competition_level = Column(Integer)
    market_size = Column(String(255))
    implementation_complexity = Column(Integer)
    required_team = Column(String(255))
    required_investment = Column(String(255))
    solo_founder_possible = Column(Boolean, default=False)
    small_team_possible = Column(Boolean, default=False)
    mvp_timeline = Column(String(100))
    profit_timeline = Column(String(100))
    scaling_potential = Column(Integer)
    
    # Scoring
    copy_score = Column(Integer)
    money_score = Column(Integer)
    viral_score = Column(Integer)
    startup_score = Column(Integer)
    russia_opportunity_score = Column(Integer)
    coolness_score = Column(Integer)
    market_saturation_score = Column(Integer)
    rotation_priority = Column(Integer, default=50)
    is_rotated = Column(Boolean, default=False)
    rotated_at = Column(DateTime)
    
    # Russia Opportunity
    has_russia_analog = Column(Boolean, default=False)
    has_cis_analog = Column(Boolean, default=False)
    has_strong_competitor = Column(Boolean, default=False)
    has_weak_competitor = Column(Boolean, default=False)
    can_localize = Column(Boolean, default=False)
    can_quick_launch = Column(Boolean, default=False)
    legal_restrictions = Column(Boolean, default=False)
    
    # AI Gap Detector
    gap_status = Column(String(20), default='unknown')
    
    # Founder Detector
    founder_history_score = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), default='active')
    
    # Embeddings & deduplication
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"))
    similarity_score = Column(DECIMAL(5, 4))
    
    # Qdrant vector ID
    qdrant_vector_id = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    source = relationship("Source", back_populates="projects")
    investments = relationship("Investment", back_populates="project")
    score_history = relationship("ScoreHistory", back_populates="project")
    telegram_posts = relationship("TelegramPost", back_populates="project")
    watchlist = relationship("Watchlist", back_populates="project", uselist=False)
    trends = relationship("Trend", secondary="project_trends", back_populates="projects")
    rotation_logs = relationship("RotationLog", back_populates="project", foreign_keys="RotationLog.project_id")


class RotationLog(Base):
    """Log of auto-rotated projects"""
    __tablename__ = "rotation_logs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    rotation_reason = Column(String(255))  # 'limit_reached', 'low_score', 'duplicate', 'old_project'
    rotation_priority = Column(Integer, default=50)
    coolness_score_before = Column(Integer)
    startup_score_before = Column(Integer)
    replaced_by_project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"))
    rotated_at = Column(DateTime, default=func.now())
    
    project = relationship("Project", back_populates="rotation_logs", foreign_keys=[project_id])


class Trend(Base):
    __tablename__ = "trends"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    source = Column(String(100))
    
    # Growth metrics
    initial_mentions = Column(Integer, default=0)
    current_mentions = Column(Integer, default=0)
    growth_percent = Column(DECIMAL(10, 2))
    
    # Source metrics
    google_trends_score = Column(Integer)
    reddit_mentions = Column(Integer, default=0)
    twitter_mentions = Column(Integer, default=0)
    youtube_mentions = Column(Integer, default=0)
    
    # Status
    is_exploding = Column(Boolean, default=False)
    explosion_detected_at = Column(DateTime)
    
    related_projects_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    projects = relationship("Project", secondary="project_trends", back_populates="trends")


class ProjectTrend(Base):
    __tablename__ = "project_trends"
    
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    trend_id = Column(Uuid(as_uuid=True), ForeignKey("trends.id", ondelete="CASCADE"), primary_key=True)
    relevance_score = Column(DECIMAL(5, 4))


class Investment(Base):
    __tablename__ = "investments"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    amount = Column(DECIMAL(15, 2))
    currency = Column(String(10), default='USD')
    stage = Column(String(50))
    investors = Column(Text)
    investment_date = Column(DateTime)
    source_url = Column(String(1000))
    created_at = Column(DateTime, default=func.now())
    
    project = relationship("Project", back_populates="investments")


class Watchlist(Base):
    __tablename__ = "watchlist"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    notes = Column(Text)
    alerts_enabled = Column(Boolean, default=True)
    score_change_threshold = Column(Integer, default=5)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    project = relationship("Project", back_populates="watchlist")
    user = relationship("User", back_populates="watchlist_items")


class ScoreHistory(Base):
    __tablename__ = "score_history"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    startup_score = Column(Integer)
    russia_opportunity_score = Column(Integer)
    copy_score = Column(Integer)
    money_score = Column(Integer)
    viral_score = Column(Integer)
    recorded_at = Column(DateTime, default=func.now())
    
    project = relationship("Project", back_populates="score_history")


class DailyReport(Base):
    __tablename__ = "daily_reports"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_date = Column(DateTime, unique=True)
    top_projects = Column(JSON)
    top_ai_saas = Column(JSON)
    top_mobile_apps = Column(JSON)
    top_telegram_bots = Column(JSON)
    top_chrome_extensions = Column(JSON)
    top_ai_agents = Column(JSON)
    top_mcp_tools = Column(JSON)
    top_github_projects = Column(JSON)
    top_investments = Column(JSON)
    top_trends = Column(JSON)
    generated_at = Column(DateTime, default=func.now())
    sent_to_telegram = Column(Boolean, default=False)
    sent_to_email = Column(Boolean, default=False)


class TelegramPost(Base):
    __tablename__ = "telegram_posts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    message_id = Column(Integer)
    channel_id = Column(String(100))
    content = Column(Text)
    posted_at = Column(DateTime, default=func.now())
    engagement_score = Column(Integer, default=0)
    
    project = relationship("Project", back_populates="telegram_posts")


class EmailAlert(Base):
    """Email alerts sent to users"""
    __tablename__ = "email_alerts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    alert_type = Column(String(50))  # 'new_project', 'score_change', 'trend_explosion'
    subject = Column(String(500))
    content = Column(Text)
    sent_at = Column(DateTime, default=func.now())
    opened_at = Column(DateTime)


class ScrapeLog(Base):
    __tablename__ = "scrape_logs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(Uuid(as_uuid=True), ForeignKey("sources.id"))
    status = Column(String(50))
    items_found = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    source = relationship("Source", back_populates="scrape_logs")


class BotSettings(Base):
    """Настройки Telegram бота для разных каналов/пользователей"""
    __tablename__ = "bot_settings"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Идентификация
    channel_id = Column(String(100), nullable=False, unique=True)
    channel_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Настройки дайджеста
    digest_interval_minutes = Column(Integer, default=30)  # Как часто отправлять (30 мин по умолчанию)
    projects_per_digest = Column(Integer, default=10)  # Сколько проектов в одном сообщении
    max_projects_per_day = Column(Integer, default=100)  # Лимит проектов в день
    
    # Фильтры
    min_coolness_score = Column(Integer, default=50)  # Минимальный Coolness Score для отправки
    min_startup_score = Column(Integer, default=60)  # Минимальный Startup Score
    min_russia_score = Column(Integer, default=0)  # Минимальный Russia Score (0 = не фильтровать)
    
    # Категории (JSON список разрешенных категорий, пустой = все)
    allowed_categories = Column(JSON, default=list)
    excluded_categories = Column(JSON, default=list)
    
    # Что отправлять
    send_digest = Column(Boolean, default=True)  # Отправлять дайджест
    send_detailed_review = Column(Boolean, default=True)  # Отправлять детальный обзор топ-1
    send_individual_alerts = Column(Boolean, default=False)  # Отправлять индивидуальные уведомления
    send_rotation_updates = Column(Boolean, default=False)  # Отправлять обновления ротации
    
    # Время отправки (если пусто - круглосуточно)
    active_hours_start = Column(Integer, default=0)  # Начало активных часов (0-23)
    active_hours_end = Column(Integer, default=23)  # Конец активных часов (0-23)
    timezone = Column(String(50), default='Europe/Moscow')
    
    # Форматирование
    include_ai_summary = Column(Boolean, default=True)  # Включать AI summary
    include_revenue_prediction = Column(Boolean, default=True)  # Включать прогноз выручки
    include_russia_launch = Column(Boolean, default=True)  # Включать Russia Launch Generator
    include_opportunity_ideas = Column(Boolean, default=True)  # Включать Opportunity Engine
    
    # Лимиты и защита от спама
    cooldown_minutes = Column(Integer, default=5)  # Минимальное время между сообщениями
    last_sent_at = Column(DateTime)
    messages_sent_today = Column(Integer, default=0)
    reset_counter_at = Column(DateTime, default=func.now())
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AppSetting(Base):
    """Системные настройки приложения (ключ-значение)"""
    __tablename__ = "app_settings"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False, default="")
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())


async def get_app_setting(db, key: str, default: str = "") -> str:
    """Получить значение настройки по ключу"""
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def set_app_setting(db, key: str, value: str, description: str = "") -> AppSetting:
    """Установить значение настройки"""
    result = await db.execute(
        select(AppSetting).where(AppSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        setting = AppSetting(key=key, value=value, description=description)
        db.add(setting)
    await db.commit()
    return setting


# Singleton
def get_default_bot_settings():
    """Получение настроек по умолчанию"""
    return {
        'digest_interval_minutes': 30,
        'projects_per_digest': 10,
        'max_projects_per_day': 100,
        'min_coolness_score': 50,
        'min_startup_score': 60,
        'min_russia_score': 0,
        'allowed_categories': [],
        'excluded_categories': [],
        'send_digest': True,
        'send_detailed_review': True,
        'send_individual_alerts': False,
        'send_rotation_updates': False,
        'active_hours_start': 0,
        'active_hours_end': 23,
        'timezone': 'Europe/Moscow',
        'include_ai_summary': True,
        'include_revenue_prediction': True,
        'include_russia_launch': True,
        'include_opportunity_ideas': True,
        'cooldown_minutes': 5,
    }
