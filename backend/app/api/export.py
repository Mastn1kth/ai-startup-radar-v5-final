import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Project

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
async def export_csv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project).where(Project.status == 'active').order_by(desc(Project.startup_score))
    )
    projects = result.scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Category', 'Description', 'Website', 'GitHub URL',
                     'Startup Score', 'Russia Score', 'Copy Score', 'Money Score', 'Viral Score',
                     'Gap Status', 'Likes', 'GitHub Stars', 'Discovered At'])
    for project in projects:
        writer.writerow([
            str(project.id), project.name, project.category, (project.description or '')[:200],
            project.website or '', project.github_url or '', project.startup_score,
            project.russia_opportunity_score, project.copy_score, project.money_score,
            project.viral_score, project.gap_status, project.likes, project.github_stars,
            project.discovered_at.isoformat() if project.discovered_at else ''
        ])
    return {
        "content": output.getvalue(),
        "filename": f"projects_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
        "count": len(projects)
    }
