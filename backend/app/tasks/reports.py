import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models import Project, DailyReport, ScoreHistory, Trend
from app.services.scoring import scoring_service
from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.ai_analyzer import ollama_client
from app.api.utils import project_to_dict as _project_to_dict

logger = logging.getLogger(__name__)


@celery_app.task
def generate_trend_products():
    """Trend-to-Product: генерация продуктовых идей из взрывных трендов"""
    asyncio.run(_generate_trend_products_async())


async def _check_ai_enabled(session) -> bool:
    from app.models import get_app_setting
    ai_enabled = await get_app_setting(session, "ai_analysis_enabled", "true")
    return ai_enabled == "true"


async def _generate_trend_products_async():
    """Автоматическая генерация продуктов из трендов"""
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Trend).where(
                and_(
                    Trend.is_exploding == True,
                    Trend.description.notlike('%🚀 Trend-to-Product%')  # Avoid re-processing
                )
            ).limit(5)
        )
        trends = result.scalars().all()
        
        for trend in trends:
            try:
                products = await ollama_client.trend_to_product(
                    trend_name=trend.name,
                    trend_description=trend.description or "",
                    trend_growth=float(trend.growth_percent) if trend.growth_percent else 100
                )
                
                product_text = "\n\n🚀 Trend-to-Product - Продукты из тренда:\n\n"
                for i, product in enumerate(products.get('products', [])[:5], 1):
                    product_text += f"Продукт #{i}: {product.get('name', 'Unknown')}\n"
                    product_text += f"  Тип: {product.get('type', 'Unknown')}\n"
                    product_text += f"  Описание: {product.get('description', '')}\n"
                    product_text += f"  ЦА: {product.get('target_audience', '')}\n"
                    product_text += f"  Монетизация: {product.get('monetization', '')}\n"
                    product_text += f"  MVP: {product.get('mvp_weeks', '?')} недель\n"
                    product_text += f"  Почему сейчас: {product.get('why_now', '')}\n"
                    product_text += f"  Вероятность успеха: {product.get('success_probability', '?')}%\n\n"
                
                product_text += f"Окно возможности: {products.get('trend_window', 'Unknown')}\n"
                product_text += f"Оценка рынка: {products.get('market_size_estimate', 'Unknown')}\n"
                
                trend.description = (trend.description or "") + product_text
                
                await session.commit()
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task
def generate_daily_report():
    """Генерация ежедневного отчета"""
    asyncio.run(_generate_daily_report_async())


async def _generate_daily_report_async():
    """Асинхронная генерация ежедневного отчета"""
    async with AsyncSessionLocal() as session:
        today = datetime.utcnow().date()
        
        existing = await session.execute(
            select(DailyReport).where(DailyReport.report_date == today)
        )
        if existing.scalar_one_or_none():
            return
        
        top_projects = await _get_top_projects(session, limit=10)
        top_ai_saas = await _get_top_by_category(session, 'ai_saas', 10)
        top_mobile = await _get_top_by_category(session, 'mobile_apps', 10)
        top_telegram = await _get_top_by_category(session, 'telegram', 10)
        top_chrome = await _get_top_by_category(session, 'chrome_extensions', 10)
        top_ai_agents = await _get_top_by_category(session, 'ai_agents', 10)
        top_mcp = await _get_top_by_category(session, 'mcp', 10)
        top_github = await _get_top_by_category(session, 'open_source', 10)
        top_investments = await _get_top_investments(session, 10)
        top_trends = await _get_top_trends(session, 10)
        
        # Добавляем market saturation к отчету
        market_saturation = await _get_market_saturation_report(session)
        
        report = DailyReport(
            report_date=today,
            top_projects=top_projects,
            top_ai_saas=top_ai_saas,
            top_mobile_apps=top_mobile,
            top_telegram_bots=top_telegram,
            top_chrome_extensions=top_chrome,
            top_ai_agents=top_ai_agents,
            top_mcp_tools=top_mcp,
            top_github_projects=top_github,
            top_investments=top_investments,
            top_trends=top_trends,
        )
        
        session.add(report)
        await session.commit()


