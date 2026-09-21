import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.scrapers.scrapers import (
    VentureBeatScraper, ProductHuntScraper, HackerNewsScraper,
    GitHubTrendingScraper, TechCrunchScraper, RedditScraper,
    BaseScraper
)

RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>VentureBeat</title>
    <item>
      <title>New AI startup raises $50M for SaaS platform</title>
      <link>https://venturebeat.com/ai-startup-2024</link>
      <description><![CDATA[This AI startup is building a revolutionary SaaS platform that uses machine learning to automate workflows.]]></description>
      <author>John Doe</author>
      <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Weather forecast article</title>
      <link>https://venturebeat.com/weather</link>
      <description>Weather forecast for tomorrow.</description>
      <author>Jane Smith</author>
    </item>
    <item>
      <title>ML model deployment startup launches</title>
      <link>https://venturebeat.com/ml-launch</link>
      <description>A new ML model deployment platform for enterprises.</description>
      <author>Bob Wilson</author>
    </item>
  </channel>
</rss>"""

PRODUCT_HUNT_GRAPHQL = {
    "data": {
        "posts": {
            "edges": [
                {
                    "node": {
                        "id": "12345",
                        "name": "AI Assistant Pro",
                        "tagline": "Smart AI assistant for developers",
                        "url": "https://www.producthunt.com/posts/12345",
                        "votesCount": 1500,
                        "website": "https://aiassistant.dev",
                        "topics": {"edges": [{"node": {"name": "AI"}}, {"node": {"name": "Developer Tools"}}]},
                        "makers": [{"name": "Alice Maker", "username": "alice"}],
                    }
                },
                {
                    "node": {
                        "id": "67890",
                        "name": "DataViz AI",
                        "tagline": "AI-powered data visualization",
                        "url": "https://www.producthunt.com/posts/67890",
                        "votesCount": 2300,
                        "website": "https://dataviz.ai",
                        "topics": {"edges": [{"node": {"name": "Analytics"}}]},
                        "makers": [{"name": "Bob Builder", "username": "bob"}],
                    }
                },
            ]
        }
    }
}

HACKER_NEWS_HTML = """
<html><body>
<table class="itemlist">
  <tr class="athing" id="12345">
    <td class="title"><span class="titleline"><a href="https://example.com/project1">Show HN: AI Code Assistant</a></span></td>
  </tr>
  <tr><td class="subtext"><span class="score">120 points</span></td></tr>
  <tr class="athing" id="67890">
    <td class="title"><span class="titleline"><a href="https://example.com/project2">Launch HN: ML Platform for Teams</a></span></td>
  </tr>
  <tr><td class="subtext"><span class="score">350 points</span></td></tr>
</table></body></html>
"""

GITHUB_TRENDING_HTML = """
<html><body>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/owner/repo1">owner / repo1</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">An awesome AI project description</p>
  <div class="f6 color-fg-muted mt-2">
    <a class="Link--muted" href="/owner/repo1/stargazers">1,500</a>
    <a class="Link--muted" href="/owner/repo1/forks">42</a>
    <span class="d-inline-block mr-3"><span itemprop="programmingLanguage">Python</span></span>
  </div>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed"><a href="/owner2/repo2">owner2 / repo2</a></h2>
  <p class="col-9 color-fg-muted my-1 pr-4">Machine learning framework for everyone</p>
  <div class="f6 color-fg-muted mt-2">
    <a class="Link--muted" href="/owner2/repo2/stargazers">5,200</a>
    <a class="Link--muted" href="/owner2/repo2/forks">120</a>
    <span class="d-inline-block mr-3"><span itemprop="programmingLanguage">TypeScript</span></span>
  </div>
</article>
</body></html>
"""

TECHCRUNCH_HTML = """
<html><body>
<div class="post-block">
  <header class="post-block__header">
    <h2 class="post-block__title"><a href="https://techcrunch.com/2024/01/01/ai-startup">AI Startup Raises $20M Series A</a></h2>
  </header>
  <div class="post-block__content">A promising AI startup has raised $20 million in Series A funding to expand its platform.</div>
  <div class="post-block__author">By TechCrunch Author</div>
</div>
<div class="post-block">
  <header class="post-block__header">
    <h2 class="post-block__title"><a href="https://techcrunch.com/2024/01/02/ml-tool">New ML Tool Launches to Public</a></h2>
  </header>
  <div class="post-block__content">A new machine learning tool has launched publicly after a successful beta.</div>
  <div class="post-block__author">By Staff Writer</div>
