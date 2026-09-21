import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.core.config import settings
from app.services.scoring import scoring_service

logger = logging.getLogger(__name__)


class TelegramBotService:
    """Сервис Telegram бота для публикаций и администрирования"""
    
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
        self.channel_id = settings.TELEGRAM_CHANNEL_ID
        self._settings_cache = {}
        self._cache_timestamp = None
        self._app = None
        self._polling = False
    
    async def _get_app_setting(self, key: str, default: str = "") -> str:
        """Получить настройку приложения"""
        from app.models import get_app_setting
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            return await get_app_setting(session, key, default)
    
    async def _set_app_setting(self, key: str, value: str, description: str = ""):
        """Установить настройку приложения"""
        from app.models import set_app_setting
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await set_app_setting(session, key, value, description)
    
    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команд администрирования"""
        user = update.effective_user
        text = update.message.text.strip()
        
        if text == "/toggle_ai":
            current = await self._get_app_setting("ai_analysis_enabled", "true")
            new_value = "false" if current == "true" else "true"
            await self._set_app_setting("ai_analysis_enabled", new_value, "Включить AI анализ проектов")
            status = "включен" if new_value == "true" else "выключен"
            await update.message.reply_text(
                f"AI анализ {status}\n"
                f"Проекты будут оцениваться {'через Ollama' if new_value == 'true' else 'только алгоритмически (метрики, GitHub)'}"
            )
        
        elif text == "/status":
            ai_enabled = await self._get_app_setting("ai_analysis_enabled", "true")
            ai_status = "AI анализ: ✅ включен" if ai_enabled == "true" else "AI анализ: ❌ выключен"
            await update.message.reply_text(
                f"🤖 AI Startup Radar — Статус\n\n"
                f"{ai_status}\n"
                f"Команды:\n"
                f"/toggle_ai — вкл/выкл AI анализ\n"
                f"/status — статус системы"
            )
    
    def start_polling(self):
        """Запуск polling для команд"""
        if not settings.TELEGRAM_BOT_TOKEN or self._polling:
            return
        
        self._app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self._app.add_handler(CommandHandler(["toggle_ai", "status"], self._admin_command))
        
        import threading
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._polling = True
            self._app.run_polling(allowed_updates=["messages"])
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
    
    async def _get_bot_settings(self, channel_id: str = None) -> Dict:
        """Получение настроек бота из БД или кэша"""
        cache_ttl = timedelta(minutes=5)
        
        # Проверяем кэш
        if (self._cache_timestamp and 
            datetime.utcnow() - self._cache_timestamp < cache_ttl and
            channel_id in self._settings_cache):
            return self._settings_cache[channel_id]
        
        try:
            from app.models import BotSettings
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(BotSettings).where(BotSettings.channel_id == (channel_id or self.channel_id))
                )
                bot_settings = result.scalar_one_or_none()
                
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
                else:
                    # Настройки по умолчанию
                    settings_dict = self._get_default_settings()
                
                # Обновляем кэш
                self._settings_cache[channel_id or self.channel_id] = settings_dict
                self._cache_timestamp = datetime.utcnow()
                
                return settings_dict
        except Exception as e:
            logger.error("Error loading bot settings: %s", e)
            return self._get_default_settings()
    
    def _get_default_settings(self) -> Dict:
        """Настройки по умолчанию"""
        return {
            'digest_interval_minutes': 30,
            'projects_per_digest': 10,
            'max_projects_per_day': 100,
            'min_coolness_score': 50,
            'min_startup_score': 60,
            'min_russia_score': 0,
            'allowed_categories': [],
            'excluded_categories': [],
            'send_digest': True,
            'send_detailed_review': True,
            'send_individual_alerts': False,
            'send_rotation_updates': False,
            'active_hours_start': 0,
            'active_hours_end': 23,
            'timezone': 'Europe/Moscow',
            'include_ai_summary': True,
            'include_revenue_prediction': True,
            'include_russia_launch': True,
            'include_opportunity_ideas': True,
            'cooldown_minutes': 5,
            'last_sent_at': None,
            'messages_sent_today': 0,
        }
    
    def _is_active_hours(self, settings: Dict) -> bool:
        """Проверка активных часов отправки"""
        from pytz import timezone
        tz = timezone(settings.get('timezone', 'Europe/Moscow'))
        now = datetime.now(tz)
        hour = now.hour
        
        start = settings.get('active_hours_start', 0)
        end = settings.get('active_hours_end', 23)
        
        if start <= end:
            return start <= hour <= end
        else:  # Например 22-6 (ночной режим)
            return hour >= start or hour <= end
    
    def _check_cooldown(self, settings: Dict) -> bool:
        """Проверка кулдауна между сообщениями"""
        last_sent = settings.get('last_sent_at')
        cooldown = settings.get('cooldown_minutes', 5)
        
        if not last_sent:
            return True
        
        if isinstance(last_sent, str):
            last_sent = datetime.fromisoformat(last_sent)
        
        return datetime.utcnow() - last_sent >= timedelta(minutes=cooldown)
    
    def _check_daily_limit(self, settings: Dict) -> bool:
        """Проверка дневного лимита сообщений"""
        reset_at = settings.get('reset_counter_at')
        if reset_at:
            if isinstance(reset_at, str):
                reset_at = datetime.fromisoformat(reset_at)
            if datetime.utcnow().date() > reset_at.date():
                # Сброс счетчика
                return True
        
        return settings.get('messages_sent_today', 0) < settings.get('max_projects_per_day', 100)
    
    def _filter_projects_by_settings(self, projects: List[Dict], settings: Dict) -> List[Dict]:
        """Фильтрация проектов по настройкам бота"""
        filtered = []
        
        for project in projects:
            # Фильтр по Coolness Score
            if project.get('coolness_score', 0) < settings.get('min_coolness_score', 50):
                continue
            
            # Фильтр по Startup Score
            if project.get('startup_score', 0) < settings.get('min_startup_score', 60):
                continue
            
            # Фильтр по Russia Score
            if settings.get('min_russia_score', 0) > 0:
                if project.get('russia_opportunity_score', 0) < settings.get('min_russia_score', 0):
                    continue
            
            # Фильтр по категориям
            allowed = settings.get('allowed_categories', [])
            if allowed and project.get('category') not in allowed:
                continue
            
            excluded = settings.get('excluded_categories', [])
            if excluded and project.get('category') in excluded:
                continue
            
            filtered.append(project)
        
        return filtered
    
    async def _update_send_stats(self, channel_id: str = None):
        """Обновление статистики отправки"""
        try:
            from app.models import BotSettings
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select, update
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(BotSettings).where(BotSettings.channel_id == (channel_id or self.channel_id))
                )
                bot_settings = result.scalar_one_or_none()
                
                if bot_settings:
                    # Проверяем нужен ли сброс счетчика
                    if bot_settings.reset_counter_at and bot_settings.reset_counter_at.date() < datetime.utcnow().date():
                        bot_settings.messages_sent_today = 1
                        bot_settings.reset_counter_at = datetime.utcnow()
                    else:
                        bot_settings.messages_sent_today = (bot_settings.messages_sent_today or 0) + 1
                    
                    bot_settings.last_sent_at = datetime.utcnow()
                    await session.commit()
        except Exception as e:
            logger.error("Error updating send stats: %s", e)
    
    async def send_project_alert(self, project_data: Dict, channel_id: str = None) -> bool:
        """Отправка уведомления о проекте в Telegram с учетом настроек"""
        if not self.bot or not self.channel_id:
            return False
        
        target_channel = channel_id or self.channel_id
        
        # Получаем настройки
        bot_settings = await self._get_bot_settings(target_channel)
        
        # Проверяем активные часы
        if not self._is_active_hours(bot_settings):
            logger.info("Skipping send - outside active hours (%d-%d)", bot_settings.get('active_hours_start', 0), bot_settings.get('active_hours_end', 23))
            return False
        
        # Проверяем кулдаун
        if not self._check_cooldown(bot_settings):
            logger.info("Skipping send - cooldown active (%d min)", bot_settings.get('cooldown_minutes', 5))
            return False
        
        # Проверяем дневной лимит
        if not self._check_daily_limit(bot_settings):
            logger.info("Skipping send - daily limit reached (%d/%d)", bot_settings.get('messages_sent_today', 0), bot_settings.get('max_projects_per_day', 100))
            return False
        
        try:
            message = self._format_project_message(project_data, bot_settings)
            await self.bot.send_message(
                chat_id=target_channel,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            # Обновляем статистику
            await self._update_send_stats(target_channel)
            
            return True
        except Exception as e:
            logger.error("Telegram send error: %s", e)
            return False
    
    def _format_project_message(self, project_data: Dict, settings: Dict = None) -> str:
        """Форматирование сообщения о проекте с учетом настроек"""
        
        if settings is None:
            settings = self._get_default_settings()
        
        # Определяем эмодзи по gap_status
        gap_emoji = {
            'green': '🟢',
            'yellow': '🟡',
            'red': '🔴'
        }.get(project_data.get('gap_status', 'yellow'), '🟡')
        
        # Определяем уровень крутости
        coolness = project_data.get('coolness_score', 0)
        if coolness >= 90:
            fire_emoji = '🔥🔥🔥'
        elif coolness >= 80:
            fire_emoji = '🔥🔥'
        elif coolness >= 70:
            fire_emoji = '🔥'
        else:
            fire_emoji = '⭐'
        
        # Market saturation
        saturation = project_data.get('market_saturation_score', 50)
        saturation_text = '🔴 Перенасыщен' if saturation > 80 else '🟡 Насыщен' if saturation > 60 else '🟢 Свободен'
        
        # Revenue prediction (если включено в настройках)
        revenue_text = ""
        if settings.get('include_revenue_prediction', True) and 'revenue_prediction' in project_data:
            rev = project_data['revenue_prediction']
            revenue_text = f"""
