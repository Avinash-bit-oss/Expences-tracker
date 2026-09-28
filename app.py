import csv
import io
import json
import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, Response

app = Flask(__name__, static_folder="static", static_url_path="")

# Data file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.environ.get("DATA_FILE_PATH", os.path.join(BASE_DIR, "expenses.json"))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

DEFAULT_CATEGORIES = [
    "Food",
    "Transport",
    "Entertainment",
    "Groceries",
    "Bills",
    "Shopping",
    "Health",
    "Education",
    "Other"
]

DEFAULT_PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Cash", "Net Banking", "Other"]


def load_settings():
    """Load settings (such as monthly budget limit) from settings.json."""
    default_settings = {
        "monthly_budget": 25000.0,
        "currency": "INR",
        "currency_symbol": "₹"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_settings.update(data)
        except Exception:
            pass
    return default_settings


def save_settings(settings):
    """Save settings to settings.json."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def load_expenses():
    """Load expenses from file, ensuring all entries have unique IDs and required fields."""
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                expenses = json.load(file)
        except Exception:
            expenses = []
    else:
        expenses = []

    modified = False
    for exp in expenses:
        if "id" not in exp or not exp["id"]:
            exp["id"] = f"exp_{uuid.uuid4().hex[:8]}"
            modified = True
        if "amount" in exp:
            exp["amount"] = round(float(exp["amount"]), 2)
        if "note" not in exp:
            exp["note"] = ""
        if "payment_method" not in exp or not exp["payment_method"]:
            exp["payment_method"] = "UPI"
            modified = True

    if modified:
        save_expenses(expenses)

    return expenses


def save_expenses(expenses):
    """Save expenses to file with pretty indentation."""
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(expenses, file, indent=4)


def calculate_summary(expenses):
    """Calculate comprehensive spending summaries and statistics."""
    total = 0.0
    category_summary = {}
    monthly_summary = {}
    payment_method_summary = {}
    current_month = datetime.now().strftime("%Y-%m")
    current_month_total = 0.0
    highest_expense = None

    for expense in expenses:
        amount = float(expense.get("amount", 0))
        category = expense.get("category", "Uncategorized").strip() or "Uncategorized"
        payment_method = expense.get("payment_method", "Other").strip() or "Other"
        date_str = expense.get("date", "")
        month = date_str[:7] if len(date_str) >= 7 else "Unknown"

        total += amount

        # Category-wise summary
        category_summary[category] = round(category_summary.get(category, 0.0) + amount, 2)

        # Payment method summary
        payment_method_summary[payment_method] = round(payment_method_summary.get(payment_method, 0.0) + amount, 2)

        # Monthly summary
        if month != "Unknown":
            monthly_summary[month] = round(monthly_summary.get(month, 0.0) + amount, 2)

        if month == current_month:
            current_month_total += amount

        # Track highest single expense
        if highest_expense is None or amount > highest_expense.get("amount", 0):
            highest_expense = {
                "id": expense.get("id"),
                "amount": amount,
                "category": category,
                "note": expense.get("note", ""),
                "date": date_str
            }

    # Sort monthly summary chronologically
    sorted_monthly = {k: monthly_summary[k] for k in sorted(monthly_summary.keys())}

    # Find top category
    top_category = None
    top_category_amount = 0.0
    if category_summary:
        top_category = max(category_summary, key=category_summary.get)
        top_category_amount = category_summary[top_category]

    # Daily average for current month
    day_of_month = datetime.now().day
    daily_avg_current_month = round(current_month_total / day_of_month, 2) if day_of_month > 0 else 0.0

    # Average expense per transaction
    avg_per_transaction = round(total / len(expenses), 2) if expenses else 0.0

    return {
        "total": round(total, 2),
        "count": len(expenses),
        "current_month": current_month,
        "current_month_total": round(current_month_total, 2),
        "daily_avg_current_month": daily_avg_current_month,
        "avg_per_transaction": avg_per_transaction,
        "top_category": top_category,
        "top_category_amount": round(top_category_amount, 2),
        "highest_expense": highest_expense,
        "category_summary": category_summary,
        "monthly_summary": sorted_monthly,
        "payment_method_summary": payment_method_summary,
    }


# ==================== HEALTH CHECK (RENDER CLOUD) ====================


@app.route("/health")
def health_check():
    """Health check endpoint for Render zero-downtime monitors."""
    return jsonify({
        "status": "healthy",
        "service": "personal-expense-tracker",
        "timestamp": datetime.now().isoformat()
    }), 200


# ==================== REST API ROUTES ====================


@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    """Retrieve all expenses with optional filtering, searching, date range, and sorting."""
    expenses = load_expenses()

    # Query params
    search = request.args.get("search", "").strip().lower()
    category = request.args.get("category", "").strip()
    month = request.args.get("month", "").strip()
    payment_method = request.args.get("payment_method", "").strip()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()
    sort_by = request.args.get("sort_by", "date")  # 'date' or 'amount'
    order = request.args.get("order", "desc")  # 'asc' or 'desc'

    filtered = []
    for exp in expenses:
        # Search match (category, note, or payment method)
        if search:
            note_match = search in exp.get("note", "").lower()
            cat_match = search in exp.get("category", "").lower()
            pm_match = search in exp.get("payment_method", "").lower()
            if not (note_match or cat_match or pm_match):
                continue

        # Category filter
        if category and exp.get("category", "").lower() != category.lower():
            continue

        # Payment method filter
        if payment_method and exp.get("payment_method", "").lower() != payment_method.lower():
            continue

        # Month filter (format YYYY-MM)
        exp_date = exp.get("date", "")
        if month and not exp_date.startswith(month):
            continue

        # Date range filters
        if from_date and exp_date < from_date:
            continue
        if to_date and exp_date > to_date:
            continue

        filtered.append(exp)

    # Sorting
    reverse = (order == "desc")
    if sort_by == "amount":
        filtered.sort(key=lambda x: float(x.get("amount", 0)), reverse=reverse)
    else:  # Default sort by date
        filtered.sort(key=lambda x: x.get("date", ""), reverse=reverse)

    return jsonify({"success": True, "data": filtered, "count": len(filtered)})


@app.route("/api/expenses", methods=["POST"])
def add_expense_route():
    """Add a new expense."""
    data = request.get_json() or {}

    # Validation
    try:
        amount = round(float(data.get("amount")), 2)
        if amount <= 0:
            return jsonify({"success": False, "error": "Amount must be greater than 0"}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Valid numeric amount is required"}), 400

    category = str(data.get("category", "")).strip()
    if not category:
        return jsonify({"success": False, "error": "Category is required"}), 400

    payment_method = str(data.get("payment_method", "UPI")).strip() or "UPI"

    # Date handling (YYYY-MM-DD)
    date_input = str(data.get("date", "")).strip()
    if not date_input:
        date_val = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            date_val = date_input
        except ValueError:
            return jsonify({"success": False, "error": "Date must be in YYYY-MM-DD format"}), 400

    note = str(data.get("note", "")).strip()

    new_expense = {
        "id": f"exp_{uuid.uuid4().hex[:8]}",
        "amount": amount,
        "category": category,
        "payment_method": payment_method,
        "date": date_val,
        "note": note
    }

    expenses = load_expenses()
    expenses.append(new_expense)
    save_expenses(expenses)

    return jsonify({"success": True, "data": new_expense, "message": "Expense added successfully!"}), 201


@app.route("/api/expenses/<expense_id>", methods=["DELETE"])
def delete_expense_route(expense_id):
    """Delete an expense by its unique ID."""
    expenses = load_expenses()
    removed_item = None

    for i, exp in enumerate(expenses):
        if exp.get("id") == expense_id:
            removed_item = expenses.pop(i)
            break

    if removed_item is None:
        return jsonify({"success": False, "error": "Expense not found"}), 404

    save_expenses(expenses)
    return jsonify({
        "success": True,
        "message": f"Deleted expense of ₹{removed_item['amount']} ({removed_item['category']})",
        "deleted": removed_item
    })


@app.route("/api/expenses/all", methods=["DELETE"])
def clear_all_expenses_route():
    """Clear all expenses (with safety)."""
    save_expenses([])
    return jsonify({"success": True, "message": "All expense records cleared."})


@app.route("/api/expenses/<expense_id>", methods=["PUT"])
def update_expense_route(expense_id):
    """Update an existing expense."""
    data = request.get_json() or {}
    expenses = load_expenses()
    target = None

    for exp in expenses:
        if exp.get("id") == expense_id:
            target = exp
            break

    if target is None:
        return jsonify({"success": False, "error": "Expense not found"}), 404

    if "amount" in data:
        try:
            amt = round(float(data["amount"]), 2)
            if amt <= 0:
                return jsonify({"success": False, "error": "Amount must be greater than 0"}), 400
            target["amount"] = amt
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid amount"}), 400

    if "category" in data:
        cat = str(data["category"]).strip()
        if not cat:
            return jsonify({"success": False, "error": "Category cannot be empty"}), 400
        target["category"] = cat

    if "payment_method" in data:
        pm = str(data["payment_method"]).strip()
        if pm:
            target["payment_method"] = pm

    if "date" in data:
        date_str = str(data["date"]).strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            target["date"] = date_str
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format (YYYY-MM-DD)"}), 400

    if "note" in data:
        target["note"] = str(data["note"]).strip()

    save_expenses(expenses)
    return jsonify({"success": True, "data": target, "message": "Expense updated successfully!"})


@app.route("/api/summary", methods=["GET"])
def get_summary_route():
    """Retrieve full summary statistics for cards, graphs, and analytics."""
    expenses = load_expenses()
    summary = calculate_summary(expenses)
    return jsonify({"success": True, "data": summary})


@app.route("/api/budget", methods=["GET", "POST"])
def budget_route():
    """Get or update monthly budget settings."""
    settings = load_settings()

    if request.method == "POST":
        data = request.get_json() or {}
        try:
            budget_val = round(float(data.get("monthly_budget", 0)), 2)
            if budget_val < 0:
                return jsonify({"success": False, "error": "Budget cannot be negative"}), 400
            settings["monthly_budget"] = budget_val
            save_settings(settings)
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Invalid budget value"}), 400

    # Calculate current month's budget tracking
    expenses = load_expenses()
    current_month = datetime.now().strftime("%Y-%m")
    spent = sum(float(e.get("amount", 0)) for e in expenses if e.get("date", "").startswith(current_month))
    budget_limit = float(settings.get("monthly_budget", 25000.0))
    remaining = round(budget_limit - spent, 2)
    percent_used = round((spent / budget_limit * 100), 1) if budget_limit > 0 else 0.0

    return jsonify({
        "success": True,
        "data": {
            "monthly_budget": budget_limit,
            "current_month": current_month,
            "spent": round(spent, 2),
            "remaining": remaining,
            "percent_used": percent_used,
            "is_over_budget": spent > budget_limit
        }
    })


@app.route("/api/categories", methods=["GET"])
def get_categories_route():
    """Retrieve all unique categories used + default categories."""
    expenses = load_expenses()
    used_categories = {exp.get("category", "").strip() for exp in expenses if exp.get("category")}
    all_categories = sorted(list(set(DEFAULT_CATEGORIES).union(used_categories)))
    return jsonify({"success": True, "data": all_categories})


@app.route("/api/payment-methods", methods=["GET"])
def get_payment_methods_route():
    """Retrieve list of supported payment methods."""
    expenses = load_expenses()
    used_methods = {exp.get("payment_method", "").strip() for exp in expenses if exp.get("payment_method")}
    all_methods = sorted(list(set(DEFAULT_PAYMENT_METHODS).union(used_methods)))
    return jsonify({"success": True, "data": all_methods})


@app.route("/api/expenses/import", methods=["POST"])
def import_expenses_route():
    """Bulk import expenses from JSON array or uploaded CSV file."""
    expenses = load_expenses()
    imported_count = 0

    # 1. JSON Array import
    if request.is_json:
        data = request.get_json()
        items = data if isinstance(data, list) else data.get("expenses", [])
        for item in items:
            try:
                amt = round(float(item.get("amount", 0)), 2)
                cat = str(item.get("category", "General")).strip() or "General"
                date_val = str(item.get("date", datetime.now().strftime("%Y-%m-%d"))).strip()
                note = str(item.get("note", "")).strip()
                pm = str(item.get("payment_method", "UPI")).strip() or "UPI"
                if amt > 0:
                    expenses.append({
                        "id": f"exp_{uuid.uuid4().hex[:8]}",
                        "amount": amt,
                        "category": cat,
                        "payment_method": pm,
                        "date": date_val,
                        "note": note
                    })
                    imported_count += 1
            except Exception:
                continue

    # 2. CSV file upload
    elif "file" in request.files:
        uploaded_file = request.files["file"]
        if not uploaded_file.filename:
            return jsonify({"success": False, "error": "No file selected"}), 400

        try:
            stream = io.StringIO(uploaded_file.stream.read().decode("utf-8-sig"), newline=None)
            reader = csv.DictReader(stream)
            for row in reader:
                # Normalize keys to lowercase stripped
                row_lower = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                raw_amt = row_lower.get("amount") or row_lower.get("amount (inr)") or "0"
                try:
                    amt = round(float(raw_amt.replace("₹", "").replace(",", "")), 2)
                except ValueError:
                    continue

                if amt <= 0:
                    continue

                cat = row_lower.get("category") or "General"
                date_val = row_lower.get("date") or datetime.now().strftime("%Y-%m-%d")
                note = row_lower.get("note") or row_lower.get("description") or ""
                pm = row_lower.get("payment_method") or row_lower.get("payment method") or "UPI"

                # Validate date format if possible
                try:
                    datetime.strptime(date_val, "%Y-%m-%d")
                except ValueError:
                    date_val = datetime.now().strftime("%Y-%m-%d")

                expenses.append({
                    "id": f"exp_{uuid.uuid4().hex[:8]}",
                    "amount": amt,
                    "category": cat,
                    "payment_method": pm,
                    "date": date_val,
                    "note": note
                })
                imported_count += 1
        except Exception as e:
            return jsonify({"success": False, "error": f"Failed to parse CSV: {str(e)}"}), 400
    else:
        return jsonify({"success": False, "error": "Provide JSON array or CSV file under 'file'"}), 400

    save_expenses(expenses)
    return jsonify({
        "success": True,
        "imported_count": imported_count,
        "message": f"Successfully imported {imported_count} expenses!"
    })


@app.route("/api/export/json", methods=["GET"])
def export_json_route():
    """Download entire expenses database as formatted JSON file."""
    expenses = load_expenses()
    json_str = json.dumps(expenses, indent=4)
    filename = f"expenses_{datetime.now().strftime('%Y%m%d')}.json"
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/api/sample-data", methods=["POST"])
def load_sample_data_route():
    """Populate realistic sample expenses for demo and portfolio testing."""
    today = datetime.now()
    curr_yr = today.year
    curr_mo = today.month

    # Format dates relative to current month and last month
    def make_date(year, month, day):
        return f"{year:04d}-{month:02d}-{day:02d}"

    prev_mo = curr_mo - 1 if curr_mo > 1 else 12
    prev_yr = curr_yr if curr_mo > 1 else curr_yr - 1

    sample_items = [
        {"amount": 1850.00, "category": "Groceries", "payment_method": "UPI", "date": make_date(curr_yr, curr_mo, min(2, today.day)), "note": "Weekly supermarket essentials"},
        {"amount": 350.00, "category": "Food", "payment_method": "UPI", "date": make_date(curr_yr, curr_mo, min(3, today.day)), "note": "Team lunch at cafeteria"},
        {"amount": 950.00, "category": "Bills", "payment_method": "Net Banking", "date": make_date(curr_yr, curr_mo, min(5, today.day)), "note": "High-speed broadband bill"},
        {"amount": 420.00, "category": "Transport", "payment_method": "Cash", "date": make_date(curr_yr, curr_mo, min(6, today.day)), "note": "Metro smart card recharge"},
        {"amount": 1200.00, "category": "Entertainment", "payment_method": "Credit Card", "date": make_date(curr_yr, curr_mo, min(8, today.day)), "note": "Weekend IMAX movie tickets"},
        {"amount": 2500.00, "category": "Shopping", "payment_method": "Credit Card", "date": make_date(curr_yr, curr_mo, min(10, today.day)), "note": "Running shoes discount deal"},
        {"amount": 650.00, "category": "Health", "payment_method": "Debit Card", "date": make_date(curr_yr, curr_mo, min(12, today.day)), "note": "Multivitamins & pharmacy"},
        {"amount": 199.00, "category": "Entertainment", "payment_method": "UPI", "date": make_date(curr_yr, curr_mo, min(14, today.day)), "note": "Music streaming subscription"},
        {"amount": 1400.00, "category": "Transport", "payment_method": "UPI", "date": make_date(curr_yr, curr_mo, min(16, today.day)), "note": "Fuel refill - Full tank"},
        {"amount": 880.00, "category": "Food", "payment_method": "UPI", "date": make_date(curr_yr, curr_mo, min(18, today.day)), "note": "Dinner with family"},
        {"amount": 3200.00, "category": "Groceries", "payment_method": "Debit Card", "date": make_date(prev_yr, prev_mo, 15), "note": "Monthly pantry groceries"},
        {"amount": 1500.00, "category": "Bills", "payment_method": "Net Banking", "date": make_date(prev_yr, prev_mo, 10), "note": "Electricity bill"},
        {"amount": 750.00, "category": "Education", "payment_method": "UPI", "date": make_date(prev_yr, prev_mo, 20), "note": "Programming e-book & tutorial"}
    ]

    expenses = load_expenses()
    for item in sample_items:
        expenses.append({
            "id": f"exp_{uuid.uuid4().hex[:8]}",
            "amount": item["amount"],
            "category": item["category"],
            "payment_method": item["payment_method"],
            "date": item["date"],
            "note": item["note"]
        })

    save_expenses(expenses)
    return jsonify({
        "success": True,
        "message": f"Successfully loaded {len(sample_items)} realistic sample expenses!",
        "count": len(sample_items)
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    print(f"Starting Personal Expense Tracker server on 0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)