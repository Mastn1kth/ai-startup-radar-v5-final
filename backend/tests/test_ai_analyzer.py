import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from app.services.ai_analyzer import OllamaClient


@pytest.fixture
def analyzer():
    with patch('app.services.ai_analyzer.settings') as mock_settings:
        mock_settings.OLLAMA_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "test-model"
        yield OllamaClient()


@pytest.mark.asyncio
async def test_analyze_project_returns_fallback_on_error(analyzer):
    analyzer.generate = AsyncMock(return_value="")
    result = await analyzer.analyze_project("Test", "Description", "ai_saas")
    assert isinstance(result, dict)
    assert result["summary"] == "Description"[:200]
    assert result["problem"] == "Unknown"
    assert result["target_audience"] == "Unknown"
    assert result["growth_potential"] == 50
    assert result["viral_potential"] == 50


@pytest.mark.asyncio
async def test_analyze_project_with_valid_json(analyzer):
    valid_response = json.dumps({
        "summary": "A test project",
        "problem": "Test problem",
        "target_audience": "Developers",
        "monetization_type": "subscription",
        "growth_potential": 80,
        "viral_potential": 60,
        "money_potential": 70,
        "failure_probability": 20,
        "competition_level": 40,
        "market_size": "large",
        "implementation_complexity": 30,
        "solo_founder_possible": True,
        "small_team_possible": True,
        "mvp_timeline": "2-3 months",
        "profit_timeline": "6-12 months",
        "scaling_potential": 90,
    })
    analyzer.generate = AsyncMock(return_value=valid_response)
    result = await analyzer.analyze_project("Test", "A test description", "ai_saas")
    assert result["summary"] == "A test project"
    assert result["problem"] == "Test problem"
    assert result["growth_potential"] == 80
    assert result["viral_potential"] == 60
    assert result["market_size"] == "large"
    assert result["solo_founder_possible"] is True


@pytest.mark.asyncio
async def test_analyze_project_with_json_in_markdown(analyzer):
    md_response = '```json\n{"summary": "Project from markdown", "problem": "Markdown problem", "target_audience": "Users", "monetization_type": "freemium", "growth_potential": 75, "viral_potential": 65, "money_potential": 60, "failure_probability": 25, "competition_level": 50, "market_size": "medium", "implementation_complexity": 40, "solo_founder_possible": false, "small_team_possible": true, "mvp_timeline": "1-2 months", "profit_timeline": "3-6 months", "scaling_potential": 70}\n```'
    analyzer.generate = AsyncMock(return_value=md_response)
    result = await analyzer.analyze_project("Test", "A test description", "ai_saas")
    assert result["summary"] == "Project from markdown"
    assert result["problem"] == "Markdown problem"
    assert result["growth_potential"] == 75


@pytest.mark.asyncio
async def test_analyze_project_fails_gracefully_with_invalid_json(analyzer):
    analyzer.generate = AsyncMock(return_value="This is not JSON at all {{{broken")
    result = await analyzer.analyze_project("Test", "Description", "ai_saas")
    assert isinstance(result, dict)
    assert result["growth_potential"] == 50
    assert result["competition_level"] == 50


@pytest.mark.asyncio
async def test_analyze_project_handles_partial_json(analyzer):
    analyzer.generate = AsyncMock(return_value='{"summary": "Partial"}')
    result = await analyzer.analyze_project("Test", "Description", "ai_saas")
    assert result["summary"] == "Partial"


@pytest.mark.asyncio
async def test_analyze_russia_opportunity_returns_fallback(analyzer):
    analyzer.generate = AsyncMock(return_value="")
    result = await analyzer.analyze_russia_opportunity("Test", "Description", "ai_saas")
    assert isinstance(result, dict)
    assert result["has_russia_analog"] is False
    assert result["russia_opportunity_score"] == 50
    assert result["gap_status"] == "yellow"


@pytest.mark.asyncio
async def test_analyze_russia_opportunity_valid_json(analyzer):
    valid_response = json.dumps({
        "has_russia_analog": False,
        "has_cis_analog": True,
        "has_strong_competitor": False,
        "has_weak_competitor": True,
        "can_localize": True,
        "can_quick_launch": True,
        "legal_restrictions": False,
        "russia_opportunity_score": 85,
        "gap_status": "green",
    })
    analyzer.generate = AsyncMock(return_value=valid_response)
    result = await analyzer.analyze_russia_opportunity("Test", "Description", "ai_saas")
    assert result["has_russia_analog"] is False
    assert result["has_cis_analog"] is True
    assert result["russia_opportunity_score"] == 85
    assert result["gap_status"] == "green"


@pytest.mark.asyncio
async def test_generate_method_handles_ollama_error(analyzer):
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.post.side_effect = Exception("Connection refused")
        mock_client.return_value = mock_instance
        result = await analyzer.generate("test prompt")
        assert result == ""
