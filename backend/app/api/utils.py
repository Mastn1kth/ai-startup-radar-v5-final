from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.models import Project, Trend
from app.services.scoring import scoring_service


def project_to_dict(project: Project, detailed: bool = False) -> dict:
    base = {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "category": project.category,
        "website": project.website,
        "github_url": project.github_url,
        "github_stars": project.github_stars,
        "github_forks": project.github_forks,
        "likes": project.likes,
        "startup_score": project.startup_score,
        "russia_opportunity_score": project.russia_opportunity_score,
        "copy_score": project.copy_score,
        "money_score": project.money_score,
        "viral_score": project.viral_score,
        "coolness_score": project.coolness_score,
        "market_saturation_score": project.market_saturation_score,
        "rotation_priority": project.rotation_priority,
        "is_rotated": project.is_rotated,
        "gap_status": project.gap_status,
        "status": project.status,
        "discovered_at": project.discovered_at.isoformat() if project.discovered_at else None,
    }
    if detailed:
        base.update({
            "ai_summary": project.ai_summary,
            "problem_solved": project.problem_solved,
            "target_audience": project.target_audience,
            "monetization_type": project.monetization_type,
            "has_subscription": project.has_subscription,
            "has_freemium": project.has_freemium,
            "growth_potential": project.growth_potential,
            "viral_potential": project.viral_potential,
            "money_potential": project.money_potential,
            "failure_probability": project.failure_probability,
            "competition_level": project.competition_level,
            "market_size": project.market_size,
            "implementation_complexity": project.implementation_complexity,
            "solo_founder_possible": project.solo_founder_possible,
            "small_team_possible": project.small_team_possible,
            "mvp_timeline": project.mvp_timeline,
            "profit_timeline": project.profit_timeline,
            "scaling_potential": project.scaling_potential,
            "has_russia_analog": project.has_russia_analog,
            "has_cis_analog": project.has_cis_analog,
            "can_localize": project.can_localize,
            "can_quick_launch": project.can_quick_launch,
            "legal_restrictions": project.legal_restrictions,
            "estimated_budget": scoring_service.estimate_budget(project),
            "estimated_timeline": scoring_service.estimate_timeline(project),
            "success_probability": scoring_service.calculate_success_probability(project),
            "founder_history_score": project.founder_history_score,
            "rotated_at": project.rotated_at.isoformat() if project.rotated_at else None,
        })
    return base


def trend_to_dict(trend: Trend) -> dict:
    return {
        "id": str(trend.id),
        "name": trend.name,
        "category": trend.category,
        "description": trend.description,
        "growth_percent": float(trend.growth_percent) if trend.growth_percent else 0,
        "is_exploding": trend.is_exploding,
        "explosion_detected_at": trend.explosion_detected_at.isoformat() if trend.explosion_detected_at else None,
        "created_at": trend.created_at.isoformat() if trend.created_at else None,
    }


def parse_uuid(project_id: str) -> UUID:
    try:
        return UUID(project_id)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid project ID format")
