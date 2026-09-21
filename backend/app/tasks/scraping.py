import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import select, update, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models import Project, Source, ScrapeLog, Trend
from app.scrapers.scrapers import ScraperFactory
from app.services.ai_analyzer import ollama_client
from app.services.scoring import scoring_service
from app.services.vector_store import vector_store
from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def scrape_source(self, source_name: str):
    """Задача скрапинга источника"""
    asyncio.run(_scrape_source_async(source_name))


async def _scrape_source_async(source_name: str):
    """Асинхронный скрапинг источника с дедупликацией через Qdrant"""
    async with AsyncSessionLocal() as session:
        log = None
        try:
            result = await session.execute(
                select(Source).where(Source.name == source_name)
            )
            source = result.scalar_one_or_none()
            
            if not source or not source.is_active:
                return
            
            log = ScrapeLog(
                source_id=source.id,
                status='running',
                started_at=datetime.utcnow(),
            )
            session.add(log)
            await session.commit()
            
            scraper = ScraperFactory.get_scraper(source_name)
            if not scraper:
                log.status = 'error'
                log.error_message = f"Scraper not found for {source_name}"
                log.finished_at = datetime.utcnow()
                await session.commit()
                return
            
            projects_data = await scraper.scrape()
            
            items_new = 0
            items_updated = 0
            items_duplicate = 0
            
            for project_data in projects_data:
                try:
                    # Check for duplicates via vector store
                    duplicates = await vector_store.find_duplicates(
                        name=project_data.get('name', ''),
                        description=project_data.get('description', ''),
                        threshold=0.90
                    )
                    
                    if duplicates:
                        items_duplicate += 1
                        continue
                    
                    # Check existing by URL
                    existing = await session.execute(
                        select(Project).where(
                            and_(
                                Project.source_url == project_data.get('source_url'),
                                Project.name == project_data.get('name')
                            )
                        )
                    )
                    existing_project = existing.scalar_one_or_none()
                    
                    if existing_project:
                        # Update existing project
                        for key, value in project_data.items():
                            if key != 'source_name' and hasattr(existing_project, key):
                                setattr(existing_project, key, value)
                        existing_project.last_updated_at = datetime.utcnow()
                        items_updated += 1
                    else:
                        # Create new project
                        new_project = Project(
                            source_id=source.id,
                            **{k: v for k, v in project_data.items() if k != 'source_name' and hasattr(Project, k)}
                        )
                        session.add(new_project)
                        await session.flush()  # Get ID
                        
                        # Add to vector store
                        await vector_store.add_project(
                            project_id=str(new_project.id),
                            name=new_project.name,
                            description=new_project.description or '',
                            category=new_project.category or 'unknown',
                            metadata={'source': source_name}
                        )
                        
                        items_new += 1
                
                except Exception as e:
                    continue
            
            log.status = 'success'
            log.items_found = len(projects_data)
            log.items_new = items_new
            log.items_updated = items_updated
            log.finished_at = datetime.utcnow()
            log.duration_seconds = int((log.finished_at - log.started_at).total_seconds())
            
            source.last_scraped_at = datetime.utcnow()
            
            await session.commit()
            
        except Exception as e:
            await session.rollback()
            if log:
                log.status = 'error'
                log.error_message = str(e)
                log.finished_at = datetime.utcnow()
                await session.commit()
            raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_unprocessed_projects(self):
    """Анализ новых проектов через AI с полным набором модулей"""
    try:
        asyncio.run(_analyze_projects_async())
    except Exception as exc:
        raise self.retry(exc=exc)


async def _check_ai_enabled(session) -> bool:
    """Проверить включен ли AI анализ"""
    from app.models import get_app_setting
    ai_enabled = await get_app_setting(session, "ai_analysis_enabled", "true")
    return ai_enabled == "true"


