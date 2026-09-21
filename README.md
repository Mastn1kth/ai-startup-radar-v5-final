# AI Startup Radar 2026

Прототип платформы для исследования стартапов и технологических продуктов.
Она объединяет сбор данных, поиск, оценку, отслеживание трендов и dashboard для
анализа возможностей. Репозиторий демонстрирует архитектуру и локальный запуск;
это не инвестиционная рекомендация и не развёрнутый коммерческий сервис.

## Архитектура

- **Backend**: FastAPI + SQLAlchemy + Celery
- **Database**: PostgreSQL + Qdrant (vector DB)
- **Cache/Queue**: Redis
- **AI**: Ollama (Qwen 2.5 14B)
- **Frontend**: React + Tailwind CSS + Recharts
- **Infrastructure**: Docker Compose

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone <repo>
cd ai-startup-radar
cp .env.example .env
# Отредактируйте .env - добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHANNEL_ID
```

### 2. Запуск

```bash
docker-compose up -d
```

### 3. Установка модели Ollama

```bash
docker-compose exec ollama ollama pull qwen2.5:14b
```

### 4. Доступ

- Dashboard: http://localhost:3000
- API: http://localhost:8000
- Flower (Celery): http://localhost:5555

## API Endpoints

### Projects
- `GET /api/projects` - Список проектов с фильтрами
- `GET /api/projects/{id}` - Детали проекта
- `GET /api/projects/featured` - Топ проекты
- `GET /api/projects/russia-opportunities` - Возможности для РФ

### Trends
- `GET /api/trends` - Тренды
- `GET /api/trends/exploding` - Взрывные тренды

### Dashboard
- `GET /api/dashboard/stats` - Статистика
- `GET /api/dashboard/top-categories` - Топ категории

### Watchlist
- `POST /api/watchlist/{project_id}` - Добавить в watchlist
- `GET /api/watchlist` - Список watchlist

### Search
- `GET /api/search?q={query}` - Поиск проектов

### Reports
- `GET /api/reports/daily` - Ежедневные отчеты

## Система скоринга

### Copy Score (0-100)
Насколько легко повторить продукт. Учитывает сложность, AI, лицензии, инфраструктуру.

### Money Score (0-100)
Потенциал заработка. Учитывает инвестиции, монетизацию, размер рынка.

### Viral Score (0-100)
Потенциал вирусности. Учитывает метрики, категорию, freemium.

### Startup Score (0-100)
Главный рейтинг. Комплексная оценка всех факторов.

### Russia Opportunity Score (0-100)
Возможность запуска в России. Учитывает аналоги, конкуренцию, локализацию.

## AI Gap Detector

- 🟢 **Green** - Аналогов нет, отличная возможность
- 🟡 **Yellow** - Есть слабые аналоги, можно конкурировать
- 🔴 **Red** - Рынок занят, сложно войти

## Детекторы

### Trend Explosion Detector
Выявляет тренды с ростом >100% и создает алерты.

### GitHub Explosion Detector
Обнаруживает проекты с >1000 stars за 7 дней.

### Search Explosion Detector
Отслеживает Google Trends, Reddit, Twitter, YouTube.

### Investment Detector
Выделяет проекты после инвестиций.

### Startup Graveyard
Отслеживает закрытые стартапы и рынки с высокой смертностью.

## Telegram Bot

Автоматическая публикация:
- Топ-5 проектов дня (score > 70)
- Взрывные тренды
- Ежедневный дайджест

Формат публикации включает:
- Название, категория, описание
- Все скоры (Startup, Russia, Money, Viral, Copy)
- Статус рынка РФ
- Метрики (stars, likes)
- Ссылки

## Расписание задач (Celery Beat)

- **Каждые 2 часа**: Product Hunt, GitHub Trending
- **Каждый час**: Hacker News
- **Каждые 4 часа**: Hugging Face
- **Каждые 30 минут**: AI анализ новых проектов
- **Каждый час**: Расчет скоров
- **Каждые 24 часа**: Генерация отчетов, отправка в Telegram
- **Каждый час**: Детекторы трендов и GitHub

## Разработка

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Celery
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
celery -A app.core.celery_app beat --loglevel=info
```

## Переменные окружения

```env
DATABASE_URL=postgresql+asyncpg://radar:radar_secret_2026@localhost:5432/ai_startup_radar
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
SECRET_KEY=your-secret-key
```

## Лицензия

MIT License
