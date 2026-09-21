import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Создание приложения Celery
celery_app = Celery(
    "ai_startup_radar",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.scraping",
        "app.tasks.reports",
    ],
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_hijack_root_logger=False,
    worker_log_color=not settings.DEBUG,
    # Расписание периодических задач
    # ВНИМАНИЕ: Скрапперы добавлять ТОЛЬКО если реализованы в ScraperFactory
    # Актуальный список: Product Hunt, GitHub Trending, Hacker News, Hugging Face,
    # TikTok, YouTube Shorts, X (Twitter), LinkedIn, TechCrunch, Reddit,
    # AppSumo, BetaList, IndieHackers, Chrome Web Store, Google Play,
    # VentureBeat, YC Launches
    beat_schedule={
        # === СКРАПИНГ ===
        "scrape-product-hunt": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 7200.0,
            "args": ("Product Hunt",),
        },
        "scrape-github": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 7200.0,
            "args": ("GitHub Trending",),
        },
        "scrape-hacker-news": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 3600.0,
            "args": ("Hacker News",),
        },
        "scrape-hugging-face": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("Hugging Face",),
        },
        "scrape-tiktok": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("TikTok",),
        },
        "scrape-youtube-shorts": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("YouTube Shorts",),
        },
        "scrape-x": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("X (Twitter)",),
        },
        "scrape-linkedin": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("LinkedIn",),
        },
        "scrape-techcrunch": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 7200.0,
            "args": ("TechCrunch",),
        },
        "scrape-reddit": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 7200.0,
            "args": ("Reddit",),
        },
        "scrape-appsumo": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("AppSumo",),
        },
        "scrape-betalist": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("BetaList",),
        },
        "scrape-indiehackers": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("IndieHackers",),
        },
        "scrape-chrome-web-store": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("Chrome Web Store",),
        },
        "scrape-google-play": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("Google Play",),
        },
        "scrape-venturebeat": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("VentureBeat",),
        },
        "scrape-yc-launches": {
            "task": "app.tasks.scraping.scrape_source",
            "schedule": 14400.0,
            "args": ("YC Launches",),
        },
        
        # === AI АНАЛИТИКА ===
        # Каждые 30 минут - анализ новых проектов
        "analyze-new-projects": {
            "task": "app.tasks.scraping.analyze_unprocessed_projects",
            "schedule": 1800.0,
        },
        # Каждые 30 минут - скоринг и анализ
        "score-projects": {
            "task": "app.tasks.scraping.score_unscored_projects",
            "schedule": 1800.0,
        },
        # Каждые 6 часов - генерация планов запуска
        "generate-opportunity-plans": {
            "task": "app.tasks.scraping.generate_opportunity_plans",
            "schedule": 21600.0,
        },
        # Каждые 12 часов - генерация ТЗ для клонирования
        "generate-clone-specs": {
            "task": "app.tasks.scraping.generate_clone_specs",
            "schedule": 43200.0,
        },
        # Каждые 12 часов - анализ барьеров для России
        "analyze-russia-barriers": {
            "task": "app.tasks.scraping.analyze_russia_barriers",
            "schedule": 43200.0,
        },
        # Каждые 24 часа - генерация бизнес-планов
        "generate-business-plans": {
            "task": "app.tasks.scraping.generate_business_plans",
            "schedule": 86400.0,
        },
        
        # === ДЕТЕКТОРЫ ===
        # Каждый час - детекторы
        "detect-trend-explosions": {
            "task": "app.tasks.scraping.detect_trend_explosions",
            "schedule": 3600.0,
        },
        "detect-github-explosions": {
            "task": "app.tasks.scraping.detect_github_explosions",
            "schedule": 3600.0,
        },
        
        # === ОТЧЕТЫ ===
        # Каждые 24 часа - отчеты
        "generate-daily-report": {
            "task": "app.tasks.reports.generate_daily_report",
            "schedule": 86400.0,
        },
        "send-telegram-digest": {
            "task": "app.tasks.reports.send_daily_digest",
            "schedule": 86400.0,
        },
        # Каждые 12 часов - генерация бизнес-идей из трендов
        "generate-business-ideas": {
            "task": "app.tasks.reports.generate_business_ideas_from_trends",
            "schedule": 43200.0,
        },
        # Каждые 6 часов - Trend-to-Product
        "generate-trend-products": {
            "task": "app.tasks.reports.generate_trend_products",
            "schedule": 21600.0,
        },
        # Каждые 30 минут - Coolness Digest в Telegram (топ крутых проектов)
        "send-coolness-digest": {
            "task": "app.tasks.reports.send_coolness_digest",
            "schedule": 1800.0,
        },
        # Каждые 30 минут - автоматическая ротация проектов при достижении лимита
        "auto-rotate-projects": {
            "task": "app.tasks.scraping.auto_rotate_old_projects",
            "schedule": 1800.0,
        },
        # Каждые 24 часа - экспорт данных
        "export-to-csv": {
            "task": "app.tasks.reports.export_projects_to_csv",
            "schedule": 86400.0,
        },
    },
)