async def _get_top_projects(session: AsyncSession, limit: int = 10) -> List[Dict]:
    """Получение топ проектов"""
    result = await session.execute(
        select(Project).where(
            and_(
                Project.startup_score.isnot(None),
                Project.status == 'active'
            )
        ).order_by(desc(Project.startup_score)).limit(limit)
    )
    projects = result.scalars().all()
    
    return [_project_to_dict(p) for p in projects]


async def _get_top_by_category(session: AsyncSession, category: str, limit: int = 10) -> List[Dict]:
    """Получение топ проектов по категории"""
    result = await session.execute(
        select(Project).where(
            and_(
                Project.category == category,
                Project.startup_score.isnot(None),
                Project.status == 'active'
            )
        ).order_by(desc(Project.startup_score)).limit(limit)
    )
    projects = result.scalars().all()
    
    return [_project_to_dict(p) for p in projects]


async def _get_top_investments(session: AsyncSession, limit: int = 10) -> List[Dict]:
    """Получение топ инвестиций"""
    from app.models import Investment
    
    result = await session.execute(
        select(Project, Investment).join(Investment).where(
            Investment.amount.isnot(None)
        ).order_by(desc(Investment.amount)).limit(limit)
    )
    
    investments = []
    for project, investment in result.all():
        investments.append({
            'project_name': project.name,
            'amount': float(investment.amount) if investment.amount else 0,
            'stage': investment.stage,
            'investors': investment.investors,
            'date': investment.investment_date.isoformat() if investment.investment_date else None,
        })
    
    return investments


async def _get_top_trends(session: AsyncSession, limit: int = 10) -> List[Dict]:
    """Получение топ трендов"""
    result = await session.execute(
        select(Trend).where(
            Trend.growth_percent.isnot(None)
        ).order_by(desc(Trend.growth_percent)).limit(limit)
    )
    trends = result.scalars().all()
    
    return [{
        'name': t.name,
        'category': t.category,
        'growth_percent': float(t.growth_percent) if t.growth_percent else 0,
        'is_exploding': t.is_exploding,
    } for t in trends]


async def _get_market_saturation_report(session: AsyncSession) -> List[Dict]:
    """Получение отчета о насыщенности рынков"""
    result = await session.execute(
        select(Project).where(
            and_(
                Project.startup_score.isnot(None),
                Project.status == 'active'
            )
        ).order_by(desc(Project.startup_score)).limit(50)
    )
    projects = result.scalars().all()
    
    saturation_report = []
    for project in projects:
        saturation_score = scoring_service.calculate_market_saturation_score(project)
        saturation_report.append({
            'name': project.name,
            'category': project.category,
            'saturation_score': saturation_score,
            'status': 'overheated' if saturation_score > 80 else 'saturated' if saturation_score > 60 else 'moderate' if saturation_score > 40 else 'open'
        })
    
    return saturation_report


@celery_app.task
def send_coolness_digest():
    """Отправка дайджеста топ проектов по Coolness Score в Telegram"""
    asyncio.run(_send_coolness_digest_async())


