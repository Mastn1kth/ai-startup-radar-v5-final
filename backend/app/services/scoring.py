import math
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from app.models import Project


class ScoringService:
    """Сервис для расчета всех скоров проектов"""
    
    @staticmethod
    def calculate_copy_score(project: Project) -> int:
        """
        Copy Score: насколько легко повторить продукт
        Учитывает: сложность, AI, лицензии, инфраструктуру, стоимость
        """
        score = 50  # Базовая оценка
        
        # Чем меньше сложность реализации, тем выше copy score
        if project.implementation_complexity:
            score += (100 - project.implementation_complexity) * 0.3
        
        # GitHub stars - если много, значит сложнее повторить
        if project.github_stars:
            if project.github_stars > 10000:
                score -= 20
            elif project.github_stars > 1000:
                score -= 10
            elif project.github_stars > 100:
                score -= 5
        
        # AI продукты сложнее копировать
        if project.category in ['ai_models', 'ai_agents']:
            score -= 15
        
        # Open source легче копировать
        if project.category == 'open_source':
            score += 15
        
        # SaaS обычно легче копировать
        if project.category == 'ai_saas':
            score += 10
        
        # Монетизация через подписку - сложнее
        if project.has_subscription:
            score -= 5
        
        # Freemium - легче запустить
        if project.has_freemium:
            score += 5
        
        return max(0, min(100, int(score)))
    
    @staticmethod
    def calculate_money_score(project: Project) -> int:
        """
        Money Score: потенциал заработка
        """
        score = 50
        
        # Инвестиции - хороший индикатор
        if project.investment_amount:
            if project.investment_amount > 10000000:  # > $10M
                score += 25
            elif project.investment_amount > 1000000:  # > $1M
                score += 15
            elif project.investment_amount > 100000:  # > $100K
                score += 10
        
        # Монетизация
        if project.has_subscription:
            score += 15
        if project.has_freemium:
            score += 10
        
        # Потенциал заработка от AI
        if project.money_potential:
            score += project.money_potential * 0.2
        
        # Размер рынка
        market_size_scores = {
            'huge': 20,
            'large': 15,
            'medium': 10,
            'small': 5,
        }
        score += market_size_scores.get(project.market_size, 10)
        
        # GitHub stars - индикатор спроса
        if project.github_stars:
            if project.github_stars > 5000:
                score += 15
            elif project.github_stars > 1000:
                score += 10
            elif project.github_stars > 100:
                score += 5
        
        # Likes/votes
        if project.likes:
            if project.likes > 1000:
                score += 10
            elif project.likes > 100:
                score += 5
        
        # Сложность реализации - обратная зависимость
        if project.implementation_complexity:
            score += (100 - project.implementation_complexity) * 0.1
        
        return max(0, min(100, int(score)))
    
    @staticmethod
    def calculate_viral_score(project: Project) -> int:
        """
        Viral Score: потенциал вирусности
        """
        score = 30  # Базовая оценка
        
        # Потенциал вирусности от AI
        if project.viral_potential:
            score += project.viral_potential * 0.3
        
        # GitHub stars - вирусность в dev community
        if project.github_stars:
            if project.github_stars > 10000:
                score += 25
            elif project.github_stars > 5000:
                score += 20
            elif project.github_stars > 1000:
                score += 15
            elif project.github_stars > 100:
                score += 10
        
        # Likes/votes
        if project.likes:
            if project.likes > 5000:
                score += 20
            elif project.likes > 1000:
                score += 15
            elif project.likes > 100:
                score += 10
        
        # Рост
        if project.growth_potential:
            score += project.growth_potential * 0.2
        
        # Категории с высокой вирусностью
        viral_categories = ['chrome_extensions', 'telegram', 'ai_saas']
        if project.category in viral_categories:
            score += 15
        
        # Freemium - вирусная модель
        if project.has_freemium:
            score += 10
        
        # Мобильные приложения - вирусные
        if project.category == 'mobile_apps':
            score += 10
        
        return max(0, min(100, int(score)))
    
    @staticmethod
    def calculate_startup_score(project: Project) -> int:
        """
        Startup Score: главный рейтинг
        Учитывает: рост, инвестиции, тренды, спрос, конкуренцию, монетизацию, вирусность
        """
        score = 40  # Базовая оценка
        
        # Рост
        if project.growth_potential:
            score += project.growth_potential * 0.15
        
        # Инвестиции
        if project.investment_amount:
            if project.investment_amount > 10000000:
                score += 20
            elif project.investment_amount > 1000000:
                score += 15
            elif project.investment_amount > 100000:
                score += 10
        
        # GitHub метрики
        if project.github_stars:
            if project.github_stars > 10000:
                score += 15
            elif project.github_stars > 1000:
                score += 10
            elif project.github_stars > 100:
                score += 5
        
        # Лайки/голоса
        if project.likes:
            if project.likes > 1000:
                score += 10
            elif project.likes > 100:
                score += 5
        
        # Монетизация
        if project.has_subscription:
            score += 8
        if project.has_freemium:
            score += 5
        
        # Потенциал масштабирования
        if project.scaling_potential:
            score += project.scaling_potential * 0.1
        
        # Конкуренция - обратная зависимость
        if project.competition_level:
            score += (100 - project.competition_level) * 0.1
        
        # Вероятность провала - обратная зависимость
        if project.failure_probability:
            score += (100 - project.failure_probability) * 0.15
        
        # Founder history
        if project.founder_history_score:
            score += project.founder_history_score * 0.1
        
        # Russia opportunity - бонус
        if project.russia_opportunity_score and project.russia_opportunity_score > 70:
            score += 10
        
        return max(0, min(100, int(score)))
    
    @staticmethod
    def calculate_coolness_score(project: Project) -> int:
        """
        Coolness Score: насколько проект "крутой" и интересный
        Композитный скор который учитывает все факторы и ранжирует проекты по привлекательности
        """
        score = 30  # Базовая оценка
        
        # Startup Score - основной компонент (вес 30%)
        startup_score = project.startup_score or 50
        score += startup_score * 0.30
        
        # Viral Score - вирусность (вес 20%)
        viral_score = project.viral_score or 50
        score += viral_score * 0.20
        
        # Money Score - деньги (вес 15%)
        money_score = project.money_score or 50
        score += money_score * 0.15
        
        # Copy Score - легкость копирования (вес 10%)
        copy_score = project.copy_score or 50
        score += copy_score * 0.10
        
        # Russia Opportunity - возможность в России (вес 15%)
        russia_score = project.russia_opportunity_score or 50
        score += russia_score * 0.15
        
        # Market Saturation - обратная зависимость (вес 10%)
        saturation = project.market_saturation_score or 50
        score += (100 - saturation) * 0.10
        
        # Бонусы за уникальные характеристики
        # Много GitHub stars = крутой проект
        if project.github_stars:
            if project.github_stars > 10000:
                score += 5
            elif project.github_stars > 5000:
                score += 3
        
        # Много лайков = крутой проект
        if project.likes:
            if project.likes > 10000:
                score += 5
            elif project.likes > 5000:
                score += 3
        
        # Большие инвестиции = крутой проект
        if project.investment_amount:
            if project.investment_amount > 10000000:
                score += 5
            elif project.investment_amount > 1000000:
                score += 3
        
        # Свежий проект (менее 7 дней) = бонус
        if project.discovered_at:
            days_since = (datetime.utcnow() - project.discovered_at).days
            if days_since <= 7:
                score += 5  # Новый проект
            elif days_since <= 30:
                score += 2  # Относительно свежий
        
        # AI Gap Detector зеленый статус = бонус
        if project.gap_status == 'green':
            score += 5
        elif project.gap_status == 'yellow':
            score += 2
        
        # Можно запустить одному = бонус
        if project.solo_founder_possible:
            score += 3
        
        # Быстрый MVP = бонус
        if project.mvp_timeline:
            if 'week' in project.mvp_timeline.lower() or 'недел' in project.mvp_timeline.lower():
                score += 3
        
        return max(0, min(100, int(score)))
    
    @staticmethod
    def calculate_russia_opportunity_score(project: Project) -> int:
        """
        Russia Opportunity Score: возможность запуска в России
        """
        score = 50  # Базовая оценка
        
        # Если нет аналогов - большой плюс
        if not project.has_russia_analog and not project.has_cis_analog:
            score += 30
        elif not project.has_russia_analog:
            score += 15
        
        # Если есть слабый конкурент - можно захватить рынок
        if project.has_weak_competitor and not project.has_strong_competitor:
            score += 15
        
        # Если можно локализовать
        if project.can_localize:
            score += 10
        
        # Если можно быстро запустить
        if project.can_quick_launch:
            score += 10
        
        # Юридические ограничения - минус
        if project.legal_restrictions:
            score -= 25
        
        # Сложность реализации - чем проще, тем лучше для России
        if project.implementation_complexity:
            score += (100 - project.implementation_complexity) * 0.1
        
        # Категории с хорошим потенциалом в России
        good_categories = ['ai_saas', 'telegram', 'chrome_extensions', 'open_source']
        if project.category in good_categories:
            score += 5
        
        # AI модели - сложнее из-за санкций
        if project.category == 'ai_models':
            score -= 10
        
        return max(0, min(100, int(score)))
    
    @classmethod
    def calculate_all_scores(cls, project: Project) -> Dict[str, int]:
        """Расчет всех скоров сразу"""
        return {
            'copy_score': cls.calculate_copy_score(project),
            'money_score': cls.calculate_money_score(project),
            'viral_score': cls.calculate_viral_score(project),
            'startup_score': cls.calculate_startup_score(project),
            'russia_opportunity_score': cls.calculate_russia_opportunity_score(project),
            'coolness_score': cls.calculate_coolness_score(project),
        }
    
    @staticmethod
    def determine_gap_status(project: Project) -> str:
        """
        AI Gap Detector: определение статуса рынка
        🟢 Аналогов нет
        🟡 Есть слабые аналоги
        🔴 Рынок занят
        """
        if not project.has_russia_analog and not project.has_cis_analog:
            if not project.has_strong_competitor:
                return 'green'
        
        if project.has_weak_competitor and not project.has_strong_competitor:
            return 'yellow'
        
        if project.has_strong_competitor:
            return 'red'
        
        if project.russia_opportunity_score and project.russia_opportunity_score > 70:
            return 'green'
        elif project.russia_opportunity_score and project.russia_opportunity_score > 40:
            return 'yellow'
        
        return 'yellow'
    
    @staticmethod
    def estimate_budget(project: Project) -> str:
        """Оценка бюджета запуска аналога"""
        complexity = project.implementation_complexity or 50
        
        if complexity < 30:
            return "$1K - $5K"
        elif complexity < 50:
            return "$5K - $20K"
        elif complexity < 70:
            return "$20K - $50K"
        elif complexity < 90:
            return "$50K - $100K"
        else:
            return "$100K+"
    
    @staticmethod
    def estimate_timeline(project: Project) -> str:
        """Оценка срока разработки MVP"""
        if project.mvp_timeline:
            return project.mvp_timeline
        
        complexity = project.implementation_complexity or 50
        
        if complexity < 30:
            return "2-4 недели"
        elif complexity < 50:
            return "1-2 месяца"
        elif complexity < 70:
            return "2-4 месяца"
        elif complexity < 90:
            return "4-6 месяцев"
        else:
            return "6-12 месяцев"
    
    @staticmethod
    def calculate_success_probability(project: Project) -> int:
        """Вероятность успеха (обратная failure_probability)"""
        if project.failure_probability:
            return 100 - project.failure_probability
        return 50
    
    @staticmethod
    def calculate_market_saturation_score(project: Project) -> int:
        """
        Market Saturation Score: насыщенность рынка (0-100)
        0 = пустой рынок, 100 = перенасыщен
        """
        score = 30  # Базовая оценка
        
        # Конкуренция
        if project.competition_level:
            score += project.competition_level * 0.4
        
        # Аналоги в России
        if project.has_russia_analog:
            score += 20
        if project.has_cis_analog:
            score += 10
        
        # Сильные конкуренты
        if project.has_strong_competitor:
            score += 25
        elif project.has_weak_competitor:
            score += 10
        
        # GitHub stars - много проектов = насыщенный рынок
        if project.github_stars:
            if project.github_stars > 10000:
                score += 15
            elif project.github_stars > 5000:
                score += 10
            elif project.github_stars > 1000:
                score += 5
        
        # Категории с высокой насыщенностью
        saturated_categories = ['ai_saas', 'open_source']
        if project.category in saturated_categories:
            score += 10
        
        # Легко копировать = насыщенный рынок
        if project.copy_score and project.copy_score > 70:
            score += 10
        
        return max(0, min(100, int(score)))
    
    @staticmethod
    def get_rotation_priority(project: Project) -> int:
        """
        Определение приоритета ротации проекта
        Чем выше приоритет, тем раньше проект будет заменен при достижении лимитов
        """
        priority = 50  # Базовый приоритет
        
        # Низкий Coolness Score = высокий приоритет ротации (заменить первым)
        coolness = project.coolness_score or 50
        priority += (100 - coolness) * 0.4
        
        # Старый проект = высокий приоритет ротации
        if project.discovered_at:
            days_since = (datetime.utcnow() - project.discovered_at).days
            if days_since > 90:
                priority += 20
            elif days_since > 60:
                priority += 10
            elif days_since > 30:
                priority += 5
        
        # Низкая активность = высокий приоритет
        if project.last_updated_at:
            days_since_update = (datetime.utcnow() - project.last_updated_at).days
            if days_since_update > 30:
                priority += 15
        
        # Дублированный проект = высокий приоритет
        if project.is_duplicate:
            priority += 25
        
        # Низкий Startup Score = высокий приоритет
        startup = project.startup_score or 50
        priority += (100 - startup) * 0.3
        
        # Низкая вирусность = высокий приоритет
        viral = project.viral_score or 50
        priority += (100 - viral) * 0.2
        
        # Проекты с красным gap_status = высокий приоритет (рынок занят)
        if project.gap_status == 'red':
            priority += 10
        
        return max(0, min(100, int(priority)))
    
    @staticmethod
    def should_rotate(project: Project, total_projects: int, max_projects: int = 1000) -> bool:
        """
        Определить, нужно ли ротировать проект при достижении лимита
        """
        if total_projects < max_projects:
            return False
        
        # При достижении лимита ротируем проекты с высоким приоритетом
        rotation_priority = ScoringService.get_rotation_priority(project)
        
        # Ротируем если приоритет > 70 (топ 30% проектов по приоритету ротации)
        return rotation_priority > 70
    
    @staticmethod
    def rank_projects(projects: List[Project], sort_by: str = "coolness_score") -> List[Project]:
        """
        Ранжирование проектов по выбранному скору
        По умолчанию по Coolness Score (крутости)
        """
        if sort_by == "coolness_score":
            return sorted(projects, key=lambda p: p.coolness_score or 0, reverse=True)
        elif sort_by == "startup_score":
            return sorted(projects, key=lambda p: p.startup_score or 0, reverse=True)
        elif sort_by == "viral_score":
            return sorted(projects, key=lambda p: p.viral_score or 0, reverse=True)
        elif sort_by == "money_score":
            return sorted(projects, key=lambda p: p.money_score or 0, reverse=True)
        elif sort_by == "russia_opportunity_score":
            return sorted(projects, key=lambda p: p.russia_opportunity_score or 0, reverse=True)
        elif sort_by == "copy_score":
            return sorted(projects, key=lambda p: p.copy_score or 0, reverse=True)
        elif sort_by == "rotation_priority":
            return sorted(projects, key=lambda p: ScoringService.get_rotation_priority(p), reverse=True)
        else:
            return sorted(projects, key=lambda p: p.coolness_score or 0, reverse=True)
    
    @staticmethod
    def get_top_projects(projects: List[Project], limit: int = 50, sort_by: str = "coolness_score") -> List[Project]:
        """
        Получение топ проектов по ранжированию
        """
        ranked = ScoringService.rank_projects(projects, sort_by)
        return ranked[:limit]
    
    @staticmethod
    def auto_rotate_projects(projects: List[Project], max_projects: int = 1000) -> tuple[List[Project], List[Project]]:
        """
        Автоматическая ротация проектов при достижении лимита
        Возвращает: (проекты_для_сохранения, проекты_для_ротации)
        """
        if len(projects) <= max_projects:
            return projects, []
        
        # Ранжируем по приоритету ротации (от высокого к низкому)
        rotation_ranked = ScoringService.rank_projects(projects, "rotation_priority")
        
        # Определяем сколько проектов нужно ротировать
        to_rotate_count = len(projects) - max_projects
        
        # Проекты для ротации - те у кого highest rotation priority
        projects_to_rotate = rotation_ranked[:to_rotate_count]
        
        # Проекты для сохранения - остальные
        projects_to_keep = rotation_ranked[to_rotate_count:]
        
        return projects_to_keep, projects_to_rotate


# Singleton
scoring_service = ScoringService()