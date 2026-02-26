# Math Tutor DC – Backend API
# Deployed on Render.com: https://math-tutor-backend-y3uz.onrender.com
#
# Endpoints (existing, unchanged):
#   POST /contact           – Accept tutoring request, send email via Resend, log to DB
#
# Endpoints (admin):
#   GET  /ping              – Health check / wake-up for Render free-tier sleep
#   POST /admin/login       – Validate password, return JWT
#   GET  /admin/submissions – List all submissions (JWT required)
#   GET  /admin/stats       – Source analytics (JWT required)
#
# Endpoints (tutor portal):
#   POST /tutor/login       – Validate tutor password, return JWT

import os
import time
import sqlite3
import requests
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import bcrypt
import jwt

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow all origins (same as original)

# =============================================================================
# ENV VARS
# =============================================================================

# --- Existing vars (unchanged) ---
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_TO       = os.environ.get("EMAIL_TO")  # e.g. "you@gmail.com,partner@gmail.com"

# --- New vars (admin + tutor portal) ---
# Generate bcrypt hashes with:
#   python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
# Generate JWT_SECRET with:
#   python -c "import secrets; print(secrets.token_hex(48))"
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")
TUTOR_PASSWORD_HASH = os.environ.get("TUTOR_PASSWORD_HASH", "")
JWT_SECRET          = os.environ.get("JWT_SECRET", "")

if not RESEND_API_KEY:
    raise Exception("Missing RESEND_API_KEY env var in Render!")
if not EMAIL_TO:
    raise Exception("Missing EMAIL_TO env var in Render!")

# =============================================================================
# DATABASE  (SQLite – stores a local copy of every submission)
# =============================================================================
# Render free tier has an ephemeral filesystem, so this resets on redeploy.
# The canonical record is still the email that Resend sends.
# Upgrade to Render PostgreSQL for permanent persistence.

DB_PATH = os.environ.get("DB_PATH", "submissions.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id         INTEGER  PRIMARY KEY AUTOINCREMENT,
                name       TEXT     NOT NULL,
                email      TEXT     NOT NULL,
                phone      TEXT     DEFAULT '',
                class      TEXT     DEFAULT '',
                mode       TEXT     DEFAULT '',
                time       TEXT     DEFAULT '',
                message    TEXT     DEFAULT '',
                src        TEXT     DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


init_db()

# =============================================================================
# RATE LIMITING  (identical to original)
# =============================================================================

RATE_LIMIT_MAX    = 2      # max submissions per IP
RATE_LIMIT_WINDOW = 3600   # seconds (1 hour)
rate_limit_store  = {}     # ip → [timestamps]


def get_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def check_rate_limit(ip):
    now = time.time()
    timestamps = rate_limit_store.get(ip, [])
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        return False
    timestamps.append(now)
    rate_limit_store[ip] = timestamps
    return True

# =============================================================================
# RESEND EMAIL  (identical to original, with optional src line appended)
# =============================================================================


def send_email_via_resend(name, email, phone, course, mode, time_pref, message, src=""):
    """Send email using Resend API. Unchanged from original except optional src line."""
    src_line = f"\nSource: {src}" if src else ""

    payload = {
        "from": "Math Tutor DC <onboarding@resend.dev>",
        "to":   EMAIL_TO.split(","),
        "subject": f"New Math Tutoring Request{f' [{src}]' if src else ''}",
        "text": f"""
New tutoring request:

Name: {name}
Email: {email}
Phone: {phone}
Class: {course}
Mode: {mode}
Preferred time: {time_pref}{src_line}

Additional details:
{message}
""",
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    r = requests.post("https://api.resend.com/emails", json=payload, headers=headers)

    if r.status_code >= 300:
        print("[EMAIL ERROR]", r.text)
        return False

    print("[EMAIL SUCCESS] Sent via Resend")
    return True

# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================


@app.get("/ping")
def ping():
    """Health check. The admin page hits this on load to wake up Render's free tier."""
    return jsonify({"ok": True, "ts": time.time()})


@app.post("/contact")
def contact():
    """
    Accept a tutoring request. Identical behaviour to the original endpoint.
    The only addition: an optional `src` field is logged alongside the lead
    and appended to the email so campaign attribution is visible in your inbox.
    """
    data = request.get_json() or {}
    ip   = get_client_ip()

    if not check_rate_limit(ip):
        print(f"[RATE LIMIT] Blocked IP: {ip}")
        return jsonify({"error": "Too many submissions. Please try again in 1 hour."}), 429

    required = ["name", "email", "phone", "class", "mode", "time", "message"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        print("[VALIDATION ERROR]", missing)
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    name      = data["name"]
    email     = data["email"]
    phone     = data["phone"]
    course    = data["class"]
    mode      = data["mode"]
    time_pref = data["time"]
    message   = data["message"]
    src       = data.get("src", "")[:64]  # optional; capped to 64 chars

    print(f"[CONTACT] {name} <{email}> | Course={course} | src={src or 'direct'} | IP={ip}")

    # Store in DB before emailing so the lead is never lost if Resend fails
    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO submissions (name, email, phone, class, mode, time, message, src)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, email, phone, course, mode, time_pref, message, src),
            )
            conn.commit()
    except Exception as e:
        print("[DB ERROR]", e)  # non-fatal – proceed to email

    ok = send_email_via_resend(name, email, phone, course, mode, time_pref, message, src)
    if not ok:
        return jsonify({"error": "Email send failed."}), 500

    return jsonify({"ok": True})

# =============================================================================
# ADMIN AUTH
# =============================================================================


@app.post("/admin/login")
def admin_login():
    """
    Validate admin password against the bcrypt hash stored in ADMIN_PASSWORD_HASH.
    Returns a JWT valid for 8 hours on success.
    """
    data     = request.get_json() or {}
    password = data.get("password", "")

    if not password:
        return jsonify({"error": "Password required"}), 400

    # Trigger: env vars not configured
    # Why: fail loudly so misconfiguration is obvious during setup
    # Outcome: 503 instead of a misleading 401
    if not ADMIN_PASSWORD_HASH or not JWT_SECRET:
        print("[ADMIN] ADMIN_PASSWORD_HASH or JWT_SECRET not set")
        return jsonify({"error": "Admin not configured on server"}), 503

    valid = bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode())
    if not valid:
        return jsonify({"error": "Invalid password"}), 401

    token = jwt.encode(
        {"admin": True, "exp": datetime.now(timezone.utc) + timedelta(hours=8)},
        JWT_SECRET,
        algorithm="HS256",
    )
    return jsonify({"token": token})


