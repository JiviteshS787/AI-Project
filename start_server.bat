@echo off
cd /d C:\Users\jivit\AI_Project\AI-Project
call venv\Scripts\activate.bat
uvicorn dashboard_api.server:app --host 0.0.0.0 --port 8000 >> C:\Users\jivit\AI_Project\AI-Project\server_log.txt 2>&1