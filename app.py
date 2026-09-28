import json
import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# Data file path relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(BASE_DIR, "expenses.json")


def load_expenses():
    """Load expenses from file, ensuring all entries have unique IDs."""
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r", encoding="utf-8") as file:
                expenses = json.load(file)
        except Exception:
            expenses = []
    else:
        expenses = []

    # Ensure every expense has an id and formatted fields
    modified = False
    for i, exp in enumerate(expenses):
        if "id" not in exp or not exp["id"]:
            exp["id"] = f"exp_{uuid.uuid4().hex[:8]}"
            modified = True
        if "amount" in exp:
            exp["amount"] = round(float(exp["amount"]), 2)
        if "note" not in exp:
            exp["note"] = ""

    if modified:
        save_expenses(expenses)

    return expenses


def save_expenses(expenses):
    """Save expenses to file with pretty indentation."""
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(expenses, file, indent=4)


def calculate_summary(expenses):
    """Calculate overall, category-wise, and monthly spending summaries."""
    total = 0.0
    category_summary = {}
    monthly_summary = {}
    current_month = datetime.now().strftime("%Y-%m")
    current_month_total = 0.0

    for expense in expenses:
        amount = float(expense.get("amount", 0))
        category = expense.get("category", "Uncategorized").strip() or "Uncategorized"
        date_str = expense.get("date", "")
        month = date_str[:7] if len(date_str) >= 7 else "Unknown"

        total += amount

        # Category wise summary
        category_summary[category] = round(category_summary.get(category, 0.0) + amount, 2)

        # Monthly summary
        if month != "Unknown":
            monthly_summary[month] = round(monthly_summary.get(month, 0.0) + amount, 2)

        if month == current_month:
            current_month_total += amount

    # Sort monthly summary chronologically
    sorted_monthly = {k: monthly_summary[k] for k in sorted(monthly_summary.keys())}

    # Find top category
    top_category = None
    top_category_amount = 0.0
    if category_summary:
        top_category = max(category_summary, key=category_summary.get)
        top_category_amount = category_summary[top_category]

    return {
        "total": round(total, 2),
        "count": len(expenses),
        "current_month": current_month,
        "current_month_total": round(current_month_total, 2),
        "top_category": top_category,
        "top_category_amount": round(top_category_amount, 2),
        "category_summary": category_summary,
        "monthly_summary": sorted_monthly,
    }


# ==================== REST API ROUTES ====================


@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    """Retrieve all expenses with optional filtering, searching, and sorting."""
    expenses = load_expenses()

    # Query params
    search = request.args.get("search", "").strip().lower()
    category = request.args.get("category", "").strip()
    month = request.args.get("month", "").strip()
    sort_by = request.args.get("sort_by", "date")  # 'date' or 'amount'
    order = request.args.get("order", "desc")  # 'asc' or 'desc'

    filtered = []
    for exp in expenses:
        # Search match (category or note)
        if search:
            note_match = search in exp.get("note", "").lower()
            cat_match = search in exp.get("category", "").lower()
            if not (note_match or cat_match):
                continue

        # Category filter
        if category and exp.get("category", "").lower() != category.lower():
            continue

        # Month filter (format YYYY-MM)
        if month and not exp.get("date", "").startswith(month):
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

    # Date handling (YYYY-MM-DD)
    date_input = str(data.get("date", "")).strip()
    if not date_input:
        date_val = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            # Validate format
            datetime.strptime(date_input, "%Y-%m-%d")
            date_val = date_input
        except ValueError:
            return jsonify({"success": False, "error": "Date must be in YYYY-MM-DD format"}), 400

    note = str(data.get("note", "")).strip()

    new_expense = {
        "id": f"exp_{uuid.uuid4().hex[:8]}",
        "amount": amount,
        "category": category,
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
    initial_len = len(expenses)
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
    """Retrieve full summary statistics for cards and graphs."""
    expenses = load_expenses()
    summary = calculate_summary(expenses)
    return jsonify({"success": True, "data": summary})


@app.route("/api/categories", methods=["GET"])
def get_categories_route():
    """Retrieve all unique categories used + common defaults."""
    expenses = load_expenses()
    default_categories = ["Food", "Transport", "Entertainment", "Groceries", "Bills", "Shopping", "Health", "Education", "Other"]
    used_categories = {exp.get("category", "").strip() for exp in expenses if exp.get("category")}
    all_categories = sorted(list(set(default_categories).union(used_categories)))
    return jsonify({"success": True, "data": all_categories})


if __name__ == "__main__":
    print("Starting Personal Expense Tracker server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)