#!/bin/bash
# AI Startup Radar - Запуск на Linux/Mac

clear
echo "=========================================="
echo "   AI Startup Radar - Запуск системы"
echo "=========================================="
echo ""

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "[ОШИБКА] Docker не найден!"
    echo "Установи Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Проверка .env
if [ ! -f .env ]; then
    echo "[ВНИМАНИЕ] Файл .env не найден!"
    echo "Копирую .env.example -> .env"
    cp .env.example .env
    echo ""
    echo "[ВАЖНО] Открой файл .env и вставь свои токены:"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - TELEGRAM_CHANNEL_ID"
    echo ""
    echo "После этого запусти ./start.sh снова."
    exit 1
fi

echo "[OK] Docker найден"
echo "[OK] .env найден"
echo ""

# Проверка Ollama
echo "Проверка Ollama (бесплатный AI)..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[ВНИМАНИЕ] Ollama не запущен локально!"
    echo ""
    echo "Для работы AI нужен Ollama:"
    echo "1. Скачай: https://ollama.com/download"
    echo "2. Запусти: ollama serve"
    echo "3. Скачай модель: ollama pull llama3.2"
    echo ""
    read -p "Продолжить без локального Ollama? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "   Запуск контейнеров..."
echo "=========================================="
echo ""

docker-compose up -d

echo ""
echo "[OK] Контейнеры запущены!"
echo ""
echo "Ожидание инициализации..."
sleep 15

echo ""
echo "=========================================="
echo "   Система готова!"
echo "=========================================="
echo ""
echo "API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""

# Открыть браузер (если есть)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi

echo "Команды:"
echo "  docker-compose logs -f    - смотреть логи"
echo "  docker-compose down       - остановить"
echo ""
echo "Нажми Ctrl+C для остановки..."
trap 'echo; echo "Остановка системы..."; docker-compose down; echo "[OK] Система остановлена!"; exit 0' INT

# Ждем
while true; do
    sleep 1
done