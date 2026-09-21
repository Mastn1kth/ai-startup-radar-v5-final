import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.scoring import ScoringService
from app.services.ai_analyzer import OllamaClient


class TestScoringPipeline:

    def test_raw_project_data_to_scores(self, mock_project):
        raw_data = {
            'implementation_complexity': 30,
            'category': 'ai_saas',
            'github_stars': 1500,
            'likes': 500,
            'has_subscription': True,
            'has_freemium': False,
            'market_size': 'large',
            'viral_potential': 70,
            'growth_potential': 65,
            'investment_amount': 5000000,
            'has_russia_analog': False,
            'has_cis_analog': False,
            'has_strong_competitor': False,
            'has_weak_competitor': False,
            'can_localize': True,
            'can_quick_launch': True,
            'legal_restrictions': False,
            'founder_history_score': 60,
            'scaling_potential': 75,
        }
        project = mock_project(raw_data)
        scores = ScoringService.calculate_all_scores(project)

        assert all(0 <= v <= 100 for v in scores.values())
        assert all(key in scores for key in [
            'copy_score', 'money_score', 'viral_score', 'startup_score',
            'russia_opportunity_score', 'coolness_score'
        ])

        gap_status = ScoringService.determine_gap_status(project)
        assert gap_status == 'green'

        budget = ScoringService.estimate_budget(project)
        assert budget in ["$1K - $5K", "$5K - $20K"]

    def test_low_potential_project_scores(self, mock_project):
        raw_data = {
            'implementation_complexity': 95,
            'category': 'ai_models',
            'github_stars': 0,
            'likes': 0,
            'has_subscription': False,
            'has_freemium': False,
            'market_size': 'small',
            'viral_potential': 10,
            'growth_potential': 5,
            'investment_amount': None,
            'has_russia_analog': True,
            'has_cis_analog': True,
            'has_strong_competitor': True,
            'has_weak_competitor': False,
            'can_localize': False,
            'can_quick_launch': False,
            'legal_restrictions': True,
            'founder_history_score': 10,
            'scaling_potential': 5,
        }
        project = mock_project(raw_data)
        scores = ScoringService.calculate_all_scores(project)

        assert all(0 <= v <= 100 for v in scores.values())

        gap_status = ScoringService.determine_gap_status(project)
        assert gap_status == 'red'

        budget = ScoringService.estimate_budget(project)
        assert budget == "$100K+"

    def test_high_potential_project_scores(self, mock_project):
        raw_data = {
            'implementation_complexity': 20,
            'category': 'mobile_apps',
            'github_stars': 10000,
            'likes': 8000,
            'has_subscription': True,
            'has_freemium': True,
            'market_size': 'large',
            'viral_potential': 95,
            'growth_potential': 90,
            'investment_amount': 20000000,
            'has_russia_analog': False,
            'has_cis_analog': False,
            'has_strong_competitor': False,
            'has_weak_competitor': True,
            'can_localize': True,
            'can_quick_launch': True,
            'legal_restrictions': False,
            'founder_history_score': 85,
            'scaling_potential': 95,
        }
        project = mock_project(raw_data)
        scores = ScoringService.calculate_all_scores(project)

        assert scores['money_score'] > 50
        assert scores['viral_score'] > 50
        assert scores['startup_score'] > 50
        assert scores['coolness_score'] > 50

        gap_status = ScoringService.determine_gap_status(project)
        assert gap_status == 'green'

    def test_pipeline_full_flow(self, mock_project):
        project = mock_project({
            'implementation_complexity': 40,
            'category': 'ai_saas',
            'github_stars': 2500,
            'likes': 1000,
            'has_subscription': False,
            'has_freemium': True,
            'market_size': 'medium',
            'viral_potential': 60,
            'growth_potential': 55,
            'investment_amount': 1000000,
            'investment_stage': 'Seed',
            'has_russia_analog': False,
            'has_cis_analog': True,
            'has_strong_competitor': False,
            'has_weak_competitor': True,
            'can_localize': True,
            'can_quick_launch': True,
            'legal_restrictions': False,
            'founder_history_score': 50,
            'scaling_potential': 60,
        })

        scores = ScoringService.calculate_all_scores(project)
        gap_status = ScoringService.determine_gap_status(project)
        budget = ScoringService.estimate_budget(project)

        assert scores['copy_score'] >= 0
        assert scores['money_score'] >= 0
        assert scores['viral_score'] >= 0
        assert scores['startup_score'] >= 0
        assert gap_status in ('green', 'yellow', 'red')
        assert budget is not None and '$' in budget

    def test_scores_are_consistent(self, mock_project):
        project_a = mock_project({
            'implementation_complexity': 20,
            'github_stars': 10000,
            'likes': 5000,
            'viral_potential': 90,
            'growth_potential': 85,
            'market_size': 'large',
        })

        project_b = mock_project({
            'implementation_complexity': 80,
            'github_stars': 10,
            'likes': 0,
            'viral_potential': 10,
            'growth_potential': 5,
            'market_size': 'small',
        })

        scores_a = ScoringService.calculate_all_scores(project_a)
        scores_b = ScoringService.calculate_all_scores(project_b)

        assert scores_a['coolness_score'] >= scores_b['coolness_score']
        assert scores_a['startup_score'] >= scores_b['startup_score']
        assert scores_a['viral_score'] >= scores_b['viral_score']
        assert scores_a['money_score'] >= scores_b['money_score']

    def test_gap_status_precedence(self, mock_project):
        project = mock_project({'has_strong_competitor': True})
        assert ScoringService.determine_gap_status(project) == 'red'

        project = mock_project({
            'has_strong_competitor': False,
            'has_weak_competitor': True,
            'has_russia_analog': False,
            'has_cis_analog': False,
        })
        assert ScoringService.determine_gap_status(project) == 'green'

        project = mock_project({
            'has_strong_competitor': False,
            'has_weak_competitor': False,
            'has_russia_analog': False,
            'has_cis_analog': False,
        })
        assert ScoringService.determine_gap_status(project) == 'green'

        project = mock_project({
            'has_strong_competitor': False,
            'has_weak_competitor': True,
            'has_russia_analog': True,
        })
        assert ScoringService.determine_gap_status(project) == 'yellow'

    def test_budget_estimation_ranges(self, mock_project):
        scenarios = [
            (10, "$1K - $5K"),
            (30, "$5K - $20K"),
            (55, "$20K - $50K"),
            (75, "$50K - $100K"),
            (95, "$100K+"),
        ]
        for complexity, expected_range in scenarios:
            project = mock_project({'implementation_complexity': complexity})
            budget = ScoringService.estimate_budget(project)
            assert budget == expected_range, (
                f"Complexity {complexity}: expected {expected_range}, got {budget}"
            )


