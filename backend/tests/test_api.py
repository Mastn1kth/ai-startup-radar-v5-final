import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models import Project


@pytest.fixture
def override_get_db(mock_db):
    async def _override():
        yield mock_db
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


class TestProjectsAPI:

    def test_get_projects_returns_correct_structure(self, client, override_get_db, mock_db, mock_project):
        project = mock_project()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Project"
        assert data["items"][0]["category"] == "ai_saas"

    def test_get_project_invalid_uuid_returns_400(self, client):
        response = client.get("/api/projects/invalid-uuid")
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    def test_get_project_not_found_returns_404(self, client, override_get_db, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.get("/api/projects/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"

    def test_get_projects_with_filters(self, client, override_get_db, mock_db, mock_project):
        project = mock_project({'category': 'ai_saas', 'startup_score': 80})
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/projects?category=ai_saas&min_score=70")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1


class TestSearchAPI:

    def test_search_empty_query_returns_422(self, client):
        response = client.get("/api/search")
        assert response.status_code == 422

    def test_search_short_query_returns_422(self, client):
        response = client.get("/api/search?q=a")
        assert response.status_code == 422

    def test_search_valid_returns_results(self, client, override_get_db, mock_db, mock_project):
        project = mock_project({'name': 'AI Test Project'})
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [project]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/search?q=AI")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total" in data
        assert data["query"] == "AI"


class TestDashboardAPI:

    def test_get_stats_returns_all_fields(self, client, override_get_db, mock_db):
        mock_count = MagicMock()
        mock_count.scalar.return_value = 42
        mock_db.execute.return_value = mock_count

        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        assert "categories" in data
        assert "high_potential" in data
        assert "russia_opportunities" in data
        assert "new_24h" in data
        assert "exploding_trends" in data
        assert "top_coolness" in data
        assert "rotated_projects" in data
        assert "last_updated" in data
        assert data["total_projects"] == 42

    def test_get_top_categories(self, client, override_get_db, mock_db):
        mock_result = MagicMock()
        mock_result.all.return_value = [("ai_saas", 15), ("startups", 10)]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/dashboard/top-categories")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) == 2
        assert data["categories"][0]["name"] == "ai_saas"
        assert data["categories"][0]["count"] == 15

    def test_get_score_distribution(self, client, override_get_db, mock_db):
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        mock_db.execute.return_value = mock_count

        response = client.get("/api/dashboard/score-distribution")
        assert response.status_code == 200
        data = response.json()
        assert "distribution" in data
        assert len(data["distribution"]) == 5
        assert data["metric"] == "coolness_score"
        assert all("range" in d and "count" in d for d in data["distribution"])


class TestTrendsAPI:

    def test_get_trends_returns_list(self, client, override_get_db, mock_db, mock_project):
        mock_trend = MagicMock()
        mock_trend.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_trend.name = "AI Agents"
        mock_trend.category = "ai_saas"
        mock_trend.description = "Growing trend"
        mock_trend.source = "Product Hunt"
        mock_trend.initial_mentions = 10
        mock_trend.current_mentions = 100
        mock_trend.growth_percent = 900.00
        mock_trend.google_trends_score = 80
        mock_trend.reddit_mentions = 50
        mock_trend.twitter_mentions = 200
        mock_trend.youtube_mentions = 30
        mock_trend.is_exploding = True
        mock_trend.explosion_detected_at = None
        mock_trend.related_projects_count = 5
        mock_trend.created_at = None
        mock_trend.updated_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_trend]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/trends")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "AI Agents"
        assert data["items"][0]["is_exploding"] is True

    def test_get_trends_filters_exploding(self, client, override_get_db, mock_db, mock_project):
        mock_trend = MagicMock()
        mock_trend.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_trend.name = "Exploding Trend"
        mock_trend.category = "ai_saas"
        mock_trend.description = "Hot trend"
        mock_trend.source = "Reddit"
        mock_trend.initial_mentions = 5
        mock_trend.current_mentions = 500
        mock_trend.growth_percent = 9900.00
        mock_trend.google_trends_score = 95
        mock_trend.reddit_mentions = 300
        mock_trend.twitter_mentions = 1000
        mock_trend.youtube_mentions = 50
        mock_trend.is_exploding = True
        mock_trend.explosion_detected_at = None
        mock_trend.related_projects_count = 8
        mock_trend.created_at = None
        mock_trend.updated_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_trend]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/trends?is_exploding=true")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    def test_get_exploding_trends_endpoint(self, client, override_get_db, mock_db, mock_project):
        mock_trend = MagicMock()
        mock_trend.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_trend.name = "Hot Trend"
        mock_trend.category = "ai_models"
        mock_trend.description = "Very hot trend"
        mock_trend.source = "Twitter"
        mock_trend.initial_mentions = 1
        mock_trend.current_mentions = 1000
        mock_trend.growth_percent = 99900.00
        mock_trend.google_trends_score = 99
        mock_trend.reddit_mentions = 500
        mock_trend.twitter_mentions = 5000
        mock_trend.youtube_mentions = 100
        mock_trend.is_exploding = True
        mock_trend.explosion_detected_at = None
        mock_trend.related_projects_count = 10
        mock_trend.created_at = None
        mock_trend.updated_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_trend]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/trends/exploding")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1
        assert response.json()["items"][0]["is_exploding"] is True


