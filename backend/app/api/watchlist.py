from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Project, Watchlist
from app.api.utils import project_to_dict, parse_uuid

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.post("/{project_id}")
async def add_to_watchlist(project_id: str, db: AsyncSession = Depends(get_db)):
    project_uuid = parse_uuid(project_id)
    result = await db.execute(select(Project).where(Project.id == project_uuid))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    existing = await db.execute(select(Watchlist).where(Watchlist.project_id == project_uuid))
    if existing.scalar_one_or_none():
        return {"status": "already_exists", "project_id": project_id}
    watchlist_item = Watchlist(project_id=project_uuid)
    db.add(watchlist_item)
    await db.commit()
    return {"status": "added", "project_id": project_id}


@router.delete("/{project_id}")
async def remove_from_watchlist(project_id: str, db: AsyncSession = Depends(get_db)):
    project_uuid = parse_uuid(project_id)
    result = await db.execute(select(Watchlist).where(Watchlist.project_id == project_uuid))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    await db.delete(item)
    await db.commit()
    return {"status": "removed", "project_id": project_id}


@router.get("")
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Watchlist).join(Project))
    items = result.scalars().all()
    return {
        "items": [
            {"id": str(item.id), "project": project_to_dict(item.project),
             "notes": item.notes, "added_at": item.created_at.isoformat() if item.created_at else None}
            for item in items
        ]
    }
