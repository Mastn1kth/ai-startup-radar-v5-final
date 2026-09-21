@echo off
chcp 65001 >nul
title AI Startup Radar - Запуск...
cls

echo ==========================================
echo    AI Startup Radar - Запуск системы
echo ==========================================
echo.

REM Проверка Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] Docker не найден!
    echo Установи Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Проверка .env
if not exist .env (
    echo [ВНИМАНИЕ] Файл .env не найден!
    echo Копирую .env.example -> .env
    copy .env.example .env
    echo.
    echo [ВАЖНО] Открой файл .env и вставь свои токены:
    echo   - TELEGRAM_BOT_TOKEN
    echo   - TELEGRAM_CHANNEL_ID
    echo.
    echo После этого запусти start.bat снова.
    pause
    exit /b 1
)

echo [OK] Docker найден
echo [OK] .env найден
echo.

REM Проверка Ollama
echo Проверка Ollama (бесплатный AI)...
curl -s http://localhost:11434/api/tags >nul 2>nul
if %errorlevel% neq 0 (
    echo [ВНИМАНИЕ] Ollama не запущен локально!
    echo.
    echo Для работы AI нужен Ollama:
    echo 1. Скачай: https://ollama.com/download/windows
    echo 2. Установи и запусти
    echo 3. Скачай модель: ollama pull llama3.2
    echo.
    echo Или используй Docker-версию Ollama (будет запущена автоматически)
    echo.
    choice /C YN /M "Продолжить без локального Ollama?"
    if %errorlevel% equ 2 exit /b 1
)

echo.
echo ==========================================
echo    Запуск контейнеров...
echo ==========================================
echo.

docker-compose up -d

echo.
echo [OK] Контейнеры запущены!
echo.
echo Ожидание инициализации...
timeout /t 15 /nobreak > nul

echo.
echo ==========================================
echo    Система готова!
echo ==========================================
echo.
echo Открываю дашборд...
start http://localhost:3000
echo.
echo API: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Команды:
echo   docker-compose logs -f    - смотреть логи
echo   docker-compose down       - остановить
echo.
echo Нажми любую клавишу для остановки...
pause > nul

echo.
echo Остановка системы...
docker-compose down
echo.
echo [OK] Система остановлена!
timeout /t 2 > nul