class TestAIAnalyzerPipeline:

    @pytest.mark.asyncio
    async def test_analyze_returns_all_required_fields(self):
        analyzer = OllamaClient()
        analyzer.generate = AsyncMock(return_value='{"summary": "Test", "problem": "Test problem", "target_audience": "Devs", "monetization_type": "subscription", "growth_potential": 70, "viral_potential": 60, "money_potential": 50, "failure_probability": 30, "competition_level": 40, "market_size": "medium", "implementation_complexity": 35, "solo_founder_possible": true, "small_team_possible": true, "mvp_timeline": "2-3 months", "profit_timeline": "6-12 months", "scaling_potential": 80}')

        result = await analyzer.analyze_project("TestApp", "Description", "ai_saas")
        required = ['summary', 'problem', 'target_audience', 'monetization_type',
                    'growth_potential', 'viral_potential', 'money_potential',
                    'failure_probability', 'competition_level', 'market_size',
                    'implementation_complexity', 'solo_founder_possible',
                    'small_team_possible', 'mvp_timeline', 'profit_timeline',
                    'scaling_potential']
        for field in required:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_russia_opportunity_analyze_returns_fields(self):
        analyzer = OllamaClient()
        analyzer.generate = AsyncMock(return_value='{"has_russia_analog": false, "has_cis_analog": true, "has_strong_competitor": false, "has_weak_competitor": true, "can_localize": true, "can_quick_launch": true, "legal_restrictions": false, "russia_opportunity_score": 75, "gap_status": "yellow"}')

        result = await analyzer.analyze_russia_opportunity("TestApp", "Description", "ai_saas")
        expected = ['has_russia_analog', 'has_cis_analog', 'has_strong_competitor',
                    'has_weak_competitor', 'can_localize', 'can_quick_launch',
                    'legal_restrictions', 'russia_opportunity_score', 'gap_status']
        for field in expected:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_pipeline_analyze_then_score(self, mock_project):
        analyzer = OllamaClient()
        analyzer.generate = AsyncMock(return_value='{"summary": "Pipeline test", "problem": "Testing", "target_audience": "Developers", "monetization_type": "freemium", "growth_potential": 75, "viral_potential": 65, "money_potential": 55, "failure_probability": 25, "competition_level": 45, "market_size": "large", "implementation_complexity": 35, "solo_founder_possible": true, "small_team_possible": true, "mvp_timeline": "1-3 months", "profit_timeline": "6-9 months", "scaling_potential": 85}')

        ai_result = await analyzer.analyze_project("PipelineApp", "Pipeline description", "ai_saas")
        assert ai_result['implementation_complexity'] == 35
        assert ai_result['market_size'] == 'large'

        project = mock_project({
            'implementation_complexity': ai_result['implementation_complexity'],
            'market_size': ai_result['market_size'],
            'growth_potential': ai_result['growth_potential'],
            'viral_potential': ai_result['viral_potential'],
            'money_potential': ai_result['money_potential'],
            'scaling_potential': ai_result['scaling_potential'],
            'failure_probability': ai_result['failure_probability'],
            'competition_level': ai_result['competition_level'],
        })

        scores = ScoringService.calculate_all_scores(project)
        assert all(0 <= v <= 100 for v in scores.values())

        assert scores['coolness_score'] > 0
        assert scores['startup_score'] > 0

    @pytest.mark.asyncio
    async def test_russia_analyze_then_gap_status(self, mock_project):
        analyzer = OllamaClient()
        analyzer.generate = AsyncMock(return_value='{"has_russia_analog": false, "has_cis_analog": false, "has_strong_competitor": false, "has_weak_competitor": false, "can_localize": true, "can_quick_launch": true, "legal_restrictions": false, "russia_opportunity_score": 85, "gap_status": "green"}')

        russia_result = await analyzer.analyze_russia_opportunity("Test", "Desc", "ai_saas")
        assert russia_result['gap_status'] == 'green'
        assert russia_result['russia_opportunity_score'] == 85

        project = mock_project({
            'has_russia_analog': russia_result['has_russia_analog'],
            'has_cis_analog': russia_result['has_cis_analog'],
            'has_strong_competitor': russia_result['has_strong_competitor'],
            'has_weak_competitor': russia_result['has_weak_competitor'],
            'can_localize': russia_result['can_localize'],
            'can_quick_launch': russia_result['can_quick_launch'],
            'legal_restrictions': russia_result['legal_restrictions'],
        })

        status = ScoringService.determine_gap_status(project)
        assert status == 'green'
