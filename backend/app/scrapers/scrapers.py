import httpx
import asyncio
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import re
import json
import hashlib
import feedparser
from urllib.parse import urljoin, urlparse
from app.core.config import settings
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class BaseScraper:
    """Базовый класс для всех скрапперов с продвинутой дедупликацией"""
    
    def __init__(self, source_name: str, source_url: str):
        self.source_name = source_name
        self.source_url = source_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session_cookies = {}
        self.rate_limit_delay = 1.0  # seconds between requests
        self.max_retries = 5
        self.retry_delays = [1, 2, 5, 10, 30]  # exponential backoff
    
    async def fetch(self, url: str, retries: int = None, headers: Dict = None, 
                    return_json: bool = False, method: str = "GET", 
                    data: Dict = None, proxy: str = None) -> Optional[Any]:
        """Улучшенная загрузка с обходом ограничений"""
        retries = retries or self.max_retries
        request_headers = {**self.headers, **(headers or {})}
        
        async with httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT, 
            follow_redirects=True,
            proxies={"http://": proxy, "https://": proxy} if proxy else None
        ) as client:
            for attempt in range(retries):
                try:
                    if method == "GET":
                        response = await client.get(url, headers=request_headers, cookies=self.session_cookies)
                    elif method == "POST":
                        response = await client.post(url, headers=request_headers, json=data, cookies=self.session_cookies)
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', self.retry_delays[min(attempt, len(self.retry_delays)-1)]))
                        await asyncio.sleep(retry_after)
                        continue
                    
                    # Handle Cloudflare and other protections
                    if response.status_code == 403 and 'cloudflare' in response.text.lower():
                        # Try with different headers
                        request_headers['User-Agent'] = self._rotate_user_agent()
                        await asyncio.sleep(self.retry_delays[min(attempt, len(self.retry_delays)-1)])
                        continue
                    
                    response.raise_for_status()
                    
                    # Store cookies for session
                    self.session_cookies.update(response.cookies)
                    
                    if return_json:
                        return response.json()
                    return response.text
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 404:
                        return None
                    if attempt == retries - 1:
                        logger.error("Failed to fetch %s: %s", url, e)
                        return None
                    await asyncio.sleep(self.retry_delays[min(attempt, len(self.retry_delays)-1)])
                    
                except Exception as e:
                    if attempt == retries - 1:
                        logger.error("Failed to fetch %s: %s", url, e)
                        return None
                    await asyncio.sleep(self.retry_delays[min(attempt, len(self.retry_delays)-1)])
        
        return None
    
    def _rotate_user_agent(self) -> str:
        """Rotate user agent to avoid blocks"""
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
        import random
        return random.choice(agents)
    
    def normalize_data(self, data: Dict) -> Dict:
        """Нормализация данных проекта"""
        normalized = {
            'name': self._clean_text(data.get('name', 'Unknown')),
            'description': self._clean_text(data.get('description', '')),
            'source_url': self._normalize_url(data.get('source_url', '')),
            'website': self._normalize_url(data.get('website', '')),
            'github_url': self._normalize_url(data.get('github_url', '')),
            'category': self._normalize_category(data.get('category', 'unknown')),
            'source_name': self.source_name,
            'discovered_at': datetime.utcnow(),
        }
        
        # Numeric fields
        for field in ['likes', 'github_stars', 'github_forks', 'downloads', 'users_count', 'reviews_count']:
            value = data.get(field)
            normalized[field] = self._parse_number(value) if value else 0
        
        # Rating
        rating = data.get('rating')
        normalized['rating'] = float(rating) if rating else None
        
        # Investment
        investment = data.get('investment_amount')
        normalized['investment_amount'] = float(investment) if investment else None
        normalized['investment_stage'] = data.get('investment_stage')
        normalized['investors'] = data.get('investors')
        
        # GitHub
        normalized['github_language'] = data.get('github_language')
        
        # Author
        normalized['author'] = self._clean_text(data.get('author', ''))
        normalized['author_url'] = self._normalize_url(data.get('author_url', ''))
        
        return normalized
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ''
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\-.,!?@#$%&*()\/\'"]', '', text)
        return text.strip()
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL"""
        if not url:
            return ''
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category name"""
        category_map = {
            'saas': 'ai_saas',
            'ai saas': 'ai_saas',
            'startup': 'startups',
            'startups': 'startups',
            'open source': 'open_source',
            'opensource': 'open_source',
            'github': 'open_source',
            'ai model': 'ai_models',
            'ai models': 'ai_models',
            'huggingface': 'ai_models',
            'ai agent': 'ai_agents',
            'ai agents': 'ai_agents',
            'mcp': 'mcp',
            'mobile': 'mobile_apps',
            'mobile app': 'mobile_apps',
            'app': 'mobile_apps',
            'telegram': 'telegram',
            'telegram bot': 'telegram',
            'chrome': 'chrome_extensions',
            'extension': 'chrome_extensions',
            'browser extension': 'chrome_extensions',
        }
        return category_map.get(category.lower().strip(), category.lower().strip().replace(' ', '_'))
    
    def _parse_number(self, value) -> int:
        """Parse number with K, M, B suffixes"""
        if isinstance(value, (int, float)):
            return int(value)
        if not value:
            return 0
        
        text = str(value).strip().replace(',', '').replace(' ', '')
        
        # Handle K, M, B
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
        for suffix, multiplier in multipliers.items():
            if suffix in text.lower():
                try:
                    return int(float(text.lower().replace(suffix, '')) * multiplier)
                except (ValueError, TypeError):
                    return 0
        
        try:
            return int(float(text))
        except (ValueError, TypeError):
            return 0
    
    def generate_fingerprint(self, data: Dict) -> str:
        """Generate unique fingerprint for deduplication"""
        # Create fingerprint from name + domain
        name = data.get('name', '').lower().strip()
        url = data.get('source_url', '') or data.get('website', '')
        domain = urlparse(url).netloc.lower() if url else ''
        
        fingerprint = f"{name}:{domain}"
        return hashlib.md5(fingerprint.encode()).hexdigest()
    
    async def check_duplicate(self, data: Dict) -> Optional[Dict]:
        """Check for duplicates using vector search and fingerprint"""
        fingerprint = self.generate_fingerprint(data)
        
        # Check vector store for semantic similarity
        similar = await vector_store.search_similar(
            text=f"{data.get('name', '')} {data.get('description', '')}",
            threshold=0.85
        )
        
        if similar:
            return {
                'is_duplicate': True,
                'duplicate_id': similar[0]['id'],
                'similarity': similar[0]['score'],
                'fingerprint': fingerprint
            }
        
        return {
            'is_duplicate': False,
            'fingerprint': fingerprint
        }
    
    async def scrape(self) -> List[Dict]:
        """Метод для переопределения в дочерних классах"""
        raise NotImplementedError


class ProductHuntScraper(BaseScraper):
    """Полноценный скраппер Product Hunt с API fallback"""
    
    def __init__(self):
        super().__init__("Product Hunt", "https://www.producthunt.com")
        self.api_token = None  # Can be set via environment
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг Product Hunt с API и fallback"""
        projects = []
        
        # Try API first if token available
        if self.api_token:
            api_projects = await self._scrape_api()
            if api_projects:
                projects.extend(api_projects)
        
        # Fallback to web scraping
        if not projects:
            web_projects = await self._scrape_web()
            projects.extend(web_projects)
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects
    
    async def _scrape_api(self) -> List[Dict]:
        """Scrape using Product Hunt GraphQL API"""
        graphql_query = {
            "query": """
            query {
                posts(first: 20, order: RANKING) {
                    edges {
                        node {
                            id
                            name
                            tagline
                            url
                            votesCount
                            website
                            thumbnail {
                                url
                            }
                            topics {
                                edges {
                                    node {
                                        name
                                    }
                                }
                            }
                            makers {
                                name
                                username
                            }
                        }
                    }
                }
            }
            """
        }
        
        headers = {
            **self.headers,
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }
        
        data = await self.fetch(
            "https://api.producthunt.com/v2/api/graphql",
            method="POST",
            headers=headers,
            data=graphql_query,
            return_json=True
        )
        
        if not data or 'data' not in data:
            return []
        
        projects = []
        for edge in data['data']['posts']['edges']:
            node = edge['node']
            projects.append({
                'name': node['name'],
                'description': node['tagline'],
                'source_url': f"https://www.producthunt.com/posts/{node['id']}",
                'website': node.get('website', ''),
                'likes': node.get('votesCount', 0),
                'category': 'ai_saas',
                'author': ', '.join([m['name'] for m in node.get('makers', [])]),
            })
        
        return projects
    
    async def _scrape_web(self) -> List[Dict]:
        """Fallback web scraping"""
        html = await self.fetch("https://www.producthunt.com/")
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        
        # Multiple selectors for robustness
        selectors = [
            'div[data-test="post-item"]',
            'div[class*="postItem"]',
            'article[class*="post"]',
        ]
        
        posts = []
        for selector in selectors:
            posts = soup.find_all(selector.split('[')[0], 
                                {k:v for k,v in [sel.split('=') for sel in selector.split('[')[1:]]} if '[' in selector else {})
            if posts:
                break
        
        for post in posts[:20]:
            try:
                name_elem = post.find('h2') or post.find('a', {'data-test': 'post-name'}) or post.find('a', class_=re.compile(r'title|name'))
                desc_elem = post.find('p') or post.find('div', {'data-test': 'post-description'}) or post.find('div', class_=re.compile(r'description|tagline'))
                link_elem = post.find('a', href=re.compile(r'/posts/')) or post.find('a', href=True)
                votes_elem = post.find('button', {'data-test': 'vote-button'}) or post.find('span', class_=re.compile(r'vote|like|count'))
                
                name = name_elem.text.strip() if name_elem else "Unknown"
                description = desc_elem.text.strip() if desc_elem else ""
                
                url = ""
                if link_elem:
                    href = link_elem.get('href', '')
                    url = urljoin("https://www.producthunt.com", href) if not href.startswith('http') else href
                
                votes = 0
                if votes_elem:
                    votes_text = votes_elem.text.strip()
                    votes_match = re.search(r'(\d+)', votes_text)
                    votes = int(votes_match.group(1)) if votes_match else 0
                
                projects.append({
                    'name': name,
                    'description': description,
                    'source_url': url,
                    'website': url,
                    'likes': votes,
                    'category': 'ai_saas',
                })
            except Exception as e:
                continue
        
        return projects


class GitHubTrendingScraper(BaseScraper):
    """Полноценный скраппер GitHub Trending"""
    
    def __init__(self):
        super().__init__("GitHub Trending", "https://github.com/trending")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг GitHub Trending с API и web fallback"""
        projects = []
        
        # Try GitHub API first
        api_projects = await self._scrape_api()
        if api_projects:
            projects.extend(api_projects)
        
        # Fallback to web
        if not projects:
            web_projects = await self._scrape_web()
            projects.extend(web_projects)
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects
    
    async def _scrape_api(self) -> List[Dict]:
        """Scrape using GitHub API"""
        # Search for trending repos created in last 30 days
        query = "created:>" + (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        data = await self.fetch(
            f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=25",
            return_json=True
        )
        
        if not data or 'items' not in data:
            return []
        
        projects = []
        for item in data['items']:
            projects.append({
                'name': item['name'],
                'description': item.get('description', ''),
                'source_url': item['html_url'],
                'website': item['html_url'],
                'github_url': item['html_url'],
                'github_stars': item.get('stargazers_count', 0),
                'github_forks': item.get('forks_count', 0),
                'github_language': item.get('language', 'Unknown'),
                'category': 'open_source',
                'author': item.get('owner', {}).get('login', ''),
                'author_url': item.get('owner', {}).get('html_url', ''),
            })
        
        return projects
    
    async def _scrape_web(self) -> List[Dict]:
        """Fallback web scraping"""
        html = await self.fetch("https://github.com/trending?since=daily")
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        
        repos = soup.find_all('article', class_='Box-row')
        
        for repo in repos[:25]:
            try:
                link = repo.find('h2', class_='h3')
                if not link:
                    continue
                
                full_name = link.text.strip().replace('\n', '').replace(' ', '')
                url = f"https://github.com/{full_name}"
                
                desc = repo.find('p', class_='col-9')
                description = desc.text.strip() if desc else ""
                
                stars_elem = repo.find('a', href=re.compile(r'/stargazers'))
                stars_text = stars_elem.text.strip() if stars_elem else "0"
                stars = self._parse_number(stars_text)
                
                lang_elem = repo.find('span', itemprop='programmingLanguage')
                language = lang_elem.text.strip() if lang_elem else "Unknown"
                
                forks_elem = repo.find('a', href=re.compile(r'/forks'))
                forks_text = forks_elem.text.strip() if forks_elem else "0"
                forks = self._parse_number(forks_text)
                
                projects.append({
                    'name': full_name.split('/')[-1],
                    'description': description,
                    'source_url': url,
                    'website': url,
                    'github_url': url,
                    'github_stars': stars,
                    'github_forks': forks,
                    'github_language': language,
                    'category': 'open_source',
                })
            except Exception as e:
                continue
        
        return projects


class HackerNewsScraper(BaseScraper):
    """Полноценный скраппер Hacker News"""
    
    def __init__(self):
        super().__init__("Hacker News", "https://news.ycombinator.com")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг Hacker News через API"""
        projects = []
        
        # Use Algolia API for better results
        api_projects = await self._scrape_api()
        if api_projects:
            projects.extend(api_projects)
        
        # Fallback to web
        if not projects:
            web_projects = await self._scrape_web()
            projects.extend(web_projects)
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects
    
    async def _scrape_api(self) -> List[Dict]:
        """Scrape using HN Algolia API"""
        # Search for Show HN and AI-related posts in last 24 hours
        query = "show hn OR (AI OR GPT OR LLM OR chatbot OR agent)"
        
        data = await self.fetch(
            f"https://hn.algolia.com/api/v1/search_by_date?query={query}&tags=story&numericFilters=created_at_i>{(datetime.utcnow() - timedelta(hours=24)).timestamp()}",
            return_json=True
        )
        
        if not data or 'hits' not in data:
            return []
        
        projects = []
        for hit in data['hits']:
            title = hit.get('title', '')
            
            # Filter for relevant posts
            is_show_hn = title.startswith('Show HN:')
            is_ai = any(kw in title.lower() for kw in ['ai', 'ml', 'gpt', 'llm', 'neural', 'chatbot', 'agent'])
            
            if not (is_show_hn or is_ai):
                continue
            
            if is_show_hn:
                title = title.replace('Show HN:', '').strip()
            
            projects.append({
                'name': title[:200],
                'description': hit.get('story_text', '')[:500] or title,
                'source_url': f"https://news.ycombinator.com/item?id={hit['objectID']}",
                'website': hit.get('url', ''),
                'likes': hit.get('points', 0),
                'category': 'startups',
                'author': hit.get('author', ''),
            })
        
        return projects
    
    async def _scrape_web(self) -> List[Dict]:
        """Fallback web scraping"""
        html = await self.fetch("https://news.ycombinator.com/show")
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        
        items = soup.find_all('tr', class_='athing')
        
        for item in items[:30]:
            try:
                title_elem = item.find('span', class_='titleline')
                if not title_elem:
                    continue
                
                link = title_elem.find('a')
                title = link.text.strip() if link else ""
                url = link['href'] if link else ""
                
                is_show_hn = title.startswith('Show HN:')
                is_ai = any(kw in title.lower() for kw in ['ai', 'ml', 'gpt', 'llm', 'neural', 'chatbot', 'agent'])
                
                if not (is_show_hn or is_ai):
                    continue
                
                if is_show_hn:
                    title = title.replace('Show HN:', '').strip()
                
                score_elem = item.find_next_sibling('tr')
                if score_elem:
                    score_span = score_elem.find('span', class_='score')
                    score = int(re.findall(r'\d+', score_span.text)[0]) if score_span else 0
                else:
                    score = 0
                
                projects.append({
                    'name': title[:200],
                    'description': title,
                    'source_url': f"https://news.ycombinator.com/item?id={item.get('id', '')}",
                    'website': url if url.startswith('http') else f"https://news.ycombinator.com/{url}",
                    'likes': score,
                    'category': 'startups',
                })
            except Exception as e:
                continue
        
        return projects


class HuggingFaceScraper(BaseScraper):
    """Полноценный скраппер Hugging Face"""
    
    def __init__(self):
        super().__init__("Hugging Face", "https://huggingface.co")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг Hugging Face trending models"""
        projects = []
        
        # Try API first
        api_projects = await self._scrape_api()
        if api_projects:
            projects.extend(api_projects)
        
        # Fallback to web
        if not projects:
            web_projects = await self._scrape_web()
            projects.extend(web_projects)
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects
    
    async def _scrape_api(self) -> List[Dict]:
        """Scrape using Hugging Face API"""
        data = await self.fetch(
            "https://huggingface.co/api/models?sort=likes&direction=-1&limit=25",
            return_json=True
        )
        
        if not data or not isinstance(data, list):
            return []
        
        projects = []
        for item in data[:25]:
            projects.append({
                'name': item.get('id', '').split('/')[-1],
                'description': item.get('description', '') or item.get('cardData', {}).get('description', ''),
                'source_url': f"https://huggingface.co/{item.get('id', '')}",
                'website': f"https://huggingface.co/{item.get('id', '')}",
                'likes': item.get('likes', 0),
                'downloads': item.get('downloads', 0),
                'category': 'ai_models',
                'author': item.get('id', '').split('/')[0] if '/' in item.get('id', '') else '',
            })
        
        return projects
    
    async def _scrape_web(self) -> List[Dict]:
        """Fallback web scraping"""
        html = await self.fetch("https://huggingface.co/models?sort=trending")
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        
        models = soup.find_all('article', class_='transform') or soup.find_all('div', class_='model-card')
        
        for model in models[:20]:
            try:
                link = model.find('a', href=re.compile(r'^/[^/]+/[^/]+$'))
                if not link:
                    continue
                
                name = link.text.strip()
                url = f"https://huggingface.co{link['href']}"
                
                desc = model.find('p') or model.find('div', class_='text-sm')
                description = desc.text.strip() if desc else ""
                
                likes_elem = model.find('button', {'aria-label': 'Like'})
                likes = int(re.findall(r'\d+', likes_elem.text)[0]) if likes_elem else 0
                
                projects.append({
                    'name': name.split('/')[-1],
                    'description': description,
                    'source_url': url,
                    'website': url,
                    'likes': likes,
                    'category': 'ai_models',
                })
            except Exception as e:
                continue
        
        return projects


class TikTokScraper(BaseScraper):
    """Скраппер TikTok для поиска AI трендов"""
    
    def __init__(self):
        super().__init__("TikTok", "https://www.tiktok.com")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг TikTok через API"""
        projects = []
        
        # Try TikTok unofficial API
        data = await self.fetch(
            "https://www.tiktok.com/api/search/general/preview/?keyword=AI+startup+app",
            return_json=True
        )
        
        if data and 'data' in data:
            for item in data['data']:
                projects.append({
                    'name': item.get('title', 'TikTok AI Trend'),
                    'description': item.get('desc', 'AI тренд из TikTok'),
                    'source_url': f"https://www.tiktok.com/@{item.get('author', 'unknown')}",
                    'website': f"https://www.tiktok.com/@{item.get('author', 'unknown')}",
                    'likes': item.get('stats', {}).get('diggCount', 0),
                    'category': 'ai_saas',
                    'author': item.get('author', ''),
                })
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects


class YouTubeShortsScraper(BaseScraper):
    """Скраппер YouTube Shorts для AI трендов"""
    
    def __init__(self):
        super().__init__("YouTube Shorts", "https://www.youtube.com")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг YouTube Shorts через RSS/API"""
        projects = []
        
        # Try YouTube RSS feed for AI-related shorts
        feed = await self.fetch(
            "https://www.youtube.com/feeds/videos.xml?search_query=AI+startup+app+shorts",
            return_json=False
        )
        
        if feed:
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(feed)
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                for entry in root.findall('atom:entry', ns)[:20]:
                    title = entry.find('atom:title', ns).text if entry.find('atom:title', ns) else "YouTube AI Trend"
                    link = entry.find('atom:link', ns).get('href', '') if entry.find('atom:link', ns) else ''
                    
                    projects.append({
                        'name': title[:200],
                        'description': f"AI тренд из YouTube Shorts: {title}",
                        'source_url': link,
                        'website': link,
                        'category': 'ai_saas',
                    })
            except (ValueError, TypeError, AttributeError):
                pass
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects


class XScraper(BaseScraper):
    """Скраппер X (Twitter) для AI трендов"""
    
    def __init__(self):
        super().__init__("X (Twitter)", "https://x.com")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг X через Nitter API (без авторизации)"""
        projects = []
        
        # Try Nitter instances for public Twitter data
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.it",
            "https://nitter.cz"
        ]
        
        for instance in nitter_instances:
            try:
                html = await self.fetch(f"{instance}/search?f=tweets&q=AI+startup+app&since={datetime.utcnow().strftime('%Y-%m-%d')}")
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    tweets = soup.find_all('div', class_='timeline-item')
                    
                    for tweet in tweets[:15]:
                        try:
                            content = tweet.find('div', class_='tweet-content')
                            if content:
                                text = content.get_text(strip=True)
                                link = tweet.find('a', class_='tweet-link')
                                url = f"{instance}{link['href']}" if link else instance
                                
                                if len(text) > 20 and any(kw in text.lower() for kw in ['ai', 'startup', 'app', 'bot']):
                                    projects.append({
                                        'name': text[:100],
                                        'description': text[:500],
                                        'source_url': url,
                                        'website': url,
                                        'category': 'startups',
                                    })
                        except (ValueError, TypeError, AttributeError):
                            continue
                    
                    if projects:
                        break  # Stop if we got results
                        
            except Exception as e:
                continue
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects


class LinkedInScraper(BaseScraper):
    """Скраппер LinkedIn для AI стартапов"""
    
    def __init__(self):
        super().__init__("LinkedIn", "https://www.linkedin.com")
    
    async def scrape(self) -> List[Dict]:
        """Скрапинг LinkedIn через RSS и публичные страницы"""
        projects = []
        
        # Try LinkedIn RSS feeds for AI content
        feed = await self.fetch(
            "https://www.linkedin.com/in/rss/",
            return_json=False
        )
        
        # Fallback: search for AI startup posts via Google
        search_html = await self.fetch(
            "https://www.google.com/search?q=site:linkedin.com/posts+AI+startup+app+2026",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        if search_html:
            soup = BeautifulSoup(search_html, 'html.parser')
            results = soup.find_all('div', class_='g')
            
            for result in results[:10]:
                try:
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        
                        if 'linkedin.com' in url and any(kw in title.lower() for kw in ['ai', 'startup', 'app']):
                            projects.append({
                                'name': title[:200],
                                'description': f"LinkedIn AI стартап: {title}",
                                'source_url': url,
                                'website': url,
                                'category': 'startups',
                            })
                except (ValueError, TypeError, AttributeError):
                    continue
        
        # Normalize and deduplicate
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        
        return normalized_projects


class TechCrunchScraper(BaseScraper):
    """Scraper for TechCrunch AI startup articles via RSS"""

    def __init__(self):
        super().__init__("TechCrunch", "https://techcrunch.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        rss_projects = await self._scrape_rss()
        if rss_projects:
            projects.extend(rss_projects)
        if not projects:
            web_projects = await self._scrape_web()
            projects.extend(web_projects)
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects

    async def _scrape_rss(self) -> List[Dict]:
        feed = await self.fetch("https://techcrunch.com/feed/")
        if not feed:
            return []
        projects = []
        parsed = feedparser.parse(feed)
        for entry in parsed.entries[:20]:
            title = entry.get('title', '')
            if not any(kw in title.lower() for kw in ['ai', 'startup', 'app', 'saas', 'launch', 'tech']):
                continue
            projects.append({
                'name': title[:200],
                'description': entry.get('summary', '')[:500] or title,
                'source_url': entry.get('link', ''),
                'website': entry.get('link', ''),
                'category': 'ai_saas',
                'author': entry.get('author', ''),
            })
        return projects

    async def _scrape_web(self) -> List[Dict]:
        html = await self.fetch("https://techcrunch.com/category/artificial-intelligence/")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        articles = soup.find_all('article') or soup.find_all('div', class_='post-block')
        for article in articles[:20]:
            try:
                title_elem = article.find('h2') or article.find('h3') or article.find('a', class_='post-title')
                link_elem = article.find('a', href=True)
                desc_elem = article.find('p') or article.find('div', class_='post-excerpt')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                url = link_elem['href'] if link_elem else ''
                if url and not url.startswith('http'):
                    url = urljoin('https://techcrunch.com', url)
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                projects.append({
                    'name': title[:200],
                    'description': description[:500],
                    'source_url': url,
                    'website': url,
                    'category': 'ai_saas',
                })
            except (ValueError, TypeError, AttributeError):
                continue
        return projects


class RedditScraper(BaseScraper):
    """Scraper for Reddit r/startups and r/SaaS via JSON API"""

    def __init__(self):
        super().__init__("Reddit", "https://reddit.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        for subreddit in ['startups', 'SaaS', 'Entrepreneur']:
            sub_projects = await self._scrape_subreddit(subreddit)
            projects.extend(sub_projects)
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects

    async def _scrape_subreddit(self, subreddit: str) -> List[Dict]:
        data = await self.fetch(
            f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25",
            return_json=True
        )
        if not data or 'data' not in data or 'children' not in data['data']:
            return []
        projects = []
        for child in data['data']['children']:
            try:
                post = child['data']
                title = post.get('title', '')
                if not any(kw in title.lower() for kw in ['ai', 'startup', 'app', 'saas', 'tool', 'launch', 'build']):
                    continue
                url = post.get('url', '')
                selftext = post.get('selftext', '') or ''
                projects.append({
                    'name': title[:200],
                    'description': selftext[:500] or title,
                    'source_url': f"https://www.reddit.com{post.get('permalink', '')}",
                    'website': url,
                    'likes': post.get('score', 0),
                    'category': 'startups',
                    'author': post.get('author', ''),
                })
            except (ValueError, TypeError, KeyError):
                continue
        return projects


class AppSumoScraper(BaseScraper):
    """Scraper for AppSumo deals"""

    def __init__(self):
        super().__init__("AppSumo", "https://appsumo.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        html = await self.fetch("https://appsumo.com/products/")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        products = soup.find_all('div', class_='ProductCard') or soup.find_all('div', class_='product-item') or soup.find_all('a', href=re.compile(r'/products/'))
        for product in products[:25]:
            try:
                link = product if product.name == 'a' else product.find('a', href=re.compile(r'/products/'))
                if not link:
                    continue
                title_elem = product.find('h3') or product.find('h2') or product.find('span', class_='name')
                title = title_elem.get_text(strip=True) if title_elem else ''
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin('https://appsumo.com', url)
                price_elem = product.find('span', class_='price') or product.find('span', class_='sale-price')
                description = f"AppSumo deal: {title}"
                projects.append({
                    'name': title[:200],
                    'description': description[:500],
                    'source_url': url,
                    'website': url,
                    'category': 'ai_saas',
                })
            except (ValueError, TypeError, AttributeError):
                continue
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects


class BetaListScraper(BaseScraper):
    """Scraper for BetaList startups"""

    def __init__(self):
        super().__init__("BetaList", "https://betalist.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        html = await self.fetch("https://betalist.com/most-popular")
        if not html:
            html = await self.fetch("https://betalist.com/")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='startup-card') or soup.find_all('div', class_='media') or soup.find_all('a', href=re.compile(r'/startups/'))
        for item in items[:25]:
            try:
                link = item if item.name == 'a' and item.get('href') else item.find('a', href=re.compile(r'/startups/'))
                if not link:
                    continue
                title_elem = item.find('h3') or item.find('h2') or item.find('span', class_='name') or item.find('strong')
                title = title_elem.get_text(strip=True) if title_elem else ''
                desc_elem = item.find('p') or item.find('div', class_='description') or item.find('span', class_='tagline')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin('https://betalist.com', url)
                projects.append({
                    'name': title[:200],
                    'description': description[:500],
                    'source_url': url,
                    'website': url,
                    'category': 'startups',
                })
            except (ValueError, TypeError, AttributeError):
                continue
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects


class IndieHackersScraper(BaseScraper):
    """Scraper for IndieHackers products"""

    def __init__(self):
        super().__init__("IndieHackers", "https://www.indiehackers.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        html = await self.fetch("https://www.indiehackers.com/products?sorting=trending")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='product-card') or soup.find_all('div', class_='media') or soup.find_all('a', href=re.compile(r'/products/'))
        for item in items[:25]:
            try:
                link = item if item.name == 'a' and item.get('href') else item.find('a', href=re.compile(r'/products/'))
                if not link:
                    continue
                title_elem = item.find('h3') or item.find('h2') or item.find('div', class_='product-name')
                title = title_elem.get_text(strip=True) if title_elem else ''
                desc_elem = item.find('p') or item.find('div', class_='description') or item.find('div', class_='product-description')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin('https://www.indiehackers.com', url)
                revenue_elem = item.find('span', class_='revenue') or item.find('div', class_='monthly-revenue')
                projects.append({
                    'name': title[:200],
                    'description': description[:500],
                    'source_url': url,
                    'website': url,
                    'category': 'startups',
                    'author': title,
                })
            except (ValueError, TypeError, AttributeError):
                continue
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects


class ChromeWebStoreScraper(BaseScraper):
    """Scraper for Chrome Web Store AI extensions"""

    def __init__(self):
        super().__init__("Chrome Web Store", "https://chromewebstore.google.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        for query in ['AI', 'chatGPT', 'writing assistant', 'productivity']:
            results = await self._search(query)
            projects.extend(results)
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects

    async def _search(self, query: str) -> List[Dict]:
        html = await self.fetch(
            f"https://chromewebstore.google.com/search/{query}",
            headers={'Accept': 'text/html,application/xhtml+xml'}
        )
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        items = soup.find_all('div', class_='imtp') or soup.find_all('a', href=re.compile(r'/detail/'))
        for item in items[:15]:
            try:
                link = item if item.name == 'a' and '/detail/' in item.get('href', '') else item.find('a', href=re.compile(r'/detail/'))
                if not link:
                    continue
                title_elem = item.find('h3') or item.find('div', class_='CqaB0') or item.find('span', class_='vWM94')
                title = title_elem.get_text(strip=True) if title_elem else ''
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin('https://chromewebstore.google.com', url)
                rating_elem = item.find('span', class_='rkrly') or item.find('div', class_='VgN4cc')
                rating = None
                if rating_elem:
                    try:
                        rating = float(rating_elem.get('aria-label', '').replace(',', '.'))
                    except (ValueError, TypeError):
                        rating = None
                projects.append({
                    'name': title[:200],
                    'description': f"Chrome extension: {title}",
                    'source_url': url,
                    'website': url,
                    'rating': rating,
                    'category': 'chrome_extensions',
                })
            except (ValueError, TypeError, AttributeError):
                continue
        return projects


class GooglePlayScraper(BaseScraper):
    """Scraper for Google Play AI apps"""

    def __init__(self):
        super().__init__("Google Play", "https://play.google.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        html = await self.fetch("https://play.google.com/store/search?q=AI+app&c=apps")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='ImZGtf') or soup.find_all('a', href=re.compile(r'/store/apps/details'))
        for item in items[:25]:
            try:
                link = item if item.name == 'a' and '/store/apps/details' in item.get('href', '') else item.find('a', href=re.compile(r'/store/apps/details'))
                if not link:
                    continue
                title_elem = item.find('h3') or item.find('div', class_='WsMG1c') or item.find('span', class_='DdYX5')
                title = title_elem.get_text(strip=True) if title_elem else ''
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin('https://play.google.com', url)
                rating_elem = item.find('div', class_='TT9eCd') or item.find('span', class_='w2kbF')
                rating = None
                if rating_elem:
                    try:
                        rating = float(rating_elem.get('aria-label', '').split()[0])
                    except (ValueError, TypeError, IndexError):
                        rating = None
                projects.append({
                    'name': title[:200],
                    'description': f"Google Play AI app: {title}",
                    'source_url': url,
                    'website': url,
                    'rating': rating,
                    'category': 'mobile_apps',
                })
            except (ValueError, TypeError, AttributeError):
                continue
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects


class VentureBeatScraper(BaseScraper):
    """Scraper for VentureBeat AI articles via RSS"""

    def __init__(self):
        super().__init__("VentureBeat", "https://venturebeat.com")

    async def scrape(self) -> List[Dict]:
        projects = []
        rss_projects = await self._scrape_rss()
        if rss_projects:
            projects.extend(rss_projects)
        if not projects:
            web_projects = await self._scrape_web()
            projects.extend(web_projects)
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects

    async def _scrape_rss(self) -> List[Dict]:
        feed = await self.fetch("https://venturebeat.com/feed/")
        if not feed:
            return []
        projects = []
        parsed = feedparser.parse(feed)
        for entry in parsed.entries[:20]:
            title = entry.get('title', '')
            if not any(kw in title.lower() for kw in ['ai', 'startup', 'app', 'saas', 'launch', 'tech', 'robot', 'ml']):
                continue
            projects.append({
                'name': title[:200],
                'description': entry.get('summary', '')[:500] or title,
                'source_url': entry.get('link', ''),
                'website': entry.get('link', ''),
                'category': 'ai_saas',
                'author': entry.get('author', ''),
            })
        return projects

    async def _scrape_web(self) -> List[Dict]:
        html = await self.fetch("https://venturebeat.com/category/ai/")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        projects = []
        articles = soup.find_all('article') or soup.find_all('div', class_='ArticleListing')
        for article in articles[:20]:
            try:
                title_elem = article.find('h2') or article.find('h3') or article.find('a', class_='article-title')
                link_elem = article.find('a', href=True)
                desc_elem = article.find('p') or article.find('div', class_='excerpt')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                url = link_elem['href'] if link_elem else ''
                if url and not url.startswith('http'):
                    url = urljoin('https://venturebeat.com', url)
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                projects.append({
                    'name': title[:200],
                    'description': description[:500],
                    'source_url': url,
                    'website': url,
                    'category': 'ai_saas',
                })
            except (ValueError, TypeError, AttributeError):
                continue
        return projects


class YCombinatorLaunchesScraper(BaseScraper):
    """Scraper for Y Combinator launches"""

    def __init__(self):
        super().__init__("YC Launches", "https://www.ycombinator.com/launches")

    async def scrape(self) -> List[Dict]:
        projects = []
        html = await self.fetch("https://www.ycombinator.com/launches")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_='launch') or soup.find_all('div', class_='LaunchCard') or soup.find_all('a', href=re.compile(r'/launches/'))
        for item in items[:25]:
            try:
                link = item if item.name == 'a' and '/launches/' in item.get('href', '') else item.find('a', href=re.compile(r'/launches/'))
                if not link:
                    continue
                title_elem = item.find('h3') or item.find('h2') or item.find('div', class_='title') or item.find('strong')
                title = title_elem.get_text(strip=True) if title_elem else ''
                desc_elem = item.find('p') or item.find('div', class_='description')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                url = link.get('href', '')
                if url and not url.startswith('http'):
                    url = urljoin('https://www.ycombinator.com', url)
                tag_elem = item.find('span', class_='tag') or item.find('div', class_='industry')
                category = 'startups'
                if tag_elem:
                    tag_text = tag_elem.get_text(strip=True).lower()
                    if 'ai' in tag_text or 'ml' in tag_text:
                        category = 'ai_saas'
                projects.append({
                    'name': title[:200],
                    'description': description[:500],
                    'source_url': url,
                    'website': url,
                    'category': category,
                })
            except (ValueError, TypeError, AttributeError):
                continue
        normalized_projects = []
        for project in projects:
            normalized = self.normalize_data(project)
            dup_check = await self.check_duplicate(normalized)
            if not dup_check['is_duplicate']:
                normalized['fingerprint'] = dup_check['fingerprint']
                normalized_projects.append(normalized)
        return normalized_projects


class ScraperFactory:
    """Фабрика скрапперов"""
    
    SCRAPERS = {
        'Product Hunt': ProductHuntScraper,
        'GitHub Trending': GitHubTrendingScraper,
        'Hacker News': HackerNewsScraper,
        'Hugging Face': HuggingFaceScraper,
        'TikTok': TikTokScraper,
        'YouTube Shorts': YouTubeShortsScraper,
        'X (Twitter)': XScraper,
        'LinkedIn': LinkedInScraper,
        'TechCrunch': TechCrunchScraper,
        'Reddit': RedditScraper,
        'AppSumo': AppSumoScraper,
        'BetaList': BetaListScraper,
        'IndieHackers': IndieHackersScraper,
        'Chrome Web Store': ChromeWebStoreScraper,
        'Google Play': GooglePlayScraper,
        'VentureBeat': VentureBeatScraper,
        'YC Launches': YCombinatorLaunchesScraper,
    }
    
    @classmethod
    def get_scraper(cls, source_name: str) -> Optional[BaseScraper]:
        scraper_class = cls.SCRAPERS.get(source_name)
        if scraper_class:
            return scraper_class()
        return None
    
    @classmethod
    def list_scrapers(cls) -> List[str]:
        return list(cls.SCRAPERS.keys())