💰 <b>Revenue Predictor:</b>
  100 пользователей: {rev.get('100_users', {}).get('monthly_revenue_rub', 0):,} ₽/мес
  1000 пользователей: {rev.get('1000_users', {}).get('monthly_revenue_rub', 0):,} ₽/мес
  10000 пользователей: {rev.get('10000_users', {}).get('monthly_revenue_rub', 0):,} ₽/мес
"""
        
        # CIS Score (если доступно)
        cis_text = ""
        if 'cis_score' in project_data:
            cis = project_data['cis_score']
            cis_text = f"""
🌍 <b>СНГ Opportunity Score:</b>
  🇷🇺 Россия: {cis.get('russia', 0)}/100
  🇰🇿 Казахстан: {cis.get('kazakhstan', 0)}/100
  🇧🇾 Беларусь: {cis.get('belarus', 0)}/100
  🇺🇿 Узбекистан: {cis.get('uzbekistan', 0)}/100
"""
        
        # Opportunity Engine ideas (если включено)
        ideas_text = ""
        if settings.get('include_opportunity_ideas', True) and 'opportunity_ideas' in project_data:
            ideas = project_data['opportunity_ideas']
            ideas_text = "\n🚀 <b>Opportunity Engine - Идеи:</b>\n"
            for i, idea in enumerate(ideas[:3], 1):
                ideas_text += f"  {i}. {idea.get('name', 'Unknown')} ({idea.get('type', 'Unknown')})\n"
                ideas_text += f"     💰 {idea.get('monetization', '')} | MVP: {idea.get('mvp_weeks', '?')} недель\n"
        
        # Russia Launch (если включено)
        russia_launch_text = ""
        if settings.get('include_russia_launch', True) and 'russia_launch' in project_data:
            rl = project_data['russia_launch']
            russia_launch_text = f"""
