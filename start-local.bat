@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title AI Startup Radar - Local launcher

echo ==========================================
echo    AI Startup Radar - запуск без Docker
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден.
    pause
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Node.js не найден.
    pause
    exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
    echo [1/4] Создаю Python-окружение...
    python -m venv "backend\.venv"
    if errorlevel 1 goto :error
)

echo [2/4] Проверяю backend-зависимости...
"backend\.venv\Scripts\python.exe" -c "import fastapi,uvicorn,aiosqlite" >nul 2>nul
if errorlevel 1 (
    "backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
    if errorlevel 1 goto :error
)

echo [3/4] Проверяю frontend-зависимости...
if not exist "frontend\node_modules\.bin\vite.cmd" (
    pushd frontend
    call npm install
    if errorlevel 1 (
        popd
        goto :error
    )
    popd
)

echo [4/4] Запускаю серверы...
set "DATABASE_URL=sqlite+aiosqlite:///./radar-local.db"
set "REDIS_URL=redis://localhost:6379/0"
set "QDRANT_URL=http://localhost:6333"
set "OLLAMA_URL=http://localhost:11434"
set "CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://gory-staff.ru,https://www.gory-staff.ru"
set "DEBUG=False"
set "SECRET_KEY=local-radar-secret-change-before-public-access"
set "DEFAULT_ADMIN_EMAIL=admin@gory-staff.ru"
set "DEFAULT_ADMIN_PASSWORD=local-admin-2026"

start "AI Radar Backend" /D "%~dp0backend" cmd /k "set DATABASE_URL=%DATABASE_URL%&& set REDIS_URL=%REDIS_URL%&& set QDRANT_URL=%QDRANT_URL%&& set OLLAMA_URL=%OLLAMA_URL%&& set CORS_ORIGINS=%CORS_ORIGINS%&& set DEBUG=%DEBUG%&& set SECRET_KEY=%SECRET_KEY%&& set DEFAULT_ADMIN_EMAIL=%DEFAULT_ADMIN_EMAIL%&& set DEFAULT_ADMIN_PASSWORD=%DEFAULT_ADMIN_PASSWORD%&& .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
start "AI Radar Frontend" /D "%~dp0frontend" cmd /k "npm start"

echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo Домен:    https://gory-staff.ru
echo База:     backend\radar-local.db
echo Админ:    admin@gory-staff.ru / local-admin-2026
echo.
echo Ollama и Qdrant необязательны для открытия интерфейса.
echo AI-анализ и векторный поиск заработают после их локального запуска.
echo Для доступа через домен нужны DNS, открытые порты и HTTPS-прокси.
echo.
timeout /t 4 /nobreak >nul
start "" "http://localhost:3000"
exit /b 0

:error
echo.
echo [ОШИБКА] Установка или запуск не завершены. Смотри сообщение выше.
pause
exit /b 1
