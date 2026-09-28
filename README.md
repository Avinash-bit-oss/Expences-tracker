# Personal Expense Tracker (Web Application)

A modern full-stack web application built from your Python personal expense tracking logic.

## Features
- **Interactive Web Dashboard**: Beautiful, clean UI with dark/light mode toggle.
- **Visual Analytics**: Interactive Category Donut Chart and Monthly Spending Trend Bar Chart powered by Chart.js.
- **RESTful Python API**: Flask backend providing endpoints for CRUD operations and summary analytics.
- **Smart Data Persistence**: Reads and writes directly to `expenses.json`.
- **Search & Filters**: Real-time search by description/category, filter by month or category, and sort by date or amount.
- **Quick Expense Entry**: Add expenses with pre-filled today's date, category selector (with custom category option), and quick-amount chips (+₹100, +₹500, etc.).
- **Edit & Delete Modals**: Safe deletions with confirmation dialogues and inline updates.
- **CSV Data Export**: Download expense records in standard CSV format.

## How to Run

### Option 1: Double-click `run.bat`
Simply double click `run.bat` in the project folder.

### Option 2: Command Line
```powershell
cd C:\Users\gedel\.gemini\antigravity\scratch\expense-tracker
python app.py
```

Then open your browser and go to:
**http://127.0.0.1:5000**

## Project Structure
- `app.py`: Flask application with REST API endpoints (`/api/expenses`, `/api/summary`, `/api/categories`).
- `expenses.json`: Persistent JSON storage compatible with your original Python script.
- `static/index.html`: Responsive single-page dashboard.
- `static/styles.css`: Custom animations, color-coded category badges, and dark mode themes.
- `static/app.js`: Dynamic frontend logic, API integration, and Chart.js graphs.
- `requirements.txt`: Python dependencies (`flask`).
- `run.bat`: Windows startup launcher.
"# Expences-tracker" 
