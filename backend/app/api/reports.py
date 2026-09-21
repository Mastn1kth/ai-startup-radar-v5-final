from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import DailyReport

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/daily")
async def get_daily_reports(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(7, ge=1, le=30)
):
    result = await db.execute(
        select(DailyReport)
        .order_by(desc(DailyReport.report_date))
        .limit(limit)
    )
    reports = result.scalars().all()
    return {
        "reports": [
            {
                "date": r.report_date.isoformat() if r.report_date else None,
                "top_projects": r.top_projects[:5] if r.top_projects else [],
                "sent_to_telegram": r.sent_to_telegram
            }
            for r in reports
        ]
    }
