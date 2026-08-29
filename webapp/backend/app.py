"""
Flask backend API for Commitment Tracker.
"""

from flask import Flask, request, jsonify, session, redirect, render_template
from flask_cors import CORS
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables at the very beginning
load_dotenv()

# --------------------------------------------------
# Path setup (important for deployment)
# --------------------------------------------------
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from webapp.database.database import Database
from webapp.backend.priority_predictor import load_model, predict_priority, predict_priority_with_source
from webapp.backend.helpers import calculate_urgency

# --------------------------------------------------
# Flask App Configuration
# --------------------------------------------------
app = Flask(
    __name__,
    template_folder=Path(__file__).parent.parent / "frontend" / "templates",
    static_folder=Path(__file__).parent.parent / "frontend" / "static"
)

# SECRET KEY (use env variable in production)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.environ.get("SECRET_KEY", "dev-secret-key"))

CORS(app)

# --------------------------------------------------
# Initialize Database
# --------------------------------------------------
db = Database()

# --------------------------------------------------
# Database Availability Middleware
# --------------------------------------------------
@app.before_request
def check_db_connection():
    if db.connection_error:
        # Allow static files and logout to pass
        if request.path.startswith('/static/') or request.path == '/logout':
            return
        # Return JSON error for API requests
        if request.path.startswith('/api/'):
            return jsonify({"error": f"Database is currently unavailable: {db.connection_error}"}), 503
        return render_template("login.html", error="Database connection failed. Please check your configuration.")

# --------------------------------------------------
# Load ML Model ONCE at startup
# --------------------------------------------------
print("Loading ML model...")
load_model()
print("Application ready!")

# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.route("/")
def index():
    """Redirect user to login or dashboard."""
    if "user_id" not in session:
        return redirect("/login")
    return redirect("/dashboard")


