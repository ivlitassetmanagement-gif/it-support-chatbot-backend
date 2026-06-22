@echo off
REM Start IT Support Chatbot
cd /d D:\IT_Support_Chatbot\backend
call .\venv\Scripts\activate.bat
echo.
echo ========================================
echo Starting IT Support Chatbot v2.0...
echo ========================================
echo.
python run.py
pause
