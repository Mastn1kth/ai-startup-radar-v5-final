from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models import Project
from app.api.utils import project_to_dict

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_projects(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
    category: Optional[str] = None,
    sort_by: str = Query("coolness_score", enum=["coolness_score", "startup_score", "viral_score", "relevance"]),
    min_score: Optional[int] = None,
):
    query = select(Project).where(
        and_(
            or_(
                Project.name.ilike(f"%{q}%"),
                Project.description.ilike(f"%{q}%"),
                Project.category.ilike(f"%{q}%"),
                Project.author.ilike(f"%{q}%"),
                Project.github_language.ilike(f"%{q}%"),
            ),
            Project.status == 'active'
        )
    )
    if category:
        query = query.where(Project.category == category)
    if min_score and sort_by != "relevance":
        score_col = getattr(Project, sort_by, Project.coolness_score)
        query = query.where(score_col >= min_score)
    if sort_by == "relevance":
        relevance = case(
            (Project.name.ilike(f"{q}"), 100),
            (Project.name.ilike(f"%{q}%"), 80),
            (Project.description.ilike(f"%{q}%"), 60),
            (Project.category.ilike(f"%{q}%"), 40),
            (Project.author.ilike(f"%{q}%"), 30),
            (Project.github_language.ilike(f"%{q}%"), 20),
            else_=10
        )
        query = query.order_by(relevance.desc(), desc(Project.coolness_score))
    else:
        score_col = getattr(Project, sort_by, Project.coolness_score)
        query = query.order_by(desc(score_col))
    result = await db.execute(query.limit(limit))
    projects = result.scalars().all()
    return {"query": q, "results": [project_to_dict(p) for p in projects], "total": len(projects), "sort_by": sort_by}