🇷🇺 <b>Russia Launch Generator:</b>
  Название: {rl.get('names', [''])[0]}
  УТП: {rl.get('utp', '')}
  Бюджет: {rl.get('launch_budget_rub', 0):,} ₽
  До денег: {rl.get('weeks_to_revenue', '?')} недель
"""
        
        message = f"""{fire_emoji} <b>Новый перспективный проект</b>

<b>Название:</b> {project_data.get('name', 'Unknown')}
<b>Категория:</b> {project_data.get('category', 'Unknown')}

<b>Описание:</b>
{project_data.get('description', 'Нет описания')[:300]}...

<b>Скоринг:</b>
🎯 Startup Score: <b>{project_data.get('startup_score', 'N/A')}/100</b>
🇷🇺 Russia Opportunity: <b>{project_data.get('russia_opportunity_score', 'N/A')}/100</b>
💰 Money Score: <b>{project_data.get('money_score', 'N/A')}/100</b>
📈 Viral Score: <b>{project_data.get('viral_score', 'N/A')}/100</b>
🔨 Copy Score: <b>{project_data.get('copy_score', 'N/A')}/100</b>
📊 Market Saturation: <b>{saturation}/100</b> ({saturation_text})

<b>Рынок РФ:</b> {gap_emoji} {self._get_gap_status_text(project_data.get('gap_status'))}
{revenue_text}{cis_text}{ideas_text}{russia_launch_text}
<b>Метрики:</b>
⭐ Stars: {project_data.get('github_stars', 0)}
👍 Likes: {project_data.get('likes', 0)}

