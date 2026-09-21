import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from app.core.config import Settings


@pytest.fixture
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_project():
    def _create(overrides: Dict[str, Any] = None):
        p = MagicMock()
        p.id = "123e4567-e89b-12d3-a456-426614174000"
        p.name = "Test Project"
        p.description = "A test project description"
        p.category = "ai_saas"
        p.source_url = "https://example.com"
        p.website = "https://example.com"
        p.github_url = None
        p.github_stars = 1000
        p.github_forks = 0
        p.github_language = "Python"
        p.likes = 500
        p.rating = None
        p.reviews_count = 0
        p.downloads = 0
        p.users_count = 0
        p.author = "Test Author"
        p.author_url = None
        p.implementation_complexity = 50
        p.investment_amount = None
        p.investment_stage = None
        p.investors = None
        p.has_subscription = False
        p.has_freemium = False
        p.money_potential = 50
        p.viral_potential = 50
        p.growth_potential = 50
        p.market_size = "medium"
        p.competition_level = 50
        p.failure_probability = 30
        p.founder_history_score = 50
        p.scaling_potential = 50
        p.copy_score = 50
        p.money_score = 50
        p.viral_score = 50
        p.startup_score = 50
        p.russia_opportunity_score = 50
        p.coolness_score = 50
        p.market_saturation_score = 50
        p.rotation_priority = 50
        p.is_rotated = False
        p.is_duplicate = False
        p.status = "active"
        p.gap_status = "yellow"
        p.has_russia_analog = False
        p.has_cis_analog = False
        p.has_strong_competitor = False
        p.has_weak_competitor = False
        p.can_localize = True
        p.can_quick_launch = True
        p.legal_restrictions = False
        p.solo_founder_possible = True
        p.small_team_possible = True
        p.mvp_timeline = "2-3 months"
        p.profit_timeline = "6-12 months"
        p.discovered_at = None
        p.last_updated_at = None
        p.rotated_at = None
        p.ai_summary = None
        p.problem_solved = None
        p.target_audience = None
        p.monetization_type = None

        if overrides:
            for key, value in overrides.items():
                setattr(p, key, value)
        return p
    return _create


@pytest.fixture
def settings():
    with patch('app.core.config.Settings') as mock:
        mock.OLLAMA_URL = "http://localhost:11434"
        mock.OLLAMA_MODEL = "test-model"
        mock.DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test"
        mock.REDIS_URL = "redis://localhost:6379/0"
        mock.SECRET_KEY = "test-secret-key"
        mock.DEBUG = True
        mock.APP_NAME = "Test App"
        mock.APP_VERSION = "1.0.0"
        mock.REQUEST_TIMEOUT = 30
        yield mock