async def _send_coolness_digest_async():
    """Асинхронная отправка дайджеста по крутости - ВСЕ проекты каждые 30 минут с учетом настроек бота"""
    from app.services.telegram_bot import telegram_bot
    from app.models import BotSettings
    
    async with AsyncSessionLocal() as session:
        # Получаем настройки бота из БД
        result = await session.execute(
            select(BotSettings).where(BotSettings.is_active == True)
        )
        bot_settings_list = result.scalars().all()
        
        # Если настроек нет - используем дефолтные
        if not bot_settings_list:
            bot_settings_list = [None]  # Будет использоваться канал по умолчанию
        
        # Получаем ВСЕ активные проекты отсортированные по coolness_score
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.coolness_score.isnot(None),
                    Project.status == 'active',
                    Project.is_rotated == False
                )
            ).order_by(desc(Project.coolness_score))
        )
        projects = result.scalars().all()
        
        if not projects:
            return
        
        # Конвертируем в dict для Telegram бота
        projects_data = [_project_to_dict(p) for p in projects]
        
        # Отправляем в каждый настроенный канал
        for bot_settings in bot_settings_list:
            channel_id = bot_settings.channel_id if bot_settings else telegram_bot.channel_id
            settings_dict = None
            
            if bot_settings:
                settings_dict = {
                    'digest_interval_minutes': bot_settings.digest_interval_minutes,
                    'projects_per_digest': bot_settings.projects_per_digest,
                    'max_projects_per_day': bot_settings.max_projects_per_day,
                    'min_coolness_score': bot_settings.min_coolness_score,
                    'min_startup_score': bot_settings.min_startup_score,
                    'min_russia_score': bot_settings.min_russia_score,
                    'allowed_categories': bot_settings.allowed_categories or [],
                    'excluded_categories': bot_settings.excluded_categories or [],
                    'send_digest': bot_settings.send_digest,
                    'send_detailed_review': bot_settings.send_detailed_review,
                    'send_individual_alerts': bot_settings.send_individual_alerts,
                    'send_rotation_updates': bot_settings.send_rotation_updates,
                    'active_hours_start': bot_settings.active_hours_start,
                    'active_hours_end': bot_settings.active_hours_end,
                    'timezone': bot_settings.timezone,
                    'include_ai_summary': bot_settings.include_ai_summary,
                    'include_revenue_prediction': bot_settings.include_revenue_prediction,
                    'include_russia_launch': bot_settings.include_russia_launch,
                    'include_opportunity_ideas': bot_settings.include_opportunity_ideas,
                    'cooldown_minutes': bot_settings.cooldown_minutes,
                    'last_sent_at': bot_settings.last_sent_at,
                    'messages_sent_today': bot_settings.messages_sent_today,
                }
            
            # Отправляем дайджест ВСЕХ проектов с учетом настроек
            if not bot_settings or bot_settings.send_digest:
                await telegram_bot.send_coolness_digest(
                    projects_data, 
                    channel_id=channel_id, 
                    bot_settings=settings_dict
                )
            
            # Отправляем детальный обзор топ-1 проекта (если включено)
            if projects_data and (not bot_settings or bot_settings.send_detailed_review):
                # Фильтруем по настройкам для детального обзора
                filtered = telegram_bot._filter_projects_by_settings(projects_data, settings_dict or {})
                if filtered:
                    await telegram_bot.send_detailed_project_review(filtered[0], channel_id=channel_id)
            
            # Отправляем индивидуальные уведомления (если включено)
            if not bot_settings or bot_settings.send_individual_alerts:
                high_coolness = [p for p in projects_data if p.get('coolness_score', 0) >= 80]
                filtered_high = telegram_bot._filter_projects_by_settings(high_coolness, settings_dict or {})
                for project in filtered_high[:5]:  # Максимум 5 индивидуальных уведомлений
                    await telegram_bot.send_project_alert(project, channel_id=channel_id)


@celery_app.task
def send_daily_digest():
    """Отправка дайджеста в Telegram"""
    asyncio.run(_send_daily_digest_async())


async def _send_daily_digest_async():
    """Асинхронная отправка дайджеста"""
    from app.services.telegram_bot import telegram_bot
    
    async with AsyncSessionLocal() as session:
        today = datetime.utcnow().date()
        
        result = await session.execute(
            select(DailyReport).where(DailyReport.report_date == today)
        )
        report = result.scalar_one_or_none()
        
        if not report:
            return
        
        top_projects = report.top_projects or []
        
        for project_data in top_projects[:5]:
            if project_data.get('startup_score', 0) >= settings.MIN_STARTUP_SCORE_FOR_TELEGRAM:
                await telegram_bot.send_project_alert(project_data)
        
        report.sent_to_telegram = True
        await session.commit()


@celery_app.task
def generate_business_ideas_from_trends():
    """Генерация бизнес-идей на основе трендов"""
    asyncio.run(_generate_business_ideas_async())


