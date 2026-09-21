import httpx
import json
import logging
from typing import Dict, Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Клиент для локальных LLM через Ollama"""
    
    def __init__(self, model: str = None):
        self.base_url = settings.OLLAMA_URL
        self.model = model or settings.OLLAMA_MODEL
    
    async def generate(self, prompt: str, system: str = "", temperature: float = 0.7) -> str:
        """Генерация текста через Ollama"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": 2000,
                        }
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
            except Exception as e:
                logger.error("Ollama error: %s", e)
                return ""
    
    async def analyze_project(self, name: str, description: str, category: str) -> Dict:
        """AI анализ проекта"""
        system_prompt = """Ты - эксперт по анализу стартапов и AI-продуктов. 
Твоя задача - проанализировать продукт и дать структурированную оценку.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Проанализируй этот продукт:

Название: {name}
Категория: {category}
Описание: {description}

Дай оценку по следующим параметрам (от 0 до 100, где 100 - максимум):

1. Что делает продукт (2-3 предложения)
2. Какую проблему решает (1-2 предложения)
3. Целевая аудитория (кратко)
4. Тип монетизации (freemium, subscription, one-time, ads, etc.)
5. Потенциал роста (0-100)
6. Потенциал вирусности (0-100)
7. Потенциал заработка (0-100)
8. Вероятность провала (0-100)
9. Уровень конкуренции (0-100)
10. Размер рынка (small/medium/large/huge)
11. Сложность реализации (0-100)
12. Можно ли запустить одному (yes/no)
13. Можно ли запустить маленькой командой 2-5 чел (yes/no)
14. Срок MVP (weeks/months)
15. Срок до прибыли (months/years)
16. Потенциал масштабирования (0-100)

Формат ответа (ТОЛЬКО JSON):
{{
    "summary": "...",
    "problem": "...",
    "target_audience": "...",
    "monetization_type": "...",
    "growth_potential": 75,
    "viral_potential": 60,
    "money_potential": 80,
    "failure_probability": 30,
    "competition_level": 50,
    "market_size": "medium",
    "implementation_complexity": 40,
    "solo_founder_possible": true,
    "small_team_possible": true,
    "mvp_timeline": "2-3 months",
    "profit_timeline": "6-12 months",
    "scaling_potential": 85
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "summary": description[:200],
            "problem": "Unknown",
            "target_audience": "Unknown",
            "monetization_type": "unknown",
            "growth_potential": 50,
            "viral_potential": 50,
            "money_potential": 50,
            "failure_probability": 50,
            "competition_level": 50,
            "market_size": "medium",
            "implementation_complexity": 50,
            "solo_founder_possible": False,
            "small_team_possible": True,
            "mvp_timeline": "3-6 months",
            "profit_timeline": "6-12 months",
            "scaling_potential": 50,
        }
    
    async def analyze_russia_opportunity(self, name: str, description: str, category: str) -> Dict:
        """Анализ возможности запуска в России"""
        system_prompt = """Ты - эксперт по рынку России и СНГ. 
Твоя задача - оценить возможность локализации продукта для России.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Оцени возможность запуска этого продукта в России и СНГ:

Название: {name}
Категория: {category}
Описание: {description}

Оцени по следующим критериям (yes/no/unknown):
1. Есть ли аналог в России (yes/no/unknown)
2. Есть ли аналог в СНГ (yes/no/unknown)
3. Есть ли сильный конкурент (yes/no/unknown)
4. Есть ли слабый конкурент (yes/no/unknown)
5. Можно ли локализовать (yes/no/unknown)
6. Можно ли быстро запустить (yes/no/unknown)
7. Есть ли юридические ограничения (yes/no/unknown)

И общую оценку возможности (0-100):
8. Russia Opportunity Score (0-100)