class TestWatchlistAPI:

    def test_add_to_watchlist(self, client, override_get_db, mock_db, mock_project):
        project = mock_project()
        mock_result_project = MagicMock()
        mock_result_project.scalar_one_or_none.return_value = project
        mock_result_watchlist = MagicMock()
        mock_result_watchlist.scalar_one_or_none.return_value = None

        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_result_project
            return mock_result_watchlist

        mock_db.execute.side_effect = side_effect
        response = client.post("/api/watchlist/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 200
        assert response.json()["status"] == "added"

    def test_add_to_watchlist_not_found_returns_404(self, client, override_get_db, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.post("/api/watchlist/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404

    def test_remove_from_watchlist(self, client, override_get_db, mock_db, mock_project):
        existing_item = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_item
        mock_db.execute.return_value = mock_result

        response = client.delete("/api/watchlist/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 200
        assert response.json()["status"] == "removed"

    def test_remove_from_watchlist_not_found(self, client, override_get_db, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.delete("/api/watchlist/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 404
        assert response.json()["detail"] == "Not in watchlist"

    def test_get_watchlist(self, client, override_get_db, mock_db, mock_project):
        project = mock_project()
        item = MagicMock()
        item.id = "11111111-1111-1111-1111-111111111111"
        item.project = project
        item.notes = "Interesting project"
        item.created_at = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [item]
        mock_db.execute.return_value = mock_result

        response = client.get("/api/watchlist")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["project"]["name"] == "Test Project"
        assert data["items"][0]["notes"] == "Interesting project"


class TestAuthAPI:

    def test_login_invalid_credentials_returns_401(self, client, override_get_db, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        response = client.post("/api/auth/login", data={
            "username": "test@test.com",
            "password": "wrong"
        })
        assert response.status_code == 401

    def test_register_returns_422_if_missing_fields(self, client):
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422

    def test_register_with_no_db_override_requires_db(self, client, override_get_db, mock_db):
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        response = client.post("/api/auth/register", json={
            "email": "newuser@test.com",
            "password": "test12345"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestAPIEdgeCases:

    def test_invalid_uuid_format_returns_400(self, client):
        response = client.get("/api/projects/not-a-uuid-at-all")
        assert response.status_code == 400

    def test_negative_limit_returns_422(self, client):
        response = client.get("/api/projects?limit=-1")
        assert response.status_code == 422

    def test_large_offset_returns_empty(self, client, override_get_db, mock_db):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        response = client.get("/api/projects?offset=999999")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 0

    def test_cors_headers_present(self, client):
        response = client.options("/api/projects", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
