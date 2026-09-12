@echo off
cd /d C:\Users\jivit\AI_Project\AI-Project
call venv\Scripts\activate.bat
python -m assistant.system_tools.clipboard_helper >> C:\Users\jivit\AI_Project\AI-Project\clipboard_helper_log.txt 2>&1