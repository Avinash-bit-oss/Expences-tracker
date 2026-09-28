# Personal Expense Tracker

A modern, responsive full-stack personal finance web application built with Python (Flask) and a Tailwind CSS / Chart.js frontend. Optimized for local development and cloud production deployment on **Render**.

---

## ✨ Features

- **Interactive Financial Dashboard**:
  - Clean, modern UI with dark & light theme toggle and live status indicator.
  - Category Donut Chart and Monthly Spending Trend Bar Chart powered by Chart.js.
  - KPI cards for Total Spending, Current Month Spending, Daily Average, and Top Category.

- **🎯 Monthly Budget Tracker & Alerts (New)**:
  - Set and adjust your monthly spending budget target limit.
  - Dynamic visual progress bar (green `<75%`, amber `75%-99%`, red `≥100%`).
  - Real-time remaining balance and over-budget alert notifications.

- **💳 Payment Method Tracking (New)**:
  - Track payments across **UPI (GPay / PhonePe / Paytm)**, **Credit Card**, **Debit Card**, **Cash**, and **Net Banking**.
  - Color-coded badges for payment methods in every transaction row.
  - Filter transactions by payment method.

- **📅 Date Filter Presets (New)**:
  - Quick filter buttons for **All Time**, **This Month**, **Last 30 Days**, and **This Year**.

- **⚡ Quick Expense Entry**:
  - Add expenses with pre-filled current date, category picker (with custom category support), and quick-add buttons (+₹100, +₹250, +₹500, +₹1000).

- **🔄 Bulk CSV & JSON Import (New)**:
  - Drag-and-drop or select any CSV or JSON file to bulk-import transactions in seconds.

- **📥 Dual Format Data Export (New)**:
  - Export transactions to standard **CSV** or full **JSON** backup.

- **✨ One-Click Realistic Sample Data (New)**:
  - Populate sample categorized transactions with 1 click to preview charts and metrics immediately.

- **🛡️ Production & Render Ready (New)**:
  - Dynamic cloud port binding via `os.environ.get("PORT")`.
  - Production WSGI server via `gunicorn`.
  - Zero-downtime health check endpoint (`/health`).
  - Infrastructure-as-Code Blueprint (`render.yaml`) and `Procfile`.

---

## 📁 Project Structure

```text
├── app.py              # Flask REST API backend & static file server
├── expenses.json       # Persistent JSON database for transactions
├── settings.json       # App configuration (budget targets, currency)
├── test_app.py         # Automated unit test suite (11 unit tests)
├── requirements.txt    # Python dependencies (Flask, Gunicorn)
├── render.yaml         # Render deployment blueprint configuration
├── Procfile            # Render / Heroku process declaration
├── runtime.txt         # Pinned Python version (3.11.9)
├── .gitignore          # Git exclusion rules
├── run.bat             # Windows one-click local runner
└── static/
    ├── index.html      # Responsive dashboard UI
    ├── styles.css      # Custom styling, animations & badge themes
    └── app.js          # Dynamic UI logic, Chart.js integrations & API calls
```

---

## 🚀 How to Run Locally

### Option 1: Double-Click `run.bat`
Simply double-click `run.bat` in the project directory.

### Option 2: Command Line
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run unit tests
python test_app.py

# 3. Start the application
python app.py
```

Then visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🌐 Deploying to Render (Step-by-Step)

You can deploy this application on [Render](https://render.com) for free in just a few minutes using either GitHub or the Render Blueprint.

### Step 1: Push Code to GitHub

1. If Git is not yet installed on your system, install it from [git-scm.com](https://git-scm.com/download/win).
2. In your project directory:
   ```bash
   git init
   git add .
   git commit -m "feat: complete expense tracker with budget and render configs"
   ```
3. Create a new repository on [GitHub](https://github.com/new) (e.g. `expense-tracker`).
4. Link and push your repository:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/expense-tracker.git
   git branch -M main
   git push -u origin main
   ```

*(Alternative: You can also drag and drop the folder directly into GitHub via the "Upload files" button on GitHub.com)*

---

### Step 2: Deploy on Render

#### Method A: Connect Repository (Recommended)
1. Sign in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and connect your GitHub account.
4. Select your `expense-tracker` repository.
5. Configure the following settings:
   - **Name**: `my-expense-tracker` (or your preferred name)
   - **Region**: Choose the closest region (e.g., Singapore or Frankfurt)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank)*
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: `Free`
6. Under **Advanced**:
   - **Health Check Path**: `/health`
7. Click **Create Web Service**.

#### Method B: Render Blueprint (`render.yaml`)
1. In Render Dashboard, click **New +** and select **Blueprint**.
2. Connect your repository containing `render.yaml`.
3. Render will automatically read `render.yaml` and configure the service and health check.
4. Click **Apply**.

---

### Step 3: Access Your Live Application

Render will build the dependencies and start the app. Once completed, Render provides your public URL:
```text
https://my-expense-tracker.onrender.com
```
Open the URL in any browser on desktop or mobile!

---

## 🧪 Running Automated Tests

Run the test suite anytime using:
```bash
python test_app.py
```
This tests:
- Home page delivery (`/`)
- Expense CRUD (`GET`, `POST`, `PUT`, `DELETE /api/expenses`)
- Summary analytics (`/api/summary`)
- Health check monitoring (`/health`)
- Budget settings (`/api/budget`)
- Bulk import (`/api/expenses/import`)
- JSON export (`/api/export/json`)
- Sample data generation (`/api/sample-data`)