<b>Ссылки:</b>
🌐 <a href="{project_data.get('website', '#')}">Website</a>
💻 <a href="{project_data.get('github_url', '#')}">GitHub</a>

#startup #ai #tech #{project_data.get('category', 'project').replace('_', '')}
"""
        return message
    
    def _get_gap_status_text(self, gap_status: Optional[str]) -> str:
        """Текстовое описание gap status"""
        return {
            'green': 'Аналогов нет - отличная возможность!',
            'yellow': 'Есть слабые аналоги - можно конкурировать',
            'red': 'Рынок занят - сложно войти'
        }.get(gap_status, 'Неизвестно')
    
    async def send_trend_explosion_alert(self, trend_data: Dict) -> bool:
        """Уведомление о взрывном тренде"""
        if not self.bot or not self.channel_id:
            return False
        
        try:
            message = f"""🚀 <b>ВЗРЫВНОЙ ТРЕНД ОБНАРУЖЕН!</b>

<b>Тренд:</b> {trend_data.get('name', 'Unknown')}
<b>Категория:</b> {trend_data.get('category', 'Unknown')}

<b>Рост:</b> +{trend_data.get('growth_percent', 0)}% 📈

<b>Описание:</b>
{trend_data.get('description', 'Нет описания')[:200]}...

Рекомендуется рассмотреть возможность запуска продукта в этой нише!

#trend #explosion #opportunity
"""
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.error("Telegram trend alert error: %s", e)
            return False
    
    async def send_opportunity_plan(self, project_data: Dict, opportunity_plan: Dict) -> bool:
        """Отправка плана запуска для России"""
        if not self.bot or not self.channel_id:
            return False
        
        try:
            message = f"""💡 <b>ПЛАН ЗАПУСКА ДЛЯ РОССИИ</b>

<b>Оригинал:</b> {project_data.get('name', 'Unknown')}

<b>Название для РФ:</b> {opportunity_plan.get('names', [''])[0]}
<b>Формат:</b> {opportunity_plan.get('format', 'Unknown')}

<b>Бюджет:</b> {opportunity_plan.get('budget_rub', 0):,} ₽
<b>Срок MVP:</b> {opportunity_plan.get('mvp_weeks', 4)} недель
<b>Вероятность успеха:</b> {opportunity_plan.get('success_probability', 50)}%

<b>MVP функции:</b>
{chr(10).join(['• ' + f for f in opportunity_plan.get('mvp_features', [])[:5]])}

<b>Стек:</b> {', '.join(opportunity_plan.get('tech_stack', []))}

<b>Монетизация:</b> {opportunity_plan.get('monetization', 'Unknown')}

<b>Первые 100 пользователей:</b> {opportunity_plan.get('user_acquisition', 'Unknown')}