Формат ответа (ТОЛЬКО JSON):
{{
    "has_russia_analog": false,
    "has_cis_analog": false,
    "has_strong_competitor": false,
    "has_weak_competitor": false,
    "can_localize": true,
    "can_quick_launch": true,
    "legal_restrictions": false,
    "russia_opportunity_score": 85,
    "gap_status": "green"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "has_russia_analog": False,
            "has_cis_analog": False,
            "has_strong_competitor": False,
            "has_weak_competitor": False,
            "can_localize": True,
            "can_quick_launch": True,
            "legal_restrictions": False,
            "russia_opportunity_score": 50,
            "gap_status": "yellow",
        }
    
    async def generate_business_ideas(self, trend_name: str, trend_description: str) -> List[str]:
        """Генерация бизнес-идей на основе тренда"""
        prompt = f"""На основе этого тренда сгенерируй 5 бизнес-идей для запуска в России:

Тренд: {trend_name}
Описание: {trend_description}

Каждая идея должна быть:
1. Реалистичной для запуска в России
2. С минимальными инвестициями
3. С четким описанием MVP

Формат: просто список из 5 идей, каждая 2-3 предложения."""
        
        response = await self.generate(prompt, temperature=0.8)
        
        ideas = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                ideas.append(line.lstrip('0123456789.-* '))
        
        return ideas[:5] if ideas else ["AI-консультант для бизнеса", "Автоматизация документооборота"]
    
    async def analyze_founder_history(self, founder_name: str, founder_url: str, previous_projects: List[str]) -> Dict:
        """Анализ истории основателя"""
        system_prompt = """Ты - эксперт по анализу основателей стартапов.
Оцени историю основателя на основе его предыдущих проектов."""
        
        projects_text = "\n".join([f"- {p}" for p in previous_projects]) if previous_projects else "Нет известных предыдущих проектов"
        
        prompt = f"""Оцени основателя:

Имя: {founder_name}
URL: {founder_url}
Предыдущие проекты:
{projects_text}

Оцени (0-100):
1. Founder History Score (0-100) - насколько успешны были предыдущие проекты
2. Есть ли успешные выходы (exit) - yes/no
3. Есть ли провальные проекты - yes/no
4. Уровень опыта (junior/mid/senior/expert)

Формат (ТОЛЬКО JSON):
{{
    "founder_history_score": 75,
    "has_successful_exits": true,
    "has_failed_projects": false,
    "experience_level": "expert"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "founder_history_score": 50,
            "has_successful_exits": False,
            "has_failed_projects": False,
            "experience_level": "mid",
        }
    
    async def generate_localization_ideas(self, project_name: str, project_description: str, category: str) -> List[str]:
        """Генерация идей локализации для России"""
        prompt = f"""Предложи 5 идей локализации этого продукта для рынка России и СНГ:

Продукт: {project_name}
Категория: {category}
Описание: {project_description}

Каждая идея должна включать:
1. Что локализовать
2. Как адаптировать под рынок РФ
3. Возможные партнеры или каналы
4. Примерный бюджет

Формат: список из 5 идей."""
        
        response = await self.generate(prompt, temperature=0.7)
        
        ideas = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                ideas.append(line.lstrip('0123456789.-* '))
        
        return ideas[:5] if ideas else ["Локализация интерфейса на русский", "Адаптация платежных систем"]
    
    async def generate_opportunity_plan(self, name: str, description: str, category: str) -> Dict:
        """Генерация конкретного плана запуска для России"""
        system_prompt = """Ты - эксперт по запуску стартапов в России.
Создай конкретный план запуска аналога продукта."""
        
        prompt = f"""Создай конкретный план запуска аналога этого продукта в России:

Название оригинала: {name}
Категория: {category}
Описание: {description}

Дай конкретный ответ:

1. Название для РФ рынка (3 варианта)
2. Формат продукта (Telegram бот / веб / мобильное приложение / SaaS)
3. MVP функционал (список из 5 пунктов)
4. Стек технологий (конкретные технологии)
5. Монетизация (конкретные цены в ₽)
6. Бюджет запуска (конкретная сумма в ₽)
7. Срок MVP (конкретно в неделях)
8. Первые 100 пользователей (где искать)
9. Конкуренты в РФ (если есть)
10. Вероятность успеха (0-100)

Формат (ТОЛЬКО JSON):
{{
    "names": ["Название 1", "Название 2", "Название 3"],
    "format": "Telegram бот + веб версия",
    "mvp_features": ["Функция 1", "Функция 2", "Функция 3", "Функция 4", "Функция 5"],
    "tech_stack": ["Python", "FastAPI", "React", "PostgreSQL"],
    "monetization": "Подписка 499 ₽/мес, пробный период 7 дней",
    "budget_rub": 50000,
    "mvp_weeks": 3,
    "user_acquisition": "Telegram каналы, Product Hunt, Reddit",
    "russia_competitors": ["Конкурент 1", "Конкурент 2"],
    "success_probability": 75
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "names": [f"{name} Russia", f"{name} RU", f"{name} СНГ"],
            "format": "Telegram бот",
            "mvp_features": ["Базовый функционал", "Регистрация", "Оплата"],
            "tech_stack": ["Python", "FastAPI"],
            "monetization": "Подписка 499 ₽/мес",
            "budget_rub": 50000,
            "mvp_weeks": 4,
            "user_acquisition": "Telegram, соцсети",
            "russia_competitors": [],
            "success_probability": 60,
        }
    
    async def generate_clone_spec(self, name: str, description: str, category: str) -> Dict:
        """Генерация полного ТЗ для клонирования продукта"""
        system_prompt = """Ты - технический архитектор стартапов.
Создай полное техническое задание для клонирования продукта."""
        
        prompt = f"""Создай полное ТЗ для клонирования этого продукта:

Название: {name}
Категория: {category}
Описание: {description}

Дай полное ТЗ:

1. Бизнес-модель (как зарабатывать)
2. Архитектура системы (компоненты)
3. Стек технологий (фронтенд, бэкенд, БД, AI)
4. Экраны приложения (список всех экранов)
5. API endpoints (основные)
6. Модель данных (таблицы)
7. Интеграции (какие API нужны)
8. AI компоненты (если нужны)
9. Монетизация (тарифы)
10. MVP scope (что в первой версии)
11. Оценка сложности (0-100)
12. Оценка времени (недели)
13. Оценка бюджета ($)

Формат (ТОЛЬКО JSON):
{{
    "business_model": "...",
    "architecture": ["Компонент 1", "Компонент 2"],
    "tech_stack": {{
        "frontend": "React",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "ai": "OpenAI API"
    }},
    "screens": ["Экран 1", "Экран 2"],
    "api_endpoints": ["GET /api/items", "POST /api/items"],
    "data_model": ["users", "items", "subscriptions"],
    "integrations": ["Stripe", "OpenAI"],
    "ai_components": ["Chatbot", "Recommendation"],
    "pricing": ["Free", "Pro $10", "Enterprise"],
    "mvp_scope": ["Функция 1", "Функция 2"],
    "complexity": 60,
    "timeline_weeks": 8,
    "budget_usd": 5000
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "business_model": "Freemium SaaS",
            "architecture": ["Frontend", "Backend", "Database"],
            "tech_stack": {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL",
                "ai": "OpenAI"
            },
            "screens": ["Home", "Dashboard", "Settings"],
            "api_endpoints": ["GET /api/items", "POST /api/items"],
            "data_model": ["users", "items"],
            "integrations": ["Stripe"],
            "ai_components": [],
            "pricing": ["Free", "Pro $10"],
            "mvp_scope": ["Базовый функционал"],
            "complexity": 50,
            "timeline_weeks": 6,
            "budget_usd": 3000,
        }
    
    async def analyze_patent_risks(self, name: str, description: str, category: str) -> Dict:
        """Анализ патентных и юридических рисков"""
        system_prompt = """Ты - юрист по интеллектуальной собственности.
Оцени патентные и юридические риски клонирования продукта."""
        
        prompt = f"""Оцени юридические риски клонирования этого продукта:

Название: {name}
Категория: {category}
Описание: {description}

Оцени:

1. Вероятность патентных ограничений (0-100)
2. Есть ли известные патенты (yes/no/unknown)
3. Тип лицензии оригинала (open-source/proprietary/unknown)
4. Можно ли свободно копировать (yes/no/unknown)
5. Риски судебных исков (low/medium/high)
6. Рекомендации по защите (текст)
7. Альтернативные подходы (текст)

Формат (ТОЛЬКО JSON):
{{
    "patent_risk": 30,
    "known_patents": false,
    "license_type": "unknown",
    "can_copy": true,
    "lawsuit_risk": "low",
    "recommendations": "...",
    "alternatives": "..."
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "patent_risk": 50,
            "known_patents": False,
            "license_type": "unknown",
            "can_copy": True,
            "lawsuit_risk": "medium",
            "recommendations": "Проверить лицензию оригинала",
            "alternatives": "Реализовать схожий функционал другим способом",
        }
    
    async def calculate_market_saturation(self, category: str, description: str) -> Dict:
        """Расчет насыщенности рынка"""
        system_prompt = """Ты - аналитик рынка.
Оцени насыщенность рынка для категории продукта."""
        
        prompt = f"""Оцени насыщенность рынка для этой категории:

Категория: {category}
Описание: {description}

Оцени (0-100, где 100 = перенасыщен):

1. Market Saturation Score (0-100)
2. Количество конкурентов (many/some/few/none)
3. Сложность входа (easy/medium/hard)
4. Время до конкуренции (быстро/средне/долго)
5. Тренд рынка (растущий/стабильный/падающий)
6. Рекомендация (войти/подождать/избегать)

Формат (ТОЛЬКО JSON):
{{
    "saturation_score": 65,
    "competitor_count": "many",
    "entry_difficulty": "medium",
    "competition_time": "medium",
    "market_trend": "growing",
    "recommendation": "enter"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "saturation_score": 50,
            "competitor_count": "some",
            "entry_difficulty": "medium",
            "competition_time": "medium",
            "market_trend": "growing",
            "recommendation": "enter",
        }
    
    async def generate_business_plan(self, name: str, description: str, category: str) -> Dict:
        """Генерация полного бизнес-плана"""
        system_prompt = """Ты - бизнес-консультант.
Создай полный бизнес-план для запуска аналога продукта."""
        
        prompt = f"""Создай бизнес-план для запуска аналога:

Оригинал: {name}
Категория: {category}
Описание: {description}

Создай:

1. Executive Summary (2-3 предложения)
2. Problem (какую проблему решает)
3. Solution (как решает)
4. Market Size (оценка TAM/SAM/SOM)
5. Business Model (как зарабатывать)
6. Go-to-Market (как привлекать)
7. Competitive Advantage (преимущества)
8. Financial Projections (месяц 1-12, пользователи и выручка)
9. Team (кто нужен)
10. Milestones (ключевые этапы)
11. Risks (риски и митигация)
12. Investment Needed (сколько нужно)

Формат (ТОЛЬКО JSON):
{{
    "executive_summary": "...",
    "problem": "...",
    "solution": "...",
    "market_size": {{"tam": "100M", "sam": "10M", "som": "1M"}},
    "business_model": "...",
    "go_to_market": "...",
    "competitive_advantage": "...",
    "financial_projections": [{{"month": 1, "users": 100, "revenue": 1000}}],
    "team": ["Founder", "Developer", "Marketing"],
    "milestones": ["MVP", "100 users", "1000 users"],
    "risks": ["Риск 1", "Риск 2"],
    "investment_needed": 50000
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "executive_summary": f"Аналог {name} для рынка России",
            "problem": "Нет аналога в РФ",
            "solution": "Локализованная версия",
            "market_size": {"tam": "100M", "sam": "10M", "som": "1M"},
            "business_model": "SaaS подписка",
            "go_to_market": "Telegram, Product Hunt",
            "competitive_advantage": "Локализация, цена",
            "financial_projections": [],
            "team": ["Founder"],
            "milestones": ["MVP"],
            "risks": ["Конкуренция"],
            "investment_needed": 30000,
        }
    
    async def forecast_trend(self, trend_name: str, trend_data: List[Dict]) -> Dict:
        """Прогнозирование тренда"""
        system_prompt = """Ты - аналитик трендов.
Сделай прогноз развития тренда на основе данных."""
        
        data_text = json.dumps(trend_data, ensure_ascii=False) if trend_data else "Нет исторических данных"
        
        prompt = f"""Сделай прогноз для тренда:

Тренд: {trend_name}
Исторические данные: {data_text}

Прогнозируй:

1. Вероятность роста (0-100)
2. Пик интереса (когда)
3. Длительность тренда (месяцев)
4. Категории которые вырастут (список)
5. Лучшее время для входа (сейчас/подождать/опоздали)
6. Рекомендуемые ниши (список)

Формат (ТОЛЬКО JSON):
{{
    "growth_probability": 85,
    "peak_interest": "2024-06",
    "duration_months": 18,
    "growing_categories": ["Категория 1", "Категория 2"],
    "entry_timing": "now",
    "recommended_niches": ["Ниша 1", "Ниша 2"]
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "growth_probability": 50,
            "peak_interest": "2024-12",
            "duration_months": 12,
            "growing_categories": [],
            "entry_timing": "now",
            "recommended_niches": [],
        }
    
    async def analyze_russia_barriers(self, name: str, description: str, category: str) -> Dict:
        """Анализ барьеров для входа в Россию"""
        system_prompt = """Ты - эксперт по рынку России.
Проанализируй почему продукт еще не появился в России."""
        
        prompt = f"""Проанализируй почему этот продукт еще не в России:

Название: {name}
Категория: {category}
Описание: {description}

Оцени барьеры (0-100):

1. Языковой барьер (0-100)
2. Регуляторный барьер (0-100)
3. Отсутствие спроса (0-100)
4. Сложность реализации (0-100)
5. Отсутствие инфраструктуры (0-100)
6. Конкуренция (0-100)
7. Низкая осведомленность (0-100)

Итог:
8. Общий барьер (0-100)
9. Можно ли преодолеть (yes/no)
10. Срок преодоления (недель)
11. Рекомендация (запускать/подождать/не запускать)
12. Почему никто не сделал (текст)

Формат (ТОЛЬКО JSON):
{{
    "language_barrier": 20,
    "regulatory_barrier": 30,
    "demand_barrier": 10,
    "implementation_barrier": 40,
    "infrastructure_barrier": 25,
    "competition_barrier": 15,
    "awareness_barrier": 35,
    "total_barrier": 30,
    "can_overcome": true,
    "overcome_weeks": 4,
    "recommendation": "launch",
    "why_not_done": "..."
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "language_barrier": 30,
            "regulatory_barrier": 40,
            "demand_barrier": 20,
            "implementation_barrier": 50,
            "infrastructure_barrier": 30,
            "competition_barrier": 20,
            "awareness_barrier": 40,
            "total_barrier": 35,
            "can_overcome": True,
            "overcome_weeks": 6,
            "recommendation": "launch",
            "why_not_done": "Рынок еще не созрел",
        }


    async def generate_opportunity_engine(self, name: str, description: str, category: str) -> Dict:
        """Opportunity Engine: генерация конкретных бизнес-идей для каждого проекта"""
        system_prompt = """Ты - эксперт по запуску стартапов.
Для каждого найденного продукта генерируй конкретные бизнес-идеи которые можно запустить прямо сейчас.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Для этого продукта сгенерируй 5 конкретных бизнес-идей которые можно запустить:

Продукт: {name}
Категория: {category}
Описание: {description}

Для каждой идеи укажи:
1. Тип (SaaS / Telegram бот / Мобильное приложение / Chrome Extension / MCP Server)
2. Название на русском
3. Что делает (1-2 предложения)
4. Целевая аудитория
5. Монетизация (конкретные цены в ₽)
6. Срок MVP (недели)
7. Бюджет запуска (₽)
8. Вероятность успеха (0-100)
9. Первые 100 пользователей (где искать)

Формат (ТОЛЬКО JSON):
{{
    "ideas": [
        {{
            "type": "Telegram бот",
            "name": "АИ Психолог",
            "description": "Бот для анонимной психологической поддержки через AI",
            "target_audience": "Молодежь 18-35 лет",
            "monetization": "Подписка 299 ₽/мес, 5 бесплатных сессий",
            "mvp_weeks": 2,
            "budget_rub": 30000,
            "success_probability": 75,
            "first_users": "Telegram каналы по психологии, Reddit"
        }}
    ]
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.7)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "ideas": [
                {
                    "type": "Telegram бот",
                    "name": f"{name} Бот",
                    "description": f"Telegram бот на основе {name}",
                    "target_audience": "Широкая аудитория",
                    "monetization": "Подписка 299 ₽/мес",
                    "mvp_weeks": 2,
                    "budget_rub": 30000,
                    "success_probability": 60,
                    "first_users": "Telegram каналы"
                },
                {
                    "type": "SaaS",
                    "name": f"{name} Pro",
                    "description": f"SaaS версия {name} для бизнеса",
                    "target_audience": "Малый и средний бизнес",
                    "monetization": "Подписка 990 ₽/мес",
                    "mvp_weeks": 6,
                    "budget_rub": 100000,
                    "success_probability": 55,
                    "first_users": "LinkedIn, Product Hunt"
                }
            ]
        }
    
    async def predict_revenue(self, name: str, description: str, category: str, monetization_type: str) -> Dict:
        """Revenue Predictor: прогноз выручки для 100/1000/10000 пользователей"""
        system_prompt = """Ты - финансовый аналитик стартапов.
Дай реалистичный прогноз выручки на основе типа монетизации и категории продукта.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Дай прогноз выручки для этого продукта:

Продукт: {name}
Категория: {category}
Описание: {description}
Тип монетизации: {monetization_type}

Рассчитай для 3 сценариев:
1. 100 пользователей
2. 1000 пользователей
3. 10000 пользователей

Для каждого сценария:
- Ежемесячная выручка (₽)
- Годовая выручка (₽)
- Средний чек (₽)
- Конверсия в платных (%)
- Churn rate (%)
- Срок достижения (месяцев)

Формат (ТОЛЬКО JSON):
{{
    "scenarios": {{
        "100_users": {{
            "monthly_revenue_rub": 15000,
            "annual_revenue_rub": 180000,
            "avg_check_rub": 499,
            "paid_conversion": 30,
            "churn_rate": 10,
            "months_to_reach": 3
        }},
        "1000_users": {{
            "monthly_revenue_rub": 150000,
            "annual_revenue_rub": 1800000,
            "avg_check_rub": 499,
            "paid_conversion": 30,
            "churn_rate": 8,
            "months_to_reach": 9
        }},
        "10000_users": {{
            "monthly_revenue_rub": 1500000,
            "annual_revenue_rub": 18000000,
            "avg_check_rub": 499,
            "paid_conversion": 30,
            "churn_rate": 5,
            "months_to_reach": 24
        }}
    }},
    "best_monetization": "Freemium с подпиской 499 ₽/мес",
    "revenue_model": "SaaS подписка",
    "break_even_users": 50,
    "notes": "Реалистичный прогноз при активном маркетинге"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "scenarios": {
                "100_users": {
                    "monthly_revenue_rub": 15000,
                    "annual_revenue_rub": 180000,
                    "avg_check_rub": 499,
                    "paid_conversion": 30,
                    "churn_rate": 10,
                    "months_to_reach": 3
                },
                "1000_users": {
                    "monthly_revenue_rub": 150000,
                    "annual_revenue_rub": 1800000,
                    "avg_check_rub": 499,
                    "paid_conversion": 30,
                    "churn_rate": 8,
                    "months_to_reach": 9
                },
                "10000_users": {
                    "monthly_revenue_rub": 1500000,
                    "annual_revenue_rub": 18000000,
                    "avg_check_rub": 499,
                    "paid_conversion": 30,
                    "churn_rate": 5,
                    "months_to_reach": 24
                }
            },
            "best_monetization": "Freemium с подпиской 499 ₽/мес",
            "revenue_model": "SaaS подписка",
            "break_even_users": 50,
            "notes": "Базовый прогноз"
        }
    
    async def generate_russia_launch(self, name: str, description: str, category: str) -> Dict:
        """Russia Launch Generator: полный готовый бизнес для запуска в России"""
        system_prompt = """Ты - эксперт по запуску стартапов в России.
Создай полный готовый бизнес-пакет для запуска аналога продукта в России.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Создай полный готовый бизнес для запуска аналога в России:

Оригинал: {name}
Категория: {category}
Описание: {description}

Создай:
1. Название на русском (3 варианта, звучащих по-русски)
2. УТП (уникальное торговое предложение, 1 предложение)
3. Слоган (короткий, запоминающийся)
4. Описание лендинга (заголовок + 3 блока)
5. MVP план (5 конкретных функций)
6. Технический стек (конкретные технологии)
7. Монетизация (тарифы с ценами в ₽)
8. Маркетинг (5 каналов привлечения)
9. Конкуренты в РФ (если есть)
10. Бюджет запуска (₽)
11. Срок до первых денег (недели)
12. Команда (кто нужен)

Формат (ТОЛЬКО JSON):
{{
    "names": ["Название 1", "Название 2", "Название 3"],
    "utp": "Единственный сервис который...",
    "slogan": "Короткий слоган",
    "landing": {{
        "headline": "Заголовок лендинга",
        "blocks": ["Блок 1", "Блок 2", "Блок 3"]
    }},
    "mvp_features": ["Функция 1", "Функция 2", "Функция 3", "Функция 4", "Функция 5"],
    "tech_stack": {{
        "frontend": "React / Next.js",
        "backend": "Python FastAPI",
        "database": "PostgreSQL",
        "ai": "Ollama llama3.2",
        "hosting": "Timeweb / Selectel",
        "payments": "ЮKassa / Robokassa"
    }},
    "pricing": [
        {{"name": "Бесплатный", "price": 0, "features": ["Функция 1"]}},
        {{"name": "Про", "price": 499, "features": ["Функция 1", "Функция 2"]}},
        {{"name": "Бизнес", "price": 1990, "features": ["Всё включено"]}}
    ],
    "marketing_channels": ["Telegram каналы", "ВКонтакте", "Хабр", "Product Hunt RU", "Пикабу"],
    "russia_competitors": [],
    "launch_budget_rub": 50000,
    "weeks_to_revenue": 4,
    "team_needed": ["Разработчик", "Маркетолог"]
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.5)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "names": [f"{name} РФ", f"{name} Про", f"{name} Онлайн"],
            "utp": f"Первый российский аналог {name}",
            "slogan": "Умнее. Быстрее. По-русски.",
            "landing": {
                "headline": f"Российский аналог {name}",
                "blocks": ["Простой интерфейс", "Интеграция с российскими сервисами", "Поддержка 24/7"]
            },
            "mvp_features": ["Регистрация", "Основной функционал", "Оплата", "Личный кабинет", "Поддержка"],
            "tech_stack": {
                "frontend": "React",
                "backend": "Python FastAPI",
                "database": "PostgreSQL",
                "ai": "Ollama",
                "hosting": "Timeweb",
                "payments": "ЮKassa"
            },
            "pricing": [
                {"name": "Бесплатный", "price": 0, "features": ["Базовый функционал"]},
                {"name": "Про", "price": 499, "features": ["Всё включено"]}
            ],
            "marketing_channels": ["Telegram", "ВКонтакте", "Хабр"],
            "russia_competitors": [],
            "launch_budget_rub": 50000,
            "weeks_to_revenue": 4,
            "team_needed": ["Разработчик"]
        }
    
    async def analyze_cis_opportunity(self, name: str, description: str, category: str) -> Dict:
        """СНГ Opportunity Score: оценка аналогов в Казахстане, Беларуси, Узбекистане"""
        system_prompt = """Ты - эксперт по рынкам СНГ.
Оцени наличие аналогов продукта в странах СНГ.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Оцени наличие аналогов этого продукта в странах СНГ:

Продукт: {name}
Категория: {category}
Описание: {description}

Оцени для каждой страны:
1. Россия - есть ли аналог (yes/no/weak)
2. Казахстан - есть ли аналог (yes/no/weak)
3. Беларусь - есть ли аналог (yes/no/weak)
4. Узбекистан - есть ли аналог (yes/no/weak)
5. Украина - есть ли аналог (yes/no/weak)

Для каждой страны:
- Название аналога (если есть)
- Сила конкурента (strong/weak/none)
- Opportunity Score (0-100)
- Рекомендация (launch/wait/avoid)

Формат (ТОЛЬКО JSON):
{{
    "countries": {{
        "russia": {{
            "has_analog": false,
            "analog_name": null,
            "competitor_strength": "none",
            "opportunity_score": 85,
            "recommendation": "launch"
        }},
        "kazakhstan": {{
            "has_analog": false,
            "analog_name": null,
            "competitor_strength": "none",
            "opportunity_score": 80,
            "recommendation": "launch"
        }},
        "belarus": {{
            "has_analog": false,
            "analog_name": null,
            "competitor_strength": "none",
            "opportunity_score": 75,
            "recommendation": "launch"
        }},
        "uzbekistan": {{
            "has_analog": false,
            "analog_name": null,
            "competitor_strength": "none",
            "opportunity_score": 70,
            "recommendation": "launch"
        }},
        "ukraine": {{
            "has_analog": false,
            "analog_name": null,
            "competitor_strength": "none",
            "opportunity_score": 60,
            "recommendation": "wait"
        }}
    }},
    "best_market": "russia",
    "total_cis_score": 78,
    "cis_recommendation": "Отличная возможность для запуска в СНГ"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "countries": {
                "russia": {"has_analog": False, "analog_name": None, "competitor_strength": "none", "opportunity_score": 70, "recommendation": "launch"},
                "kazakhstan": {"has_analog": False, "analog_name": None, "competitor_strength": "none", "opportunity_score": 65, "recommendation": "launch"},
                "belarus": {"has_analog": False, "analog_name": None, "competitor_strength": "none", "opportunity_score": 60, "recommendation": "launch"},
                "uzbekistan": {"has_analog": False, "analog_name": None, "competitor_strength": "none", "opportunity_score": 55, "recommendation": "wait"},
                "ukraine": {"has_analog": False, "analog_name": None, "competitor_strength": "none", "opportunity_score": 50, "recommendation": "wait"}
            },
            "best_market": "russia",
            "total_cis_score": 60,
            "cis_recommendation": "Умеренная возможность для СНГ"
        }
    
    async def detect_app_clone_potential(self, name: str, description: str, category: str, app_store_url: str = "") -> Dict:
        """App Clone Detector: разбор приложения на экраны, функции, оценка MVP"""
        system_prompt = """Ты - мобильный разработчик и продуктовый аналитик.
Разбери приложение на составные части и оцени сложность клонирования.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Разбери это приложение и оцени возможность клонирования:

Приложение: {name}
Категория: {category}
Описание: {description}
URL: {app_store_url}

Определи:
1. Основные экраны (список всех экранов)
2. Ключевые функции (список)
3. AI компоненты (если есть)
4. Интеграции (какие API/сервисы)
5. Монетизация (как зарабатывает)
6. Сложность клонирования (0-100)
7. Срок MVP (недели)
8. Бюджет MVP (₽)
9. Что можно улучшить (список)
10. Уникальные фичи которые сложно скопировать

Формат (ТОЛЬКО JSON):
{{
    "screens": ["Онбординг", "Главный экран", "Профиль", "Настройки"],
    "features": ["Функция 1", "Функция 2"],
    "ai_components": ["Чатбот", "Рекомендации"],
    "integrations": ["Stripe", "Firebase"],
    "monetization": "Freemium + подписка",
    "clone_complexity": 45,
    "mvp_weeks": 3,
    "mvp_budget_rub": 80000,
    "improvements": ["Добавить русский язык", "Интеграция с ВКонтакте"],
    "hard_to_copy": ["Алгоритм рекомендаций", "База данных контента"],
    "clone_verdict": "Можно сделать MVP за 3 недели"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "screens": ["Главный экран", "Профиль", "Настройки"],
            "features": ["Основной функционал"],
            "ai_components": [],
            "integrations": [],
            "monetization": "Freemium",
            "clone_complexity": 50,
            "mvp_weeks": 4,
            "mvp_budget_rub": 100000,
            "improvements": ["Локализация на русский"],
            "hard_to_copy": [],
            "clone_verdict": "Средняя сложность клонирования"
        }
    
    async def trend_to_product(self, trend_name: str, trend_description: str, trend_growth: float) -> Dict:
        """Trend-to-Product: автоматическая генерация продуктовых идей из тренда"""
        system_prompt = """Ты - продуктовый стратег.
На основе тренда придумай конкретные продукты которые можно запустить прямо сейчас.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""На основе этого тренда придумай 5 конкретных продуктов:

Тренд: {trend_name}
Описание: {trend_description}
Рост: +{trend_growth}%

Для каждого продукта:
1. Название
2. Тип (SaaS / Telegram бот / Мобильное приложение / Chrome Extension)
3. Описание (2-3 предложения)
4. Целевая аудитория
5. Монетизация (цены в ₽)
6. Срок MVP (недели)
7. Почему сейчас (связь с трендом)
8. Вероятность успеха (0-100)

Формат (ТОЛЬКО JSON):
{{
    "products": [
        {{
            "name": "Название продукта",
            "type": "Telegram бот",
            "description": "Описание продукта",
            "target_audience": "Кому нужен",
            "monetization": "Подписка 299 ₽/мес",
            "mvp_weeks": 2,
            "why_now": "Тренд растет на 300%, конкурентов нет",
            "success_probability": 75
        }}
    ],
    "trend_window": "Тренд будет актуален 12-18 месяцев",
    "best_product_index": 0,
    "market_size_estimate": "Рынок ~500M ₽/год"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.8)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "products": [
                {
                    "name": f"{trend_name} App",
                    "type": "Telegram бот",
                    "description": f"Продукт на основе тренда {trend_name}",
                    "target_audience": "Широкая аудитория",
                    "monetization": "Подписка 299 ₽/мес",
                    "mvp_weeks": 3,
                    "why_now": f"Тренд растет на {trend_growth}%",
                    "success_probability": 60
                }
            ],
            "trend_window": "Тренд будет актуален 12 месяцев",
            "best_product_index": 0,
            "market_size_estimate": "Рынок ~100M ₽/год"
        }
    
    async def detect_acquisition_signal(self, name: str, description: str, category: str, investment_amount: float = 0) -> Dict:
        """Acquisition Detector: определяет сигналы интереса крупных компаний к нише"""
        system_prompt = """Ты - M&A аналитик.
Определи вероятность поглощения стартапа крупными компаниями.
Отвечай ТОЛЬКО в формате JSON без Markdown."""
        
        prompt = f"""Оцени вероятность поглощения этого стартапа:

Стартап: {name}
Категория: {category}
Описание: {description}
Инвестиции: ${investment_amount:,.0f}

Оцени:
1. Вероятность поглощения (0-100)
2. Кто может купить (список компаний)
3. Почему интересен (причины)
4. Оценочная стоимость ($)
5. Сигналы интереса (что указывает на интерес)
6. Временной горизонт (когда может произойти)
7. Что это значит для рынка

Формат (ТОЛЬКО JSON):
{{
    "acquisition_probability": 65,
    "potential_buyers": ["Google", "Microsoft", "Яндекс"],
    "reasons": ["Уникальная технология", "Большая база пользователей"],
    "estimated_value_usd": 50000000,
    "signals": ["Крупные инвестиции", "Партнерства с BigTech"],
    "timeline": "12-24 месяца",
    "market_impact": "Поглощение подтвердит ценность ниши",
    "opportunity_for_clones": "Сейчас лучшее время для запуска аналога"
}}"""
        
        response = await self.generate(prompt, system_prompt, temperature=0.3)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return {
            "acquisition_probability": 30,
            "potential_buyers": [],
            "reasons": [],
            "estimated_value_usd": 0,
            "signals": [],
            "timeline": "Неизвестно",
            "market_impact": "Нет явных сигналов поглощения",
            "opportunity_for_clones": "Рынок открыт для новых игроков"
        }


# Singleton
ollama_client = OllamaClient()