async def _analyze_projects_async():
    """Асинхронный анализ проектов с расширенными модулями"""
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.ai_summary.is_(None),
                    Project.status == 'active'
                )
            ).limit(5)  # Reduced for complex analysis
        )
        projects = result.scalars().all()
        
        for project in projects:
            try:
                # Run core analyses in parallel
                analysis, russia_analysis = await asyncio.gather(
                    ollama_client.analyze_project(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown"
                    ),
                    ollama_client.analyze_russia_opportunity(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown"
                    ),
                )
                
                project.ai_summary = analysis.get('summary', '')
                project.problem_solved = analysis.get('problem', '')
                project.target_audience = analysis.get('target_audience', '')
                project.monetization_type = analysis.get('monetization_type', '')
                project.growth_potential = analysis.get('growth_potential', 50)
                project.viral_potential = analysis.get('viral_potential', 50)
                project.money_potential = analysis.get('money_potential', 50)
                project.failure_probability = analysis.get('failure_probability', 50)
                project.competition_level = analysis.get('competition_level', 50)
                project.market_size = analysis.get('market_size', 'medium')
                project.implementation_complexity = analysis.get('implementation_complexity', 50)
                project.solo_founder_possible = analysis.get('solo_founder_possible', False)
                project.small_team_possible = analysis.get('small_team_possible', True)
                project.mvp_timeline = analysis.get('mvp_timeline', '3-6 months')
                project.profit_timeline = analysis.get('profit_timeline', '6-12 months')
                project.scaling_potential = analysis.get('scaling_potential', 50)
                
                project.has_russia_analog = russia_analysis.get('has_russia_analog', False)
                project.has_cis_analog = russia_analysis.get('has_cis_analog', False)
                project.has_strong_competitor = russia_analysis.get('has_strong_competitor', False)
                project.has_weak_competitor = russia_analysis.get('has_weak_competitor', False)
                project.can_localize = russia_analysis.get('can_localize', False)
                project.can_quick_launch = russia_analysis.get('can_quick_launch', False)
                project.legal_restrictions = russia_analysis.get('legal_restrictions', False)
                
                # Founder analysis
                if project.author:
                    founder_analysis = await ollama_client.analyze_founder_history(
                        founder_name=project.author, founder_url=project.author_url or "",
                        previous_projects=[]
                    )
                    project.founder_history_score = founder_analysis.get('founder_history_score', 0)
                
                # Run parallel secondary analyses
                patent_analysis, saturation_analysis, opp_engine, revenue = await asyncio.gather(
                    ollama_client.analyze_patent_risks(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown"
                    ),
                    ollama_client.calculate_market_saturation(
                        category=project.category or "unknown",
                        description=project.description or ""
                    ),
                    ollama_client.generate_opportunity_engine(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown"
                    ),
                    ollama_client.predict_revenue(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown",
                        monetization_type=project.monetization_type or "unknown"
                    ),
                )
                
                project.ai_summary = (project.ai_summary or "") + f"\n\n📋 Patent Risk: {patent_analysis.get('patent_risk', 50)}/100"
                project.ai_summary = (project.ai_summary or "") + f"\n\n📊 Market Saturation: {saturation_analysis.get('saturation_score', 50)}/100"
                
                ideas_text = "\n\n🚀 Opportunity Engine - Бизнес-идеи:\n\n"
                for i, idea in enumerate(opp_engine.get('ideas', [])[:3], 1):
                    ideas_text += f"Идея #{i}: {idea.get('name', 'Unknown')}\n"
                    ideas_text += f"  Тип: {idea.get('type', 'Unknown')}\n"
                    ideas_text += f"  Описание: {idea.get('description', '')}\n"
                    ideas_text += f"  Монетизация: {idea.get('monetization', '')}\n"
                    ideas_text += f"  MVP: {idea.get('mvp_weeks', '?')} недель\n"
                    ideas_text += f"  Бюджет: {idea.get('budget_rub', '?')} ₽\n"
                    ideas_text += f"  Вероятность успеха: {idea.get('success_probability', '?')}%\n\n"
                project.ai_summary = (project.ai_summary or "") + ideas_text
                
                revenue_text = "\n\n💰 Revenue Predictor - Прогноз выручки:\n\n"
                for scenario, data in revenue.get('scenarios', {}).items():
                    revenue_text += f"{scenario.replace('_', ' ').title()}:\n"
                    revenue_text += f"  Месячная выручка: {data.get('monthly_revenue_rub', 0):,} ₽\n"
                    revenue_text += f"  Годовая выручка: {data.get('annual_revenue_rub', 0):,} ₽\n"
                    revenue_text += f"  Средний чек: {data.get('avg_check_rub', 0)} ₽\n"
                    revenue_text += f"  Конверсия: {data.get('paid_conversion', 0)}%\n"
                    revenue_text += f"  Churn: {data.get('churn_rate', 0)}%\n"
                    revenue_text += f"  Срок достижения: {data.get('months_to_reach', 0)} мес\n\n"
                revenue_text += f"Модель: {revenue.get('best_monetization', 'Unknown')}\n"
                revenue_text += f"Break-even: {revenue.get('break_even_users', '?')} пользователей\n"
                project.ai_summary = (project.ai_summary or "") + revenue_text
                
                # Russia Launch + CIS in parallel
                russia_launch, cis = await asyncio.gather(
                    ollama_client.generate_russia_launch(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown"
                    ),
                    ollama_client.analyze_cis_opportunity(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown"
                    ),
                )
                
                project.ai_summary = (project.ai_summary or "") + f"\n\n🇷🇺 Russia Launch: {russia_launch.get('names', [''])[0]} | УТП: {russia_launch.get('utp', '')}"
                
                cis_text = "\n\n🌍 СНГ Opportunity Score:\n\n"
                for country, data in cis.get('countries', {}).items():
                    status = "✅" if data.get('recommendation') == 'launch' else "⚠️" if data.get('recommendation') == 'wait' else "❌"
                    cis_text += f"{status} {country.title()}: {data.get('opportunity_score', 0)}/100"
                    if data.get('analog_name'):
                        cis_text += f" (аналог: {data.get('analog_name')})"
                    cis_text += "\n"
                cis_text += f"\nЛучший рынок: {cis.get('best_market', 'russia')}\n"
                cis_text += f"Общий СНГ скор: {cis.get('total_cis_score', 0)}/100\n"
                project.ai_summary = (project.ai_summary or "") + cis_text
                
                # App Clone Detector (только для mobile/chrome)
                if project.category in ['mobile_apps', 'chrome_extensions']:
                    clone = await ollama_client.detect_app_clone_potential(
                        name=project.name, description=project.description or "",
                        category=project.category or "unknown", app_store_url=project.website or ""
                    )
                    project.ai_summary = (project.ai_summary or "") + f"\n\n📱 Clone: {clone.get('clone_complexity', 50)}/100 | {clone.get('mvp_weeks', '?')} нед"
                
                # Acquisition Detector
                acquisition = await ollama_client.detect_acquisition_signal(
                    name=project.name, description=project.description or "",
                    category=project.category or "unknown",
                    investment_amount=float(project.investment_amount) if project.investment_amount else 0
                )
                project.ai_summary = (project.ai_summary or "") + f"\n\n🎯 Acquisition: {acquisition.get('acquisition_probability', 0)}/100 | ${acquisition.get('estimated_value_usd', 0):,}"
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def score_unscored_projects(self):
    """Расчет скоров для проектов"""
    try:
        asyncio.run(_score_projects_async())
    except Exception as exc:
        raise self.retry(exc=exc)