</div>
</body></html>
"""

REDDIT_JSON = {
    "data": {
        "children": [
            {
                "data": {
                    "title": "I built an AI app that generates code",
                    "url": "https://example.com/ai-app",
                    "selftext": "I spent 6 months building this AI app",
                    "permalink": "/r/startups/comments/abc123/",
                    "score": 500,
                    "author": "dev",
                }
            },
            {
                "data": {
                    "title": "My SaaS reached $10k MRR",
                    "url": "https://example.com/saas",
                    "selftext": "After a year of hard work",
                    "permalink": "/r/SaaS/comments/def456/",
                    "score": 1200,
                    "author": "founder",
                }
            },
        ]
    }
}


@pytest.fixture(autouse=True)
def mock_vector_store():
    with patch('app.scrapers.scrapers.vector_store') as mock:
        mock.search_similar = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def mock_httpx(monkeypatch):
    responses = {}

    class MockResponse:
        def __init__(self, text, status_code=200, headers=None):
            self._text = text
            self.status_code = status_code
            self.headers = headers or {}
            self.cookies = {}

        def raise_for_status(self):
            if self.status_code >= 400:
                from httpx import HTTPStatusError
                raise HTTPStatusError("Error", request=MagicMock(), response=self)

        def json(self):
            import json
            return json.loads(self._text) if isinstance(self._text, str) else self._text

        @property
        def text(self):
            return self._text if isinstance(self._text, str) else ""

    class MockClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, **kwargs):
            for pattern, response_data in responses.items():
                if pattern in url:
                    text, status, headers = response_data
                    return MockResponse(text, status, headers)
            return MockResponse("", 404)

        async def post(self, url, **kwargs):
            for pattern, response_data in responses.items():
                if pattern in url:
                    text, status, headers = response_data
                    return MockResponse(text, status, headers)
            return MockResponse("", 404)

    def set_response(pattern, text, status=200, headers=None):
        responses[pattern] = (text, status, headers or {})

    monkeypatch.setattr('httpx.AsyncClient', MockClient)

    class Context:
        def set(self, *args, **kwargs):
            set_response(*args, **kwargs)

    context = Context()
    context.set = set_response
    return context


class TestVentureBeatIntegration:

    @pytest.mark.asyncio
    async def test_scrape_rss_returns_projects(self, mock_httpx, mock_vector_store):
        mock_httpx.set("venturebeat.com/feed", RSS_FEED)
        scraper = VentureBeatScraper()
        projects = await scraper.scrape()

        assert len(projects) == 2
        names = [p['name'] for p in projects]
        assert "New AI startup raises $50M for SaaS platform" in names
        assert "ML model deployment startup launches" in names
        assert "Non-AI article about weather" not in names

    @pytest.mark.asyncio
    async def test_scrape_rss_fields_correct(self, mock_httpx, mock_vector_store):
        mock_httpx.set("venturebeat.com/feed", RSS_FEED)
        scraper = VentureBeatScraper()
        projects = await scraper.scrape()

        project = projects[0]
        assert project['source_name'] == 'VentureBeat'
        assert 'venturebeat.com' in project['source_url']
        assert project['category'] == 'ai_saas'
        assert 'machine learning' in project['description'].lower()

    @pytest.mark.asyncio
    async def test_scrape_falls_back_to_web_when_rss_empty(self, mock_httpx, mock_vector_store):
        mock_httpx.set("venturebeat.com/feed", "")
        mock_httpx.set("venturebeat.com/category/ai", TECHCRUNCH_HTML)
        scraper = VentureBeatScraper()

        with patch.object(scraper, '_scrape_web') as mock_web:
            mock_web.return_value = []
            projects = await scraper.scrape()
            assert len(projects) == 0


class TestProductHuntIntegration:

    @pytest.mark.asyncio
    async def test_scrape_api_returns_projects(self, mock_httpx, mock_vector_store):
        import json
        mock_httpx.set("api.producthunt.com", json.dumps(PRODUCT_HUNT_GRAPHQL))
        scraper = ProductHuntScraper()
        scraper.api_token = "test-token"

        projects = await scraper.scrape()
        assert len(projects) == 2

    @pytest.mark.asyncio
    async def test_scrape_api_fields(self, mock_httpx, mock_vector_store):
        import json
        mock_httpx.set("api.producthunt.com", json.dumps(PRODUCT_HUNT_GRAPHQL))
        scraper = ProductHuntScraper()
        scraper.api_token = "test-token"

        projects = await scraper.scrape()
        project = projects[0]
        assert project['name'] == 'AI Assistant Pro'
        assert 'Smart AI assistant' in project['description']
        assert project['source_name'] == 'Product Hunt'
        assert project['category'] == 'ai_saas'
        assert project['likes'] == 1500
        assert 'Alice' in project['author']


class TestHackerNewsIntegration:

    @pytest.mark.asyncio
    async def test_scrape_from_html(self, mock_httpx, mock_vector_store):
        mock_httpx.set("news.ycombinator.com", HACKER_NEWS_HTML)
        scraper = HackerNewsScraper()
        projects = await scraper.scrape()

        assert len(projects) == 2
        names = [p['name'] for p in projects]
        assert any('AI Code Assistant' in n for n in names)
        assert any('ML Platform' in n for n in names)


class TestGitHubTrendingIntegration:

    @pytest.mark.asyncio
    async def test_scrape_parses_repos(self, mock_httpx, mock_vector_store):
        mock_httpx.set("github.com/trending", GITHUB_TRENDING_HTML)
        scraper = GitHubTrendingScraper()
        projects = await scraper.scrape()

        assert len(projects) == 2
        names = [p['name'] for p in projects]
        assert 'repo1' in names
        assert 'repo2' in names

    @pytest.mark.asyncio
    async def test_scrape_parses_github_metrics(self, mock_httpx, mock_vector_store):
        mock_httpx.set("github.com/trending", GITHUB_TRENDING_HTML)
        scraper = GitHubTrendingScraper()
        projects = await scraper.scrape()

        project = projects[0]
        assert project['github_stars'] == 1500
        assert project['github_forks'] == 42
        assert project['github_language'] == 'Python'
        assert project['source_name'] == 'GitHub Trending'
        assert project['category'] == 'open_source'


class TestTechCrunchIntegration:

    @pytest.mark.asyncio
    async def test_scrape_parses_articles(self, mock_httpx, mock_vector_store):
        mock_httpx.set("techcrunch.com", TECHCRUNCH_HTML)
        scraper = TechCrunchScraper()
        projects = await scraper.scrape()

        assert len(projects) == 2
        names = [p['name'] for p in projects]
        assert any('AI Startup Raises' in n for n in names)
        assert any('New ML Tool' in n for n in names)

    @pytest.mark.asyncio
    async def test_scrape_fields_correct(self, mock_httpx, mock_vector_store):
        mock_httpx.set("techcrunch.com", TECHCRUNCH_HTML)
        scraper = TechCrunchScraper()
        projects = await scraper.scrape()

        project = projects[0]
        assert 'techcrunch.com' in project['source_url']
        assert project['source_name'] == 'TechCrunch'
        assert project['category'] == 'ai_saas'


class TestRedditIntegration:

    @pytest.mark.asyncio
    async def test_scrape_parses_posts(self, mock_httpx, mock_vector_store):
        import json
        mock_httpx.set("reddit.com/r/startups/hot.json", json.dumps(REDDIT_JSON))
        mock_httpx.set("reddit.com/r/SaaS/hot.json", json.dumps({"data": {"children": []}}))
        mock_httpx.set("reddit.com/r/Entrepreneur/hot.json", json.dumps({"data": {"children": []}}))
        scraper = RedditScraper()
        projects = await scraper.scrape()

        assert len(projects) == 2
        assert projects[0]['name'] == 'I built an AI app that generates code'


class TestScraperPipeline:

    @pytest.mark.asyncio
    async def test_full_scrape_normalize_fingerprint_pipeline(self, mock_httpx, mock_vector_store):
        mock_httpx.set("venturebeat.com/feed", RSS_FEED)
        scraper = VentureBeatScraper()
        projects = await scraper.scrape()

        for project in projects:
            assert 'fingerprint' in project
            assert project['name']
            assert project['source_url']
            assert project['category']
            assert project['source_name'] == 'VentureBeat'
            assert isinstance(project['fingerprint'], str)
            assert len(project['fingerprint']) == 32

    @pytest.mark.asyncio
    async def test_deduplication_skips_duplicates(self, mock_httpx, mock_vector_store):
        mock_vector_store.search_similar.return_value = [
            {'id': 'existing-id', 'score': 0.95}
        ]
        mock_httpx.set("venturebeat.com/feed", RSS_FEED)
        scraper = VentureBeatScraper()
        projects = await scraper.scrape()

        assert len(projects) == 0

    @pytest.mark.asyncio
    async def test_scraper_factory_returns_working_scrapers(self):
        from app.scrapers.scrapers import ScraperFactory
        for name in ['Product Hunt', 'GitHub Trending', 'Hacker News',
                      'TechCrunch', 'Reddit', 'VentureBeat', 'YC Launches']:
            scraper = ScraperFactory.get_scraper(name)
            assert scraper is not None, f"Scraper {name} not found"
            assert scraper.source_name == name

    def test_all_17_scrapers_available(self):
        from app.scrapers.scrapers import ScraperFactory
        scrapers = ScraperFactory.list_scrapers()
        expected = [
            'Product Hunt', 'GitHub Trending', 'Hacker News',
            'Hugging Face', 'TikTok', 'YouTube Shorts',
            'X (Twitter)', 'LinkedIn', 'TechCrunch', 'Reddit',
            'AppSumo', 'BetaList', 'IndieHackers',
            'Chrome Web Store', 'Google Play', 'VentureBeat', 'YC Launches'
        ]
        for name in expected:
            assert name in scrapers, f"Missing scraper: {name}"
        assert len(scrapers) == 17