def seed_dummy_commitments(user_id: str):
    """Seed a new user account with realistic dummy commitments."""
    now = datetime.now()
    seeds = [
        {
            "subject": "Prepare for Python system architecture interview",
            "description": "Review microservices, event-driven design, and MongoDB scalability patterns.",
            "deadline_dt": now + timedelta(days=1),
            "status": "Pending"
        },
        {
            "subject": "Pay quarterly utility bill payment",
            "description": "Pay gas, electricity, and water bills before the due date to avoid service fee penalties.",
            "deadline_dt": now + timedelta(days=3),
            "status": "Pending"
        },
        {
            "subject": "Submit monthly team performance report",
            "description": "Compile sprint velocity charts, review feedback, and send to department manager.",
            "deadline_dt": now - timedelta(hours=4),
            "status": "Pending"
        },
        {
            "subject": "Register for AWS certification exam",
            "description": "Complete the exam schedule and purchase the practice tests voucher.",
            "deadline_dt": now - timedelta(days=2),
            "status": "Completed"
        },
        {
            "subject": "Buy groceries for weekly meal prep",
            "description": "Get fresh spinach, tomatoes, chicken breasts, eggs, and coffee beans.",
            "deadline_dt": now + timedelta(days=5),
            "status": "Pending"
        }
    ]
    for seed in seeds:
        text = f"{seed['subject']} {seed['description']}".strip()
        priority, source = predict_priority_with_source(text, seed["deadline_dt"])
        db.create_commitment(
            user_id=user_id,
            subject=seed["subject"],
            description=seed["description"],
            deadline=seed["deadline_dt"].isoformat(),
            status=seed["status"],
            priority=priority,
            priority_source=source
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page supporting username/password flow."""
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username:
        return render_template("login.html", error="Name/Username is required")
    if not password:
        return render_template("login.html", error="Password is required")

    user = db.get_user_by_username(username)
    if not user:
        return render_template("login.html", error="Username does not exist. Please register first.")

    # Verify hashed password
    if not check_password_hash(user.get("password_hash", ""), password):
        return render_template("login.html", error="Incorrect password")

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect("/dashboard")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register page to create new accounts and seed realistic commitments."""
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not username:
        return render_template("register.html", error="Name/Username is required")
    if not password:
        return render_template("register.html", error="Password is required")

    existing_user = db.get_user_by_username(username)
    if existing_user:
        return render_template("register.html", error="Username already exists")

    password_hash = generate_password_hash(password)
    user_id = db.create_user(username, password_hash)
    if not user_id:
        return render_template("register.html", error="Failed to create account")

    # Seed realistic commitments for the new user
    seed_dummy_commitments(user_id)

    # Automatically sign in
    user = db.get_user_by_username(username)
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    """Dashboard view with automatic status sync."""
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    username = session["username"]

    status_filter = request.args.get("status", "")
    sort_priority = request.args.get("sort", "")

    if status_filter:
        commitments = db.get_user_commitments(user_id, status_filter, sort_priority)
    else:
        commitments = db.get_user_commitments(user_id, None, sort_priority)

    for commit in commitments:
        deadline_dt = None
        if commit.get("deadline"):
            try:
                deadline_dt = datetime.fromisoformat(commit["deadline"])
                commit["deadline_formatted"] = deadline_dt.strftime("%Y-%m-%d %H:%M")
                # Overdue if status is Overdue or (deadline passed and status is Pending)
                commit["is_overdue"] = (
                    commit["status"] == "Overdue"
                    or (deadline_dt < datetime.now() and commit["status"] == "Pending")
                )
            except Exception:
                commit["deadline_formatted"] = commit["deadline"]
                commit["is_overdue"] = False
        else:
            commit["deadline_formatted"] = "No deadline"
            commit["is_overdue"] = False

        commit["urgency"] = calculate_urgency(
            deadline_dt, commit.get("status", "Pending")
        )

        if not commit.get("priority"):
            commit["priority"] = "Medium"

    urgent = db.get_urgent_commitments(user_id, limit=5)
    for commit in urgent:
        if commit.get("deadline"):
            try:
                dt = datetime.fromisoformat(commit["deadline"])
                commit["deadline_formatted"] = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                commit["deadline_formatted"] = commit["deadline"]

    show_urgent_modal = len(urgent) > 0 and "urgent_shown" not in session

    return render_template(
        "dashboard.html",
        username=username,
        commitments=commitments,
        urgent_commitments=urgent,
        show_urgent_modal=show_urgent_modal,
        current_filter=status_filter,
        current_sort=sort_priority,
    )


@app.route("/add_commitment", methods=["POST"])
def add_commitment():
    """Add new commitment with ML-based priority and source tracking."""
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    subject = request.form.get("subject", "").strip()
    description = request.form.get("description", "").strip()
    deadline_str = request.form.get("deadline", "").strip() or None
    status = request.form.get("status", "Pending")

    if not subject:
        return redirect("/dashboard?error=Subject is required")

    deadline_dt = None
    deadline_iso = None
    if deadline_str:
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
            deadline_iso = deadline_dt.isoformat()
        except Exception:
            deadline_iso = None

    commitment_text = f"{subject} {description}".strip()
    priority, priority_source = predict_priority_with_source(commitment_text, deadline_dt)

    db.create_commitment(
        user_id, subject, description, deadline_iso, status, priority, priority_source
    )

    return redirect("/dashboard?success=Commitment added")


@app.route("/api/commitments/<commitment_id>/status", methods=["PUT"])
def update_status(commitment_id):
    """Update status of a commitment."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    status = data.get("status")

    if status not in ["Pending", "Completed", "Overdue"]:
        return jsonify({"error": "Invalid status"}), 400

    success = db.update_commitment_status(
        commitment_id, session["user_id"], status
    )

    if not success:
        return jsonify({"error": "Commitment not found or unauthorized"}), 404

    return jsonify({"success": True})


@app.route("/api/commitments/<commitment_id>/priority", methods=["PUT"])
def update_priority(commitment_id):
    """Manually override priority of a commitment."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    priority = data.get("priority")

    if priority not in ["High", "Medium", "Low"]:
        return jsonify({"error": "Invalid priority"}), 400

    success = db.update_commitment_priority(
        commitment_id, session["user_id"], priority
    )

    if not success:
        return jsonify({"error": "Commitment not found or unauthorized"}), 404

    return jsonify({"success": True})


@app.route("/api/commitments/<commitment_id>", methods=["DELETE"])
def delete_commitment(commitment_id):
    """Delete a commitment."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    success = db.delete_commitment(commitment_id, session["user_id"])

    if not success:
        return jsonify({"error": "Commitment not found or unauthorized"}), 404

    return jsonify({"success": True})


@app.route("/api/predict_priority", methods=["POST"])
def predict_priority_api():
    """Predict priority of a commitment (API)."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    subject = data.get("subject", "").strip()
    description = data.get("description", "").strip()
    deadline_str = data.get("deadline")

    deadline_dt = None
    if deadline_str:
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
        except Exception:
            pass

    text = f"{subject} {description}".strip()
    priority = predict_priority(text, deadline_dt)

    return jsonify({"priority": priority})


@app.route("/logout", methods=["POST"])
def logout():
    """Clear session data."""
    session.clear()
    return jsonify({"success": True})


@app.route("/api/mark_urgent_shown", methods=["POST"])
def mark_urgent_shown():
    """Mark urgent commitments as shown in this session."""
    if "user_id" in session:
        session["urgent_shown"] = True
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