async def _score_projects_async():
    """Асинхронный расчет скоров (алгоритмический, без AI)"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.startup_score.is_(None),
                    Project.status == 'active'
                )
            ).limit(20)
        )
        projects = result.scalars().all()
        
        for project in projects:
            try:
                scores = scoring_service.calculate_all_scores(project)
                
                project.copy_score = scores['copy_score']
                project.money_score = scores['money_score']
                project.viral_score = scores['viral_score']
                project.startup_score = scores['startup_score']
                project.russia_opportunity_score = scores['russia_opportunity_score']
                project.coolness_score = scores['coolness_score']
                project.market_saturation_score = scoring_service.calculate_market_saturation_score(project)
                project.rotation_priority = scoring_service.get_rotation_priority(project)
                
                project.gap_status = scoring_service.determine_gap_status(project)
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task
def detect_trend_explosions():
    """Обнаружение взрывных трендов"""
    asyncio.run(_detect_trends_async())


async def _detect_trends_async():
    """Обнаружение трендов с резким ростом"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Trend).where(
                and_(
                    Trend.growth_percent > 100,
                    Trend.is_exploding == False
                )
            )
        )
        trends = result.scalars().all()
        
        for trend in trends:
            trend.is_exploding = True
            trend.explosion_detected_at = datetime.utcnow()
        
        await session.commit()


