from fastapi import APIRouter, Depends
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models import Project, Trend

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    total_projects = await db.execute(select(func.count(Project.id)).where(Project.status == 'active'))
    total = total_projects.scalar()
    categories = await db.execute(
        select(Project.category, func.count(Project.id))
        .where(Project.status == 'active').group_by(Project.category)
        .order_by(desc(func.count(Project.id)))
    )
    high_potential = await db.execute(
        select(func.count(Project.id)).where(and_(Project.coolness_score >= 80, Project.status == 'active'))
    )
    russia_opp = await db.execute(
        select(func.count(Project.id)).where(and_(Project.russia_opportunity_score >= 70, Project.gap_status == 'green', Project.status == 'active'))
    )
    new_24h = await db.execute(
        select(func.count(Project.id)).where(Project.discovered_at >= datetime.utcnow() - timedelta(hours=24))
    )
    exploding = await db.execute(select(func.count(Trend.id)).where(Trend.is_exploding == True))
    top_coolness = await db.execute(
        select(func.count(Project.id)).where(and_(Project.coolness_score >= 90, Project.status == 'active'))
    )
    rotated = await db.execute(select(func.count(Project.id)).where(Project.is_rotated == True))
    return {
        "total_projects": total,
        "categories": {cat: count for cat, count in categories.all()},
        "high_potential": high_potential.scalar(),
        "russia_opportunities": russia_opp.scalar(),
        "new_24h": new_24h.scalar(),
        "exploding_trends": exploding.scalar(),
        "top_coolness": top_coolness.scalar(),
        "rotated_projects": rotated.scalar(),
        "last_updated": datetime.utcnow().isoformat()
    }


@router.get("/top-categories")
async def get_top_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project.category, func.count(Project.id))
        .where(Project.status == 'active').group_by(Project.category)
        .order_by(desc(func.count(Project.id))).limit(10)
    )
    return {"categories": [{"name": cat, "count": count} for cat, count in result.all()]}


@router.get("/score-distribution")
async def get_score_distribution(db: AsyncSession = Depends(get_db)):
    ranges = [(0, 20, "0-20"), (20, 40, "20-40"), (40, 60, "40-60"), (60, 80, "60-80"), (80, 100, "80-100")]
    distribution = []
    for min_val, max_val, label in ranges:
        count = await db.execute(
            select(func.count(Project.id)).where(and_(Project.coolness_score >= min_val, Project.coolness_score < max_val, Project.status == 'active'))
        )
        distribution.append({"range": label, "count": count.scalar()})
    return {"distribution": distribution, "metric": "coolness_score"}
