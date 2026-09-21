import pytest
from app.services.scoring import ScoringService


class TestScoringService:

    def test_calculate_copy_score(self, mock_project):
        project = mock_project({
            'implementation_complexity': 30,
            'category': 'ai_saas',
            'github_stars': 500,
        })
        score = ScoringService.calculate_copy_score(project)
        assert isinstance(score, int)
        assert 0 <= score <= 100
        assert score > 50

    def test_calculate_copy_score_hard_to_copy(self, mock_project):
        project = mock_project({
            'implementation_complexity': 90,
            'category': 'ai_models',
            'github_stars': 20000,
            'has_subscription': True,
        })
        score = ScoringService.calculate_copy_score(project)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_calculate_money_score(self, mock_project):
        project = mock_project({
            'investment_amount': 5000000,
            'has_subscription': True,
            'market_size': 'large',
            'github_stars': 3000,
            'likes': 500,
        })
        score = ScoringService.calculate_money_score(project)
        assert isinstance(score, int)
        assert 0 <= score <= 100
        assert score > 50

    def test_calculate_money_score_no_monetization(self, mock_project):
        project = mock_project({
            'investment_amount': None,
            'has_subscription': False,
            'has_freemium': False,
            'market_size': 'small',
            'github_stars': 0,
            'likes': 0,
        })
        score = ScoringService.calculate_money_score(project)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_calculate_viral_score(self, mock_project):
        project = mock_project({
            'viral_potential': 80,
            'github_stars': 15000,
            'likes': 6000,
            'growth_potential': 70,
            'category': 'ai_saas',
        })
        score = ScoringService.calculate_viral_score(project)
        assert isinstance(score, int)
        assert 0 <= score <= 100
        assert score > 50

    def test_calculate_viral_score_low_potential(self, mock_project):
        project = mock_project({
            'viral_potential': 10,
            'github_stars': 0,
            'likes': 0,
            'growth_potential': 10,
            'category': 'ai_models',
        })
        score = ScoringService.calculate_viral_score(project)
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_determine_gap_status_green(self, mock_project):
        project = mock_project({
            'has_russia_analog': False,
            'has_cis_analog': False,
            'has_strong_competitor': False,
            'has_weak_competitor': False,
        })
        status = ScoringService.determine_gap_status(project)
        assert status == 'green'

    def test_determine_gap_status_red(self, mock_project):
        project = mock_project({
            'has_strong_competitor': True,
        })
        status = ScoringService.determine_gap_status(project)
        assert status == 'red'

    def test_determine_gap_status_yellow(self, mock_project):
        project = mock_project({
            'has_russia_analog': False,
            'has_cis_analog': True,
        })
        status = ScoringService.determine_gap_status(project)
        assert status in ('yellow', 'green')

    def test_estimate_budget_low_complexity(self, mock_project):
        project = mock_project({'implementation_complexity': 20})
        budget = ScoringService.estimate_budget(project)
        assert budget == "$1K - $5K"

    def test_estimate_budget_medium_complexity(self, mock_project):
        project = mock_project({'implementation_complexity': 55})
        budget = ScoringService.estimate_budget(project)
        assert budget == "$5K - $20K" or budget == "$20K - $50K"

    def test_estimate_budget_high_complexity(self, mock_project):
        project = mock_project({'implementation_complexity': 95})
        budget = ScoringService.estimate_budget(project)
        assert budget == "$100K+"

    def test_calculate_all_scores(self, mock_project):
        project = mock_project()
        scores = ScoringService.calculate_all_scores(project)
        assert isinstance(scores, dict)
        assert 'copy_score' in scores
        assert 'money_score' in scores
        assert 'viral_score' in scores
        assert 'startup_score' in scores
        assert 'russia_opportunity_score' in scores
        assert 'coolness_score' in scores
        for key, value in scores.items():
            assert 0 <= value <= 100