@celery_app.task
def detect_github_explosions():
    """Обнаружение GitHub проектов с резким ростом stars"""
    asyncio.run(_detect_github_async())


async def _detect_github_async():
    """Обнаружение GitHub проектов с взрывным ростом"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.github_stars > 1000,
                    Project.discovered_at >= datetime.utcnow() - timedelta(days=7)
                )
            )
        )
        projects = result.scalars().all()
        
        for project in projects:
            if project.startup_score:
                project.startup_score = min(100, project.startup_score + 10)
        
        await session.commit()


@celery_app.task
def generate_opportunity_plans():
    """Генерация планов запуска для топ проектов"""
    asyncio.run(_generate_opportunity_plans_async())


async def _generate_opportunity_plans_async():
    """Генерация конкретных планов запуска для России"""
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.russia_opportunity_score >= 70,
                    Project.gap_status == 'green',
                    Project.status == 'active'
                )
            ).limit(5)
        )
        projects = result.scalars().all()
        
        for project in projects:
            try:
                # Generate opportunity plan
                opportunity_plan = await ollama_client.generate_opportunity_plan(
                    name=project.name,
                    description=project.description or "",
                    category=project.category or "unknown"
                )
                
                # Store in project notes or description
                plan_text = f"""
💡 План запуска для России:

Название: {opportunity_plan.get('names', [''])[0]}
Формат: {opportunity_plan.get('format', 'Unknown')}
Бюджет: {opportunity_plan.get('budget_rub', 0)} ₽
Срок MVP: {opportunity_plan.get('mvp_weeks', 4)} недель
Вероятность успеха: {opportunity_plan.get('success_probability', 50)}%

MVP функции:
{chr(10).join(['- ' + f for f in opportunity_plan.get('mvp_features', [])])}

Стек: {', '.join(opportunity_plan.get('tech_stack', []))}
"""
                
                project.ai_summary = (project.ai_summary or "") + plan_text
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task
def auto_rotate_old_projects():
    """Автоматическая ротация старых проектов при достижении лимита"""
    asyncio.run(_auto_rotate_async())


async def _auto_rotate_async():
    """Автоматическая ротация проектов при достижении лимита"""
    async with AsyncSessionLocal() as session:
        from app.models import RotationLog
        
        # Count active projects
        count_result = await session.execute(
            select(func.count(Project.id)).where(Project.status == 'active')
        )
        total_active = count_result.scalar()
        
        MAX_PROJECTS = 1000
        
        if total_active <= MAX_PROJECTS:
            return  # No rotation needed
        
        # Get projects sorted by rotation priority (highest first = rotate first)
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.status == 'active',
                    Project.is_rotated == False
                )
            ).order_by(desc(Project.rotation_priority)).limit(total_active - MAX_PROJECTS)
        )
        projects_to_rotate = result.scalars().all()
        
        for project in projects_to_rotate:
            project.is_rotated = True
            project.rotated_at = datetime.utcnow()
            project.status = 'rotated'
            
            # Create rotation log
            rotation_log = RotationLog(
                project_id=project.id,
                rotation_reason='auto_limit_reached',
                rotation_priority=project.rotation_priority or 50,
                coolness_score_before=project.coolness_score,
                startup_score_before=project.startup_score
            )
            session.add(rotation_log)
        
        await session.commit()


@celery_app.task
def generate_clone_specs():
    """Генерация ТЗ для клонирования проектов"""
    asyncio.run(_generate_clone_specs_async())


async def _generate_clone_specs_async():
    """Генерация полного ТЗ для клонирования"""
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.copy_score >= 70,
                    Project.status == 'active',
                    Project.ai_summary.isnot(None)
                )
            ).limit(3)
        )
        projects = result.scalars().all()
        
        for project in projects:
            try:
                clone_spec = await ollama_client.generate_clone_spec(
                    name=project.name,
                    description=project.description or "",
                    category=project.category or "unknown"
                )
                
                spec_text = f"""
