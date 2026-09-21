import pytest
from app.scrapers.scrapers import BaseScraper, ScraperFactory


@pytest.fixture
def scraper():
    return BaseScraper("Test Source", "https://test.com")


class TestBaseScraper:

    def test_normalize_data_basic(self, scraper):
        data = {
            'name': '  Test  Project  ',
            'description': '  A  test  description  ',
            'source_url': 'example.com',
            'website': 'https://example.com',
            'github_url': 'https://github.com/test/project',
            'category': 'ai saas',
            'likes': '1.5K',
            'github_stars': '500',
            'rating': 4.5,
        }
        result = scraper.normalize_data(data)
        assert result['name'] == 'Test Project'
        assert result['description'] == 'A test description'
        assert result['source_url'] == 'https://example.com'
        assert result['website'] == 'https://example.com'
        assert result['github_url'] == 'https://github.com/test/project'
        assert result['category'] == 'ai_saas'
        assert result['source_name'] == 'Test Source'

    def test_normalize_data_numeric_fields(self, scraper):
        data = {
            'name': 'Test',
            'likes': '1.5K',
            'github_stars': '2.3M',
            'github_forks': '1.2K',
            'downloads': 50000,
            'users_count': '10K',
            'reviews_count': '500',
        }
        result = scraper.normalize_data(data)
        assert result['likes'] == 1500
        assert result['github_stars'] == 2300000
        assert result['github_forks'] == 1200
        assert result['downloads'] == 50000
        assert result['users_count'] == 10000
        assert result['reviews_count'] == 500

    def test_normalize_data_empty_fields(self, scraper):
        result = scraper.normalize_data({'name': 'Test'})
        assert result['likes'] == 0
        assert result['github_stars'] == 0
        assert result['rating'] is None
        assert result['investment_amount'] is None

    def test_parse_number_k_suffix(self, scraper):
        assert scraper._parse_number('1.5K') == 1500
        assert scraper._parse_number('2k') == 2000
        assert scraper._parse_number('0.5K') == 500

    def test_parse_number_m_suffix(self, scraper):
        assert scraper._parse_number('1M') == 1000000
        assert scraper._parse_number('2.5m') == 2500000

    def test_parse_number_b_suffix(self, scraper):
        assert scraper._parse_number('1B') == 1000000000
        assert scraper._parse_number('1.2b') == 1200000000

    def test_parse_number_integer(self, scraper):
        assert scraper._parse_number(42) == 42
        assert scraper._parse_number(0) == 0

    def test_parse_number_string_integer(self, scraper):
        assert scraper._parse_number('100') == 100
        assert scraper._parse_number('1,000') == 1000

    def test_parse_number_empty(self, scraper):
        assert scraper._parse_number(None) == 0
        assert scraper._parse_number('') == 0

    def test_normalize_category_saas(self, scraper):
        assert scraper._normalize_category('saas') == 'ai_saas'
        assert scraper._normalize_category('ai saas') == 'ai_saas'

    def test_normalize_category_open_source(self, scraper):
        assert scraper._normalize_category('open source') == 'open_source'
        assert scraper._normalize_category('opensource') == 'open_source'
        assert scraper._normalize_category('github') == 'open_source'

    def test_normalize_category_ai_models(self, scraper):
        assert scraper._normalize_category('ai model') == 'ai_models'
        assert scraper._normalize_category('ai models') == 'ai_models'
        assert scraper._normalize_category('huggingface') == 'ai_models'

    def test_normalize_category_telegram(self, scraper):
        assert scraper._normalize_category('telegram') == 'telegram'
        assert scraper._normalize_category('telegram bot') == 'telegram'

    def test_normalize_category_chrome(self, scraper):
        assert scraper._normalize_category('chrome') == 'chrome_extensions'
        assert scraper._normalize_category('extension') == 'chrome_extensions'

    def test_normalize_category_unknown(self, scraper):
        result = scraper._normalize_category('some_new_category')
        assert result == 'some_new_category'


class TestScraperFactory:

    def test_get_scraper_valid(self):
        scraper = ScraperFactory.get_scraper('Product Hunt')
        assert scraper is not None
        assert scraper.source_name == 'Product Hunt'

    def test_get_scraper_valid_github(self):
        scraper = ScraperFactory.get_scraper('GitHub Trending')
        assert scraper is not None
        assert scraper.source_name == 'GitHub Trending'

    def test_get_scraper_invalid(self):
        scraper = ScraperFactory.get_scraper('Non Existent Source')
        assert scraper is None

    def test_list_scrapers(self):
        scrapers = ScraperFactory.list_scrapers()
        assert isinstance(scrapers, list)
        assert 'Product Hunt' in scrapers
        assert 'GitHub Trending' in scrapers
        assert len(scrapers) > 5
