import logging
import time
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, init_db, AsyncSessionLocal
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.sentry_config import init_sentry
from app.models import User, get_app_setting, set_app_setting
from app.core.auth import get_password_hash
from app.services.telegram_bot import telegram_bot

logger = logging.getLogger(__name__)

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.trends import router as trends_router
from app.api.dashboard import router as dashboard_router
from app.api.watchlist import router as watchlist_router
from app.api.search import router as search_router
from app.api.reports import router as reports_router
from app.api.export import router as export_router

init_sentry(
    dsn=settings.SENTRY_DSN,
    environment="production" if not settings.DEBUG else "development",
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Startup Radar - система обнаружения перспективных стартапов и AI-продуктов"
)

allowed_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(trends_router)
app.include_router(dashboard_router)
app.include_router(watchlist_router)
app.include_router(search_router)
app.include_router(reports_router)
app.include_router(export_router)

# Rate limiting middleware
rate_limit_store = defaultdict(list)
RATE_LIMIT = 100  # requests
RATE_WINDOW = 60  # seconds


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - RATE_WINDOW
    rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if t > window_start]
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    rate_limit_store[client_ip].append(now)
    response = await call_next(request)
    return response


@app.on_event("startup")
async def startup():
    setup_logging()
    logger.info("Starting AI Startup Radar v%s", settings.APP_VERSION)
    await init_db()
    async with AsyncSessionLocal() as session:
        existing = await get_app_setting(session, "ai_analysis_enabled")
        if not existing:
            await set_app_setting(session, "ai_analysis_enabled", "true", "Enable AI analysis")
            await set_app_setting(session, "scoring_interval_minutes", "30", "Scoring interval")
            await set_app_setting(session, "max_projects_per_source", "100", "Max projects per source")
        admin = await session.execute(select(User).where(User.email == settings.DEFAULT_ADMIN_EMAIL))
        if not admin.scalar_one_or_none():
            admin_user = User(
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                full_name="Admin", is_superuser=True, is_active=True
            )
            session.add(admin_user)
            await session.commit()
    telegram_bot.start_polling()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