📋 Техническое задание для клонирования:

Архитектура: {', '.join(clone_spec.get('architecture', []))}
Сложность: {clone_spec.get('complexity', 50)}/100
Срок: {clone_spec.get('timeline_weeks', 6)} недель
Бюджет: ${clone_spec.get('budget_usd', 3000)}

Стек:
- Frontend: {clone_spec.get('tech_stack', {}).get('frontend', 'Unknown')}
- Backend: {clone_spec.get('tech_stack', {}).get('backend', 'Unknown')}
- Database: {clone_spec.get('tech_stack', {}).get('database', 'Unknown')}
- AI: {clone_spec.get('tech_stack', {}).get('ai', 'None')}

Экраны: {', '.join(clone_spec.get('screens', []))}
"""
                
                project.ai_summary = (project.ai_summary or "") + spec_text
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task
def analyze_russia_barriers():
    """Анализ барьеров для входа в Россию"""
    asyncio.run(_analyze_russia_barriers_async())


async def _analyze_russia_barriers_async():
    """Детальный анализ почему проект не в России"""
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.has_russia_analog == False,
                    Project.status == 'active',
                    Project.ai_summary.isnot(None)
                )
            ).limit(5)
        )
        projects = result.scalars().all()
        
        for project in projects:
            try:
                barriers = await ollama_client.analyze_russia_barriers(
                    name=project.name,
                    description=project.description or "",
                    category=project.category or "unknown"
                )
                
                barrier_text = f"""
🇷🇺 Анализ барьеров для России:

Общий барьер: {barriers.get('total_barrier', 50)}/100
Можно преодолеть: {'Да' if barriers.get('can_overcome', True) else 'Нет'}
Срок: {barriers.get('overcome_weeks', 6)} недель
Рекомендация: {barriers.get('recommendation', 'launch')}

Барьеры:
- Языковой: {barriers.get('language_barrier', 30)}/100
- Регуляторный: {barriers.get('regulatory_barrier', 40)}/100
- Спрос: {barriers.get('demand_barrier', 20)}/100
- Сложность: {barriers.get('implementation_barrier', 50)}/100
- Инфраструктура: {barriers.get('infrastructure_barrier', 30)}/100
- Конкуренция: {barriers.get('competition_barrier', 20)}/100
- Осведомленность: {barriers.get('awareness_barrier', 40)}/100

Почему никто не сделал: {barriers.get('why_not_done', 'Неизвестно')}
"""
                
                project.ai_summary = (project.ai_summary or "") + barrier_text
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                continue


@celery_app.task
def generate_business_plans():
    """Генерация бизнес-планов для топ проектов"""
    asyncio.run(_generate_business_plans_async())


async def _generate_business_plans_async():
    """Автоматическая генерация бизнес-планов"""
    async with AsyncSessionLocal() as session:
        if not await _check_ai_enabled(session):
            return
        result = await session.execute(
            select(Project).where(
                and_(
                    Project.startup_score >= 80,
                    Project.status == 'active'
                )
            ).limit(3)
        )
        projects = result.scalars().all()
        
        for project in projects:
            try:
                business_plan = await ollama_client.generate_business_plan(
                    name=project.name,
                    description=project.description or "",
                    category=project.category or "unknown"
                )
                
                plan_text = f"""
📊 Бизнес-план:

Summary: {business_plan.get('executive_summary', '')}

Рынок:
- TAM: {business_plan.get('market_size', {}).get('tam', 'Unknown')}
- SAM: {business_plan.get('market_size', {}).get('sam', 'Unknown')}
- SOM: {business_plan.get('market_size', {}).get('som', 'Unknown')}

Модель: {business_plan.get('business_model', 'Unknown')}
GTM: {business_plan.get('go_to_market', 'Unknown')}

Команда: {', '.join(business_plan.get('team', []))}
Инвестиции: ${business_plan.get('investment_needed', 50000)}

Риски: {', '.join(business_plan.get('risks', []))}
"""
                
                project.ai_summary = (project.ai_summary or "") + plan_text
                
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                continue