from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from datetime import datetime

from app.core.database import get_db
from app.models import Project, Source, AppSetting, get_app_setting, set_app_setting

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Получить все настройки приложения"""
    result = await db.execute(select(AppSetting))
    settings = result.scalars().all()

    items = []
    for s in settings:
        items.append({
            "key": s.key,
            "value": s.value,
        })

    return {"settings": items}


@router.put("/settings")
async def update_setting(
    setting_data: Dict[str, str],
    db: AsyncSession = Depends(get_db),
):
    """Обновить настройку"""
    key = setting_data.get("key")
    value = setting_data.get("value")

    if not key or value is None:
        raise HTTPException(status_code=400, detail="key and value are required")

    descriptions = {
        "ai_analysis_enabled": "Включить/выключить AI анализ проектов (через TG: /toggle_ai)",
        "scoring_interval_minutes": "Интервал пересчета скоров (минуты)",
        "max_projects_per_source": "Максимум проектов на один источник",
    }

    await set_app_setting(db, key, str(value), descriptions.get(key, ""))
    return {"status": "ok", "key": key, "value": str(value)}


@router.get("/stats")
async def get_admin_stats(db: AsyncSession = Depends(get_db)):
    """Детальная статистика системы"""
    total = await db.execute(select(func.count(Project.id)))
    active = await db.execute(
        select(func.count(Project.id)).where(Project.status == 'active')
    )
    analyzed = await db.execute(
        select(func.count(Project.id)).where(Project.ai_summary.isnot(None))
    )
    scored = await db.execute(
        select(func.count(Project.id)).where(Project.startup_score.isnot(None))
    )
    sources = await db.execute(select(Source))
    source_list = sources.scalars().all()
    ai_enabled = await get_app_setting(db, "ai_analysis_enabled", "true")

    return {
        "total_projects": total.scalar(),
        "active_projects": active.scalar(),
        "analyzed_by_ai": analyzed.scalar(),
        "scored": scored.scalar(),
        "sources_count": len(source_list),
        "active_sources": sum(1 for s in source_list if s.is_active),
        "ai_analysis_enabled": ai_enabled == "true",
        "last_updated": datetime.utcnow().isoformat(),
    }
