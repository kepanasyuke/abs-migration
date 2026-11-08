@echo off
rem Запуск API платформы миграции: интерфейс открывается на http://127.0.0.1:8000/app
cd /d "%~dp0"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