#russia #opportunity #mvp
"""
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            logger.error("Telegram opportunity plan error: %s", e)
            return False
    
    async def send_coolness_digest(self, projects_data: List[Dict], channel_id: str = None, bot_settings: Dict = None) -> bool:
        """Отправка дайджеста ВСЕХ проектов по крутости (Coolness Score) каждые 30 минут с учетом настроек"""
        if not self.bot or not self.channel_id:
            return False
        
        target_channel = channel_id or self.channel_id
        
        # Получаем настройки если не переданы
        if bot_settings is None:
            bot_settings = await self._get_bot_settings(target_channel)
        
        # Проверяем активные часы
        if not self._is_active_hours(bot_settings):
            logger.info("Skipping digest - outside active hours")
            return False
        
        # Проверяем кулдаун
        if not self._check_cooldown(bot_settings):
            logger.info("Skipping digest - cooldown active")
            return False
        
        # Проверяем дневной лимит
        if not self._check_daily_limit(bot_settings):
            logger.info("Skipping digest - daily limit reached")
            return False
        
        try:
            if not projects_data:
                return False
            
            # Фильтруем проекты по настройкам
            filtered_projects = self._filter_projects_by_settings(projects_data, bot_settings)
            
            if not filtered_projects:
                logger.info("No projects match bot settings filters")
                return False
            
            # Берем ВСЕ отфильтрованные проекты отсортированные по крутости
            all_projects = sorted(
                filtered_projects, 
                key=lambda p: p.get('coolness_score', 0), 
                reverse=True
            )
            
            # Получаем количество проектов на дайджест из настроек
            projects_per_digest = bot_settings.get('projects_per_digest', 10)
            
            # Разбиваем на чанки по настройкам (по умолчанию 10 проектов)
            chunk_size = min(projects_per_digest, 20)  # Максимум 20 за раз
            chunks = [all_projects[i:i+chunk_size] for i in range(0, len(all_projects), chunk_size)]
            
            # Ограничиваем количество чанков за один раз (чтобы не спамить)
            max_chunks_per_digest = 5  # Максимум 5 сообщений за раз
            chunks = chunks[:max_chunks_per_digest]
            
            for chunk_idx, chunk in enumerate(chunks):
                message = f"🔥 <b>РАДАР СТАРТАПОВ - ЧАНК {chunk_idx+1}/{len(chunks)}</b>\n\n"
                message += f"Всего проектов: {len(all_projects)} | Фильтр: Coolness >={bot_settings.get('min_coolness_score', 50)}\n"
                message += f"Обновление: каждые {bot_settings.get('digest_interval_minutes', 30)} мин\n\n"
                
                for i, project in enumerate(chunk, 1 + chunk_idx * chunk_size):
                    coolness = project.get('coolness_score', 0)
                    
                    # Определяем эмодзи по крутости
                    if coolness >= 90:
                        fire = '🔥🔥🔥'
                    elif coolness >= 80:
                        fire = '🔥🔥'
                    elif coolness >= 70:
                        fire = '🔥'
                    elif coolness >= 60:
                        fire = '⭐'
                    else:
                        fire = '💡'
                    
                    gap_emoji = {
                        'green': '🟢',
                        'yellow': '🟡', 
                        'red': '🔴'
                    }.get(project.get('gap_status', 'yellow'), '🟡')
                    
                    message += f"{fire} <b>#{i} {project.get('name', 'Unknown')}</b>\n"
                    message += f"   🎯 Coolness: <b>{coolness}/100</b>\n"
                    message += f"   📈 Startup: {project.get('startup_score', 'N/A')} | 💰 Money: {project.get('money_score', 'N/A')}\n"
                    message += f"   🇷🇺 Russia: {project.get('russia_opportunity_score', 'N/A')}/100 {gap_emoji}\n"
                    message += f"   🌐 {project.get('website', 'Нет сайта')}\n"
                    
                    # AI Summary (кратко) - если включено в настройках
                    if bot_settings.get('include_ai_summary', True):
                        ai_summary = project.get('ai_summary', '')
                        if ai_summary:
                            summary_clean = ai_summary.split('\n')[0][:150]
                            message += f"   💡 {summary_clean}...\n"
                    
                    message += "\n"
                
                message += f"#coolness #radar #startups #ai #chunk{chunk_idx+1}"
                
                await self.bot.send_message(
                    chat_id=target_channel,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                
                # Обновляем статистику после каждого сообщения
                await self._update_send_stats(target_channel)
            
            return True
        except Exception as e:
            logger.error("Telegram coolness digest error: %s", e)
            return False
    
    async def send_auto_rotated_alert(self, rotated_projects: List[Dict], new_projects: List[Dict]) -> bool:
        """Уведомление об авто-ротации: что ушло, что пришло"""
        if not self.bot or not self.channel_id:
            return False
        
        try:
            message = "🔄 <b>АВТО-РОТАЦИЯ ПРОЕКТОВ</b>\n\n"
            
            # Что ушло
            if rotated_projects:
                message += "📤 <b>Ушли из топа (низкая крутость):</b>\n"
                for p in rotated_projects[:5]:
                    message += f"   ❌ {p.get('name', 'Unknown')} (Coolness: {p.get('coolness_score', 0)})\n"
                message += "\n"
            
            # Что пришло
            if new_projects:
                message += "📥 <b>Новые в топе (высокая крутость):</b>\n"
                for p in new_projects[:5]:
                    message += f"   ✅ {p.get('name', 'Unknown')} (Coolness: {p.get('coolness_score', 0)})\n"
                    message += f"      🌐 {p.get('website', 'Нет сайта')}\n"
                message += "\n"
            
            message += "Ранжирование обновлено автоматически\n"
            message += "#rotation #auto #update"
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error("Telegram rotation alert error: %s", e)
            return False
    
    async def send_detailed_project_review(self, project_data: Dict, channel_id: str = None, bot_settings: Dict = None) -> bool:
        """Детальный обзор одного проекта с полным анализом и учетом настроек"""
        if not self.bot or not self.channel_id:
            return False
        
        target_channel = channel_id or self.channel_id
        
        # Получаем настройки если не переданы
        if bot_settings is None:
            bot_settings = await self._get_bot_settings(target_channel)
        
        # Проверяем активные часы
        if not self._is_active_hours(bot_settings):
            logger.info("Skipping detailed review - outside active hours")
            return False
        
        # Проверяем кулдаун
        if not self._check_cooldown(bot_settings):
            logger.info("Skipping detailed review - cooldown active")
            return False
        
        # Проверяем дневной лимит
        if not self._check_daily_limit(bot_settings):
            logger.info("Skipping detailed review - daily limit reached")
            return False
        
        try:
            coolness = project_data.get('coolness_score', 0)
            
            # Определяем уровень крутости
            if coolness >= 90:
                level = '🏆 ЛЕГЕНДАРНО'
            elif coolness >= 80:
                level = '🔥🔥 ОЧЕНЬ КРУТО'
            elif coolness >= 70:
                level = '🔥 КРУТО'
            elif coolness >= 60:
                level = '⭐ ХОРОШО'
            else:
                level = '💡 ИНТЕРЕСНО'
            
            gap_emoji = {
                'green': '🟢 Аналогов нет!',
                'yellow': '🟡 Есть слабые аналоги',
                'red': '🔴 Рынок занят'
            }.get(project_data.get('gap_status', 'yellow'), '🟡')
            
            message = f"""{level}