def require_auth(f):
    """Decorator: verify JWT on admin routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized – login required"}), 401
        try:
            jwt.decode(auth[7:], JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired – please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# =============================================================================
# TUTOR PORTAL AUTH
# =============================================================================


@app.post("/tutor/login")
def tutor_login():
    """
    Validate tutor password against TUTOR_PASSWORD_HASH.
    Issues a JWT with role='tutor', valid for 12 hours.
    Kept separate from admin so each portal has its own password.
    """
    data     = request.get_json() or {}
    password = data.get("password", "")

    if not password:
        return jsonify({"error": "Password required"}), 400

    if not TUTOR_PASSWORD_HASH or not JWT_SECRET:
        print("[TUTOR] TUTOR_PASSWORD_HASH or JWT_SECRET not set")
        return jsonify({"error": "Tutor portal not configured on server"}), 503

    valid = bcrypt.checkpw(password.encode(), TUTOR_PASSWORD_HASH.encode())
    if not valid:
        return jsonify({"error": "Invalid password"}), 401

    token = jwt.encode(
        {"role": "tutor", "exp": datetime.now(timezone.utc) + timedelta(hours=12)},
        JWT_SECRET,
        algorithm="HS256",
    )
    return jsonify({"token": token})

# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================


@app.get("/admin/submissions")
@require_auth
def admin_submissions():
    """Return all submissions, newest first."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM submissions ORDER BY created_at DESC LIMIT 1000"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/admin/stats")
@require_auth
def admin_stats():
    """Return aggregate stats and per-source breakdown for QR attribution."""
    with get_db() as conn:
        total  = conn.execute("SELECT COUNT(*) AS c FROM submissions").fetchone()["c"]
        recent = conn.execute(
            "SELECT COUNT(*) AS c FROM submissions WHERE created_at > datetime('now', '-7 days')"
        ).fetchone()["c"]
        by_src = conn.execute("""
            SELECT   COALESCE(NULLIF(src, ''), 'direct') AS source,
                     COUNT(*)                             AS count,
                     MAX(created_at)                      AS last_seen
            FROM     submissions
            GROUP BY source
            ORDER BY count DESC
        """).fetchall()

    return jsonify({
        "total":     total,
        "recent_7d": recent,
        "by_source": [dict(r) for r in by_src],
    })

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
