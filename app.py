from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "expenses.db")

app = Flask(__name__)
app.secret_key = "dev-secret-change-this"  # For coursework/dev. Change for production.


# ----------------------------
# DB helpers
# ----------------------------
def get_db() -> sqlite3.Connection:
    """Get a SQLite connection for the current request."""
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception: Optional[BaseException]) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Create tables + seed initial data."""
    db = get_db()

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','admin'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL CHECK(amount >= 0),
            description TEXT NOT NULL,
            expense_date TEXT NOT NULL, -- store as YYYY-MM-DD
            is_essential INTEGER NOT NULL DEFAULT 0, -- boolean 0/1
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE RESTRICT
        );
        """
    )

    # Seed categories
    default_categories = ["Food", "Transport", "Rent", "Shopping", "Bills", "Other"]
    for c in default_categories:
        db.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (c,))

    # Seed users
    # NOTE: For coursework simplicity, passwords are plain text.
    # In real apps use password hashing.
    db.execute(
        "INSERT OR IGNORE INTO users(username, password, role) VALUES (?,?,?)",
        ("student", "student123", "user"),
    )
    db.execute(
        "INSERT OR IGNORE INTO users(username, password, role) VALUES (?,?,?)",
        ("admin", "admin123", "admin"),
    )

    db.commit()


@app.before_request
def ensure_db_ready() -> None:
    # Create DB/tables on first request
    db_exists = os.path.exists(DB_PATH)
    if not db_exists:
        # Touch the file so sqlite can open it
        open(DB_PATH, "a").close()
    init_db()


# ----------------------------
# Auth helpers
# ----------------------------
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)

    return wrapper


def current_user_id() -> Optional[int]:
    return session.get("user_id")


def is_admin() -> bool:
    return session.get("role") == "admin"