async def _generate_business_ideas_async():
    """Генерация бизнес-идей на основе взрывных трендов"""
    from app.services.ai_analyzer import ollama_client
    
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Trend).where(
                and_(
                    Trend.is_exploding == True,
                )
            ).limit(5)
        )
        trends = result.scalars().all()
        
        for trend in trends:
            try:
                ideas = await ollama_client.generate_business_ideas(
                    trend_name=trend.name,
                    trend_description=trend.description or ""
                )
                
                trend.description = (trend.description or "") + f"\n\n💡 Бизнес-идеи:\n" + "\n".join([f"{i+1}. {idea}" for i, idea in enumerate(ideas)])
                
                await session.commit()
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task
def export_projects_to_csv():
    """Экспорт проектов в CSV"""
    asyncio.run(_export_to_csv_async())


async def _export_to_csv_async():
    """Экспорт проектов в CSV файл"""
    import csv
    import os
    from sqlalchemy import select, and_
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(Project.status == 'active').order_by(desc(Project.startup_score))
        )
        projects = result.scalars().all()
        
        export_dir = '/app/exports'
        os.makedirs(export_dir, exist_ok=True)
        
        filename = f"{export_dir}/projects_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'ID', 'Name', 'Category', 'Description', 'Website', 'GitHub URL',
                'Startup Score', 'Russia Score', 'Copy Score', 'Money Score', 'Viral Score',
                'Gap Status', 'Market Saturation', 'Likes', 'GitHub Stars', 'Discovered At'
            ])
            
            for project in projects:
                saturation = scoring_service.calculate_market_saturation_score(project)
                writer.writerow([
                    str(project.id),
                    project.name,
                    project.category,
                    (project.description or '')[:200],
                    project.website or '',
                    project.github_url or '',
                    project.startup_score,
                    project.russia_opportunity_score,
                    project.copy_score,
                    project.money_score,
                    project.viral_score,
                    project.gap_status,
                    saturation,
                    project.likes,
                    project.github_stars,
                    project.discovered_at.isoformat() if project.discovered_at else ''
                ])
        
        logger.info("Exported %d projects to %s", len(projects), filename)


@celery_app.task
def export_projects_to_excel():
    """Экспорт проектов в Excel"""
    asyncio.run(_export_to_excel_async())


async def _export_to_excel_async():
    """Экспорт проектов в Excel файл"""
    import os
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        logger.warning("openpyxl not installed, falling back to CSV")
        await _export_to_csv_async()
        return
    
    from sqlalchemy import select, and_
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(Project.status == 'active').order_by(desc(Project.startup_score))
        )
        projects = result.scalars().all()
        
        export_dir = '/app/exports'
        os.makedirs(export_dir, exist_ok=True)
        
        filename = f"{export_dir}/projects_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Projects"
        
        headers = [
            'ID', 'Name', 'Category', 'Description', 'Website', 'GitHub URL',
            'Startup Score', 'Russia Score', 'Copy Score', 'Money Score', 'Viral Score',
            'Gap Status', 'Market Saturation', 'Likes', 'GitHub Stars', 'Discovered At'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(bold=True, color="FFFFFF")
        
        for row, project in enumerate(projects, 2):
            saturation = scoring_service.calculate_market_saturation_score(project)
            ws.cell(row=row, column=1, value=str(project.id))
            ws.cell(row=row, column=2, value=project.name)
            ws.cell(row=row, column=3, value=project.category)
            ws.cell(row=row, column=4, value=(project.description or '')[:200])
            ws.cell(row=row, column=5, value=project.website or '')
            ws.cell(row=row, column=6, value=project.github_url or '')
            ws.cell(row=row, column=7, value=project.startup_score)
            ws.cell(row=row, column=8, value=project.russia_opportunity_score)
            ws.cell(row=row, column=9, value=project.copy_score)
            ws.cell(row=row, column=10, value=project.money_score)
            ws.cell(row=row, column=11, value=project.viral_score)
            ws.cell(row=row, column=12, value=project.gap_status)
            ws.cell(row=row, column=13, value=saturation)
            ws.cell(row=row, column=14, value=project.likes)
            ws.cell(row=row, column=15, value=project.github_stars)
            ws.cell(row=row, column=16, value=project.discovered_at.isoformat() if project.discovered_at else '')
        
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except (ValueError, TypeError, AttributeError):
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        wb.save(filename)
        logger.info("Exported %d projects to %s", len(projects), filename)