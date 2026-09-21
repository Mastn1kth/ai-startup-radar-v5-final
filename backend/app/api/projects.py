from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.models import Project
from app.api.utils import project_to_dict, parse_uuid

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("")
async def get_projects(
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    gap_status: Optional[str] = None,
    min_score: Optional[int] = None,
    min_russia_score: Optional[int] = None,
    status: str = "active",
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = "startup_score",
    order: str = "desc"
):
    query = select(Project).where(Project.status == status)
    if category:
        query = query.where(Project.category == category)
    if gap_status:
        query = query.where(Project.gap_status == gap_status)
    if min_score:
        query = query.where(Project.startup_score >= min_score)
    if min_russia_score:
        query = query.where(Project.russia_opportunity_score >= min_russia_score)
    sort_column = getattr(Project, sort_by, Project.coolness_score)
    if order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    projects = result.scalars().all()
    return {
        "items": [project_to_dict(p) for p in projects],
        "total": len(projects),
        "limit": limit,
        "offset": offset
    }


@router.get("/featured")
async def get_featured_projects(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50)
):
    result = await db.execute(
        select(Project).where(
            and_(Project.startup_score >= 70, Project.status == 'active')
        ).order_by(desc(Project.startup_score)).limit(limit)
    )
    projects = result.scalars().all()
    return {"items": [project_to_dict(p) for p in projects], "total": len(projects)}


@router.get("/russia-opportunities")
async def get_russia_opportunities(
    db: AsyncSession = Depends(get_db),
    min_score: int = Query(60, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100)
):
    result = await db.execute(
        select(Project).where(
            and_(
                Project.russia_opportunity_score >= min_score,
                Project.gap_status.in_(['green', 'yellow']),
                Project.status == 'active'
            )
        ).order_by(desc(Project.russia_opportunity_score)).limit(limit)
    )
    projects = result.scalars().all()
    return {"items": [project_to_dict(p) for p in projects], "total": len(projects)}


@router.get("/compare")
async def compare_projects(
    project_ids: str = Query(..., description="Comma-separated project IDs"),
    db: AsyncSession = Depends(get_db)
):
    try:
        ids = [UUID(pid.strip()) for pid in project_ids.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project IDs format")
    result = await db.execute(select(Project).where(Project.id.in_(ids)))
    projects = result.scalars().all()
    if len(projects) != len(ids):
        raise HTTPException(status_code=404, detail="Some projects not found")
    comparison = {}
    if len(projects) >= 2:
        comparison = {
            "best_startup_score": max(projects, key=lambda p: p.startup_score or 0).name,
            "best_russia_score": max(projects, key=lambda p: p.russia_opportunity_score or 0).name,
            "best_money_score": max(projects, key=lambda p: p.money_score or 0).name,
            "easiest_to_copy": min(projects, key=lambda p: p.implementation_complexity or 100).name,
            "highest_viral": max(projects, key=lambda p: p.viral_score or 0).name,
            "coolest": max(projects, key=lambda p: p.coolness_score or 0).name,
        }
    return {"projects": [project_to_dict(p, detailed=True) for p in projects], "comparison": comparison}


@router.get("/ranked")
async def get_ranked_projects(
    db: AsyncSession = Depends(get_db),
    sort_by: str = Query("coolness_score", enum=["coolness_score", "startup_score", "viral_score", "money_score", "russia_opportunity_score", "copy_score", "rotation_priority"]),
    min_score: Optional[int] = None,
    category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = select(Project).where(Project.status == 'active')
    if category:
        query = query.where(Project.category == category)
    if min_score:
        sort_column = getattr(Project, sort_by, Project.coolness_score)
        query = query.where(sort_column >= min_score)
    sort_column = getattr(Project, sort_by, Project.coolness_score)
    query = query.order_by(desc(sort_column)).limit(limit).offset(offset)
    result = await db.execute(query)
    projects = result.scalars().all()
    ranked_items = []
    for idx, project in enumerate(projects):
        item = project_to_dict(project)
        item["rank"] = offset + idx + 1
        item["ranked_by"] = sort_by
        ranked_items.append(item)
    return {"items": ranked_items, "total": len(projects), "sort_by": sort_by, "limit": limit, "offset": offset}


@router.get("/rotation-queue")
async def get_rotation_queue(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    result = await db.execute(
        select(Project).where(
            and_(Project.status == 'active', Project.is_rotated == False)
        ).order_by(desc(Project.rotation_priority)).limit(limit)
    )
    projects = result.scalars().all()
    return {"items": [project_to_dict(p) for p in projects], "total": len(projects)}


@router.post("/rotate")
async def rotate_projects(
    db: AsyncSession = Depends(get_db),
    max_projects: int = Query(1000, ge=100, le=10000),
    dry_run: bool = Query(False)
):
    from app.services.scoring import ScoringService
    from app.models import RotationLog
    result = await db.execute(select(Project).where(Project.status == 'active'))
    all_projects = result.scalars().all()
    if len(all_projects) <= max_projects:
        return {"message": f"Projects ({len(all_projects)}) below limit ({max_projects}). No rotation needed.", "total_projects": len(all_projects), "max_projects": max_projects, "rotated": 0}
    projects_to_keep, projects_to_rotate = ScoringService.auto_rotate_projects(list(all_projects), max_projects)
    rotated_count = 0
    if not dry_run:
        for project in projects_to_rotate:
            project.is_rotated = True
            project.rotated_at = datetime.utcnow()
            project.status = 'rotated'
            rotation_log = RotationLog(
                project_id=project.id, rotation_reason='limit_reached',
                rotation_priority=project.rotation_priority or 50,
                coolness_score_before=project.coolness_score, startup_score_before=project.startup_score
            )
            db.add(rotation_log)
            rotated_count += 1
        await db.commit()
    return {
        "message": f"Rotated {len(projects_to_rotate)} projects" if not dry_run else f"Would rotate {len(projects_to_rotate)} (dry run)",
        "total_projects": len(all_projects), "max_projects": max_projects,
        "rotated": rotated_count, "kept": len(projects_to_keep), "dry_run": dry_run,
        "rotated_projects": [{"id": str(p.id), "name": p.name, "coolness_score": p.coolness_score, "rotation_priority": p.rotation_priority} for p in projects_to_rotate[:10]]
    }


@router.get("/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project_uuid = parse_uuid(project_id)
    result = await db.execute(select(Project).where(Project.id == project_uuid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_dict(project, detailed=True)