<b>{project_data.get('name', 'Unknown')}</b>

🎯 <b>Coolness Score: {coolness}/100</b>
📈 Startup: {project_data.get('startup_score', 'N/A')}/100
💰 Money: {project_data.get('money_score', 'N/A')}/100
📊 Viral: {project_data.get('viral_score', 'N/A')}/100
🇷🇺 Russia: {project_data.get('russia_opportunity_score', 'N/A')}/100

<b>Описание:</b>
{project_data.get('description', 'Нет описания')[:400]}...

<b>AI Анализ:</b>
{project_data.get('ai_summary', 'Нет анализа')[:500]}...

<b>Рынок РФ:</b> {gap_emoji}

<b>Метрики:</b>
⭐ GitHub Stars: {project_data.get('github_stars', 0)}
👍 Likes: {project_data.get('likes', 0)}
📅 Найден: {project_data.get('discovered_at', 'Недавно')}

<b>Ссылки:</b>
🌐 <a href="{project_data.get('website', '#')}">Website</a>
💻 <a href="{project_data.get('github_url', '#')}">GitHub</a>

#startup #{project_data.get('category', 'ai').replace('_', '')} #coolness
"""
            
            await self.bot.send_message(
                chat_id=target_channel,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            # Обновляем статистику
            await self._update_send_stats(target_channel)
            
            return True
        except Exception as e:
            logger.error("Telegram detailed review error: %s", e)
            return False
    
    async def send_daily_digest(self, report_data: Dict) -> bool:
        """Отправка ежедневного дайджеста"""
        if not self.bot or not self.channel_id:
            return False
        
        try:
            top_projects = report_data.get('top_projects', [])[:5]
            
            message = "📊 <b>ЕЖЕДНЕВНЫЙ ДАЙДЖЕСТ AI STARTUP RADAR</b>\n\n"
            message += f"<b>Топ-5 проектов дня:</b>\n\n"
            
            for i, project in enumerate(top_projects, 1):
                message += f"{i}. <b>{project.get('name', 'Unknown')}</b>\n"
                message += f"   🎯 Score: {project.get('startup_score', 'N/A')} | 🇷🇺 RU: {project.get('russia_opportunity_score', 'N/A')}\n"
                message += f"   🔗 {project.get('website', 'N/A')}\n\n"
            
            message += "\nВсе проекты: http://localhost:3000"
            
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error("Telegram digest error: %s", e)
            return False


# Singleton
telegram_bot = TelegramBotService()