# ----------------------------
# Routes
# ----------------------------
@app.route("/")
def index():
    # Image size selector (Must-have: selectable sizes)
    size = request.args.get("img", "medium")
    if size not in ("small", "medium", "large"):
        size = "medium"

    # Use a Python f-string (required) in a safe way
    greeting = f"Welcome! Today you can track and control your spending."

    return render_template("index.html", img_size=size, greeting=greeting)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return render_template("login.html", username=username)

        db = get_db()
        user = db.execute(
            "SELECT id, username, role FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()

        if user is None:
            flash("Invalid login details.", "danger")
            return render_template("login.html", username=username)

        session["user_id"] = int(user["id"])
        session["username"] = user["username"]
        session["role"] = user["role"]

        flash(f"Logged in as {user['username']} ({user['role']}).", "success")
        next_url = request.args.get("next")
        return redirect(next_url or url_for("expenses"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/expenses")
@login_required
def expenses():
    """
    Shows expenses with filters (Must-have: SQL select according to user input).
    """
    db = get_db()

    # Filters from user input
    category_id = request.args.get("category_id", "").strip()
    date_from = request.args.get("from", "").strip()
    date_to = request.args.get("to", "").strip()
    essential = request.args.get("essential", "").strip()  # "", "1", "0"

    # Build query dynamically using safe parameters
    where_clauses = []
    params: List[Any] = []

    if not is_admin():
        where_clauses.append("e.user_id = ?")
        params.append(current_user_id())

    if category_id.isdigit():
        where_clauses.append("e.category_id = ?")
        params.append(int(category_id))

    if date_from:
        where_clauses.append("e.expense_date >= ?")
        params.append(date_from)

    if date_to:
        where_clauses.append("e.expense_date <= ?")
        params.append(date_to)

    if essential in ("0", "1"):
        where_clauses.append("e.is_essential = ?")
        params.append(int(essential))

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    rows = db.execute(
        f"""
        SELECT
            e.id,
            e.amount,
            e.description,
            e.expense_date,
            e.is_essential,
            c.name AS category_name,
            u.username AS owner
        FROM expenses e
        JOIN categories c ON c.id = e.category_id
        JOIN users u ON u.id = e.user_id
        {where_sql}
        ORDER BY e.expense_date DESC, e.id DESC
        """,
        tuple(params),
    ).fetchall()

    # Loop/list requirement: compute totals in Python
    total = 0.0
    totals_by_category: Dict[str, float] = {}
    for r in rows:
        amt = float(r["amount"])
        total += amt
        cname = r["category_name"]
        totals_by_category[cname] = totals_by_category.get(cname, 0.0) + amt

    categories = db.execute("SELECT id, name FROM categories ORDER BY name").fetchall()

    return render_template(
        "expenses.html",
        expenses=rows,
        categories=categories,
        total=total,
        totals_by_category=totals_by_category,
        filters={
            "category_id": category_id,
            "from": date_from,
            "to": date_to,
            "essential": essential,
        },
        admin=is_admin(),
    )


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    db = get_db()
    categories = db.execute("SELECT id, name FROM categories ORDER BY name").fetchall()

    if request.method == "POST":
        category_id = request.form.get("category_id", "").strip()
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        is_essential = 1 if request.form.get("is_essential") == "on" else 0

        # Basic validation (Should-have)
        errors = []
        if not category_id.isdigit():
            errors.append("Please select a valid category.")
        try:
            amount_f = float(amount)
            if amount_f <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Please enter a valid number for amount.")

        if not description:
            errors.append("Description is required.")
        if not expense_date:
            errors.append("Date is required (YYYY-MM-DD).")

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template(
                "add_expense.html",
                categories=categories,
                form=request.form,
            )

        # Insert into DB
        db.execute(
            """
            INSERT INTO expenses(user_id, category_id, amount, description, expense_date, is_essential)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (current_user_id(), int(category_id), float(amount), description, expense_date, is_essential),
        )
        db.commit()

        flash("Expense added successfully.", "success")
        return redirect(url_for("expenses"))

    return render_template("add_expense.html", categories=categories, form={})


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id: int):
    db = get_db()

    expense = db.execute(
        """
        SELECT id, user_id, category_id, amount, description, expense_date, is_essential
        FROM expenses
        WHERE id = ?
        """,
        (expense_id,),
    ).fetchone()

    if expense is None:
        flash("Expense not found.", "danger")
        return redirect(url_for("expenses"))

    # Permission check: users can edit only their own; admin can edit all
    if not is_admin() and int(expense["user_id"]) != int(current_user_id()):
        flash("You do not have permission to edit this item.", "danger")
        return redirect(url_for("expenses"))

    categories = db.execute("SELECT id, name FROM categories ORDER BY name").fetchall()

    if request.method == "POST":
        category_id = request.form.get("category_id", "").strip()
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        expense_date = request.form.get("expense_date", "").strip()
        is_essential = 1 if request.form.get("is_essential") == "on" else 0

        errors = []
        if not category_id.isdigit():
            errors.append("Please select a valid category.")
        try:
            amount_f = float(amount)
            if amount_f <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Please enter a valid number for amount.")

        if not description:
            errors.append("Description is required.")
        if not expense_date:
            errors.append("Date is required (YYYY-MM-DD).")

        if errors:
            for e in errors:
                flash(e, "warning")
            return render_template(
                "edit_expense.html",
                categories=categories,
                expense=dict(expense),
                form=request.form,
            )

        db.execute(
            """
            UPDATE expenses
            SET category_id = ?, amount = ?, description = ?, expense_date = ?, is_essential = ?
            WHERE id = ?
            """,
            (int(category_id), float(amount), description, expense_date, is_essential, expense_id),
        )
        db.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("expenses"))

    return render_template(
        "edit_expense.html",
        categories=categories,
        expense=dict(expense),
        form=dict(expense),
    )


@app.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id: int):
    db = get_db()

    exp = db.execute("SELECT id, user_id FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if exp is None:
        flash("Expense not found.", "danger")
        return redirect(url_for("expenses"))

    if not is_admin() and int(exp["user_id"]) != int(current_user_id()):
        flash("You do not have permission to delete this item.", "danger")
        return redirect(url_for("expenses"))

    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses"))


@app.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name is required.", "warning")
        else:
            try:
                db.execute("INSERT INTO categories(name) VALUES (?)", (name,))
                db.commit()
                flash("Category added.", "success")
            except sqlite3.IntegrityError:
                flash("That category already exists.", "warning")

        return redirect(url_for("categories"))

    cats = db.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
    return render_template("categories.html", categories=cats)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password are required.", "warning")
            return render_template("register.html")

        db = get_db()

        try:
            db.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, "user")
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists.", "danger")
            return render_template("register.html")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")



if __name__ == "__main__":
    app.run(debug=True, port=5001)
