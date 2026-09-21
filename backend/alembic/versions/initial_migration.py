"""initial

Revision ID: 001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("telegram_notifications", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("email_notifications", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("min_startup_score_alert", sa.Integer(), server_default=sa.text("70")),
        sa.Column("min_russia_score_alert", sa.Integer(), server_default=sa.text("60")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(500)),
        sa.Column("category", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("scrape_interval_minutes", sa.Integer(), server_default=sa.text("120")),
        sa.Column("last_scraped_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_sources_name", "sources", ["name"])

    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100)),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id")),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("website", sa.String(500)),
        sa.Column("author", sa.String(255)),
        sa.Column("author_url", sa.String(500)),
        sa.Column("rating", sa.DECIMAL(3, 2)),
        sa.Column("likes", sa.Integer(), server_default=sa.text("0")),
        sa.Column("reviews_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("downloads", sa.Integer(), server_default=sa.text("0")),
        sa.Column("users_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("github_url", sa.String(500)),
        sa.Column("github_stars", sa.Integer(), server_default=sa.text("0")),
        sa.Column("github_forks", sa.Integer(), server_default=sa.text("0")),
        sa.Column("github_language", sa.String(100)),
        sa.Column("investment_amount", sa.DECIMAL(15, 2)),
        sa.Column("investment_stage", sa.String(50)),
        sa.Column("investors", sa.Text()),
        sa.Column("discovered_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("last_updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ai_summary", sa.Text()),
        sa.Column("problem_solved", sa.Text()),
        sa.Column("target_audience", sa.Text()),
        sa.Column("monetization_type", sa.String(100)),
        sa.Column("has_subscription", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("has_freemium", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("growth_potential", sa.Integer()),
        sa.Column("viral_potential", sa.Integer()),
        sa.Column("money_potential", sa.Integer()),
        sa.Column("failure_probability", sa.Integer()),
        sa.Column("competition_level", sa.Integer()),
        sa.Column("market_size", sa.String(255)),
        sa.Column("implementation_complexity", sa.Integer()),
        sa.Column("required_team", sa.String(255)),
        sa.Column("required_investment", sa.String(255)),
        sa.Column("solo_founder_possible", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("small_team_possible", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("mvp_timeline", sa.String(100)),
        sa.Column("profit_timeline", sa.String(100)),
        sa.Column("scaling_potential", sa.Integer()),
        sa.Column("copy_score", sa.Integer()),
        sa.Column("money_score", sa.Integer()),
        sa.Column("viral_score", sa.Integer()),
        sa.Column("startup_score", sa.Integer()),
        sa.Column("russia_opportunity_score", sa.Integer()),
        sa.Column("coolness_score", sa.Integer()),
        sa.Column("market_saturation_score", sa.Integer()),
        sa.Column("rotation_priority", sa.Integer(), server_default=sa.text("50")),
        sa.Column("is_rotated", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("rotated_at", sa.DateTime()),
        sa.Column("has_russia_analog", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("has_cis_analog", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("has_strong_competitor", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("has_weak_competitor", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("can_localize", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("can_quick_launch", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("legal_restrictions", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("gap_status", sa.String(20), server_default=sa.text("'unknown'")),
        sa.Column("founder_history_score", sa.Integer(), server_default=sa.text("0")),
        sa.Column("status", sa.String(50), server_default=sa.text("'active'")),
        sa.Column("is_duplicate", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("similarity_score", sa.DECIMAL(5, 4)),
        sa.Column("qdrant_vector_id", sa.String(100)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_projects_slug", "projects", ["slug"])
    op.create_index("idx_projects_category", "projects", ["category"])
    op.create_index("idx_projects_status", "projects", ["status"])
    op.create_index("idx_projects_startup_score", "projects", [sa.text("startup_score DESC")])
    op.create_index("idx_projects_russia_score", "projects", [sa.text("russia_opportunity_score DESC")])
    op.create_index("idx_projects_gap_status", "projects", ["gap_status"])
    op.create_index("idx_projects_discovered_at", "projects", [sa.text("discovered_at DESC")])
    op.create_index("idx_projects_name_trgm", "projects", [sa.text("name gin_trgm_ops")], postgresql_using="gin")

    op.create_table(
        "trends",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("source", sa.String(100)),
        sa.Column("initial_mentions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("current_mentions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("growth_percent", sa.DECIMAL(10, 2)),
        sa.Column("google_trends_score", sa.Integer()),
        sa.Column("reddit_mentions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("twitter_mentions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("youtube_mentions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("is_exploding", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("explosion_detected_at", sa.DateTime()),
        sa.Column("related_projects_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_trends_growth", "trends", [sa.text("growth_percent DESC")])
    op.create_index("idx_trends_is_exploding", "trends", ["is_exploding"])

    op.create_table(
        "project_trends",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("trend_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trends.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relevance_score", sa.DECIMAL(5, 4)),
    )

    op.create_table(
        "investments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("amount", sa.DECIMAL(15, 2)),
        sa.Column("currency", sa.String(10), server_default=sa.text("'USD'")),
        sa.Column("stage", sa.String(50)),
        sa.Column("investors", sa.Text()),
        sa.Column("investment_date", sa.DateTime()),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_investments_stage", "investments", ["stage"])

    op.create_table(
        "watchlist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("notes", sa.Text()),
        sa.Column("alerts_enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("score_change_threshold", sa.Integer(), server_default=sa.text("5")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_watchlist_project", "watchlist", ["project_id"])

    op.create_table(
        "score_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("startup_score", sa.Integer()),
        sa.Column("russia_opportunity_score", sa.Integer()),
        sa.Column("copy_score", sa.Integer()),
        sa.Column("money_score", sa.Integer()),
        sa.Column("viral_score", sa.Integer()),
        sa.Column("recorded_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_score_history_project", "score_history", ["project_id", "recorded_at"])

    op.create_table(
        "daily_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_date", sa.DateTime(), unique=True),
        sa.Column("top_projects", postgresql.JSONB()),
        sa.Column("top_ai_saas", postgresql.JSONB()),
        sa.Column("top_mobile_apps", postgresql.JSONB()),
        sa.Column("top_telegram_bots", postgresql.JSONB()),
        sa.Column("top_chrome_extensions", postgresql.JSONB()),
        sa.Column("top_ai_agents", postgresql.JSONB()),
        sa.Column("top_mcp_tools", postgresql.JSONB()),
        sa.Column("top_github_projects", postgresql.JSONB()),
        sa.Column("top_investments", postgresql.JSONB()),
        sa.Column("top_trends", postgresql.JSONB()),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("sent_to_telegram", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("sent_to_email", sa.Boolean(), server_default=sa.text("false")),
    )

    op.create_table(
        "telegram_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("message_id", sa.BigInteger()),
        sa.Column("channel_id", sa.String(100)),
        sa.Column("content", sa.Text()),
        sa.Column("posted_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("engagement_score", sa.Integer(), server_default=sa.text("0")),
    )

    op.create_table(
        "email_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("alert_type", sa.String(50)),
        sa.Column("subject", sa.String(500)),
        sa.Column("content", sa.Text()),
        sa.Column("sent_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("opened_at", sa.DateTime()),
    )

    op.create_table(
        "scrape_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id")),
        sa.Column("status", sa.String(50)),
        sa.Column("items_found", sa.Integer(), server_default=sa.text("0")),
        sa.Column("items_new", sa.Integer(), server_default=sa.text("0")),
        sa.Column("items_updated", sa.Integer(), server_default=sa.text("0")),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime()),
        sa.Column("finished_at", sa.DateTime()),
        sa.Column("duration_seconds", sa.Integer()),
    )

    op.create_table(
        "rotation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("rotation_reason", sa.String(255)),
        sa.Column("rotation_priority", sa.Integer(), server_default=sa.text("50")),
        sa.Column("coolness_score_before", sa.Integer()),
        sa.Column("startup_score_before", sa.Integer()),
        sa.Column("replaced_by_project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id")),
        sa.Column("rotated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "bot_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("channel_id", sa.String(100), nullable=False),
        sa.Column("channel_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("digest_interval_minutes", sa.Integer(), server_default=sa.text("30")),
        sa.Column("projects_per_digest", sa.Integer(), server_default=sa.text("10")),
        sa.Column("max_projects_per_day", sa.Integer(), server_default=sa.text("100")),
        sa.Column("min_coolness_score", sa.Integer(), server_default=sa.text("50")),
        sa.Column("min_startup_score", sa.Integer(), server_default=sa.text("60")),
        sa.Column("min_russia_score", sa.Integer(), server_default=sa.text("0")),
        sa.Column("allowed_categories", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("excluded_categories", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb")),
        sa.Column("send_digest", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("send_detailed_review", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("send_individual_alerts", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("send_rotation_updates", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("active_hours_start", sa.Integer(), server_default=sa.text("0")),
        sa.Column("active_hours_end", sa.Integer(), server_default=sa.text("23")),
        sa.Column("timezone", sa.String(50), server_default=sa.text("'Europe/Moscow'")),
        sa.Column("include_ai_summary", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("include_revenue_prediction", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("include_russia_launch", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("include_opportunity_ideas", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("cooldown_minutes", sa.Integer(), server_default=sa.text("5")),
        sa.Column("last_sent_at", sa.DateTime()),
        sa.Column("messages_sent_today", sa.Integer(), server_default=sa.text("0")),
        sa.Column("reset_counter_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_bot_settings_channel", "bot_settings", ["channel_id"])

    op.create_table(
        "app_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("description", sa.Text()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_app_settings_key", "app_settings", ["key"], unique=True)

    op.execute("""
        INSERT INTO sources (name, url, category, scrape_interval_minutes) VALUES
        ('Product Hunt', 'https://www.producthunt.com', 'ai_saas', 120),
        ('GitHub Trending', 'https://github.com/trending', 'open_source', 120),
        ('Hacker News', 'https://news.ycombinator.com', 'startups', 60),
        ('Hugging Face', 'https://huggingface.co/models', 'ai_models', 240),
        ('BetaList', 'https://betalist.com', 'ai_saas', 240),
        ('Indie Hackers', 'https://www.indiehackers.com', 'startups', 240),
        ('YC Launches', 'https://www.ycombinator.com/launches', 'startups', 480),
        ('TechCrunch', 'https://techcrunch.com', 'startups', 120),
        ('Reddit r/startup', 'https://www.reddit.com/r/startups', 'startups', 120),
        ('Reddit r/SaaS', 'https://www.reddit.com/r/SaaS', 'ai_saas', 120),
        ('Chrome Web Store', 'https://chrome.google.com/webstore', 'chrome_extensions', 240),
        ('Exploding Topics', 'https://explodingtopics.com', 'trends', 480)
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("bot_settings")
    op.drop_table("rotation_logs")
    op.drop_table("scrape_logs")
    op.drop_table("email_alerts")
    op.drop_table("telegram_posts")
    op.drop_table("daily_reports")
    op.drop_table("score_history")
    op.drop_table("watchlist")
    op.drop_table("investments")
    op.drop_table("project_trends")
    op.drop_table("trends")
    op.drop_table("projects")
    op.drop_table("sources")
    op.drop_table("users")
