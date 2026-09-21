# Tasks package
from .scraping import scrape_source, analyze_unprocessed_projects, score_unscored_projects, detect_trend_explosions, detect_github_explosions
from .reports import generate_daily_report, send_daily_digest

__all__ = [
    'scrape_source', 'analyze_unprocessed_projects', 'score_unscored_projects',
    'detect_trend_explosions', 'detect_github_explosions',
    'generate_daily_report', 'send_daily_digest'
]