@echo off
title Personal Expense Tracker
echo ==========================================
echo Starting Personal Expense Tracker Server...
echo ==========================================
echo.
python -m pip install -r requirements.txt --quiet
python app.py
pause
