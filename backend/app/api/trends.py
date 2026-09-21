from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models import Trend
from app.api.utils import trend_to_dict

router = APIRouter(prefix="/api/trends", tags=["trends"])


@router.get("")
async def get_trends(
    db: AsyncSession = Depends(get_db),
    is_exploding: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = select(Trend)
    if is_exploding is not None:
        query = query.where(Trend.is_exploding == is_exploding)
    query = query.order_by(desc(Trend.growth_percent)).limit(limit).offset(offset)
    result = await db.execute(query)
    trends = result.scalars().all()
    return {"items": [trend_to_dict(t) for t in trends], "total": len(trends)}


@router.get("/exploding")
async def get_exploding_trends(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50)
):
    result = await db.execute(
        select(Trend).where(Trend.is_exploding == True)
        .order_by(desc(Trend.growth_percent)).limit(limit)
    )
    trends = result.scalars().all()
    return {"items": [trend_to_dict(t) for t in trends], "total": len(trends)}
