# Math Tutor DC – Backend API
# Deployed on Render.com: https://math-tutor-backend-y3uz.onrender.com
#
# Endpoints (public):
#   GET  /ping                – Health check / wake Render free-tier sleep
#   POST /contact             – Accept form, email via Resend, log lead to DB
#
# Endpoints (admin – JWT required):
#   POST /admin/login         – Validate password, return JWT
#   GET  /admin/leads         – All leads (newest first)
#   GET  /admin/submissions   – Backward-compat alias for /admin/leads
#   GET  /admin/stats         – Source analytics + aggregate counts
#   GET  /admin/clients       – All clients
#   GET  /admin/tutors        – All tutors
#   GET  /admin/financials    – Income statement + lead funnel
#   GET  /admin/db/export     – Download the SQLite database file
#
# Endpoints (tutor portal):
#   POST /tutor/login         – Validate tutor password, return JWT

import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import bcrypt
import jwt

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    Text, Date, DateTime, ForeignKey, func, select, text,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

# Google Sheets API (optional – only required for /admin/sync-sheets)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build as goog_build
    HAS_GOOGLE_SHEETS = True
except ImportError:
    HAS_GOOGLE_SHEETS = False

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow all origins – required by GitHub Pages frontend

# =============================================================================
# ENV VARS
# =============================================================================

# --- Existing vars (unchanged from original backend) ---
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_TO       = os.environ.get("EMAIL_TO")  # comma-separated recipients

# --- Auth vars (set in Render dashboard only, never committed to git) ---
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")
TUTOR_PASSWORD_HASH = os.environ.get("TUTOR_PASSWORD_HASH", "")
JWT_SECRET          = os.environ.get("JWT_SECRET", "")

if not RESEND_API_KEY:
    raise Exception("Missing RESEND_API_KEY env var!")
if not EMAIL_TO:
    raise Exception("Missing EMAIL_TO env var!")

# =============================================================================
# DATABASE  (SQLAlchemy + SQLite)
# =============================================================================
# The SQLite file lives on the Render server's filesystem.
#
# Render free tier: ephemeral – the file resets on every redeploy. Use the
#   /admin/db/export endpoint often to pull a local copy. For durable storage
#   set DB_PATH=/data/math_tutor.db and enable Render Persistent Disk.
#
# Tables:
#   leads              – every contact form submission (top of the funnel)
#   clients            – leads that converted to paying clients
#   tutors             – tutors employed by the business
#   tutoring_sessions  – individual sessions linking a client and a tutor
#   payments           – cash in (from clients) or cash out (to tutors)
#   expenses           – operating costs not tied to a session (marketing, tools…)

DB_PATH      = os.environ.get("DB_PATH", "math_tutor.db")
engine       = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Lead(Base):
    """
    Every contact form submission.  The raw top of the funnel.
    status tracks where the prospect is in the sales process.
    """
    __tablename__ = "leads"

    id         = Column(Integer,  primary_key=True)
    name       = Column(String,   nullable=False)
    email      = Column(String,   nullable=False)
    phone      = Column(String,   default="")
    course     = Column(String,   default="")   # subject/class requested
    mode       = Column(String,   default="")   # online / in-person
    time_pref  = Column(String,   default="")
    message    = Column(Text,     default="")
    src        = Column(String,   default="")   # QR / campaign attribution key
    status     = Column(String,   default="new")  # new | contacted | converted | lost
    created_at = Column(DateTime, default=datetime.utcnow)
    tally_id   = Column(String,   nullable=True, unique=False)  # Tally submission ID (dedup key)

    # Trigger: lead has been converted to a paying client
    # Why: links the original inquiry to the client row without losing lead history
    # Outcome: lead.client gives full client context; client.leads shows acquisition history
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client    = relationship("Client", back_populates="leads")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "phone": self.phone,
            # Key is "class" (not "course") so existing admin.html JS works unchanged
            "class": self.course,
            "mode": self.mode, "time": self.time_pref, "message": self.message,
            "src": self.src, "status": self.status, "client_id": self.client_id,
            "tally_id": self.tally_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Client(Base):
    """A converted lead – someone who has paid for at least one session."""
    __tablename__ = "clients"

    id         = Column(Integer,  primary_key=True)
    name       = Column(String,   nullable=False)
    email      = Column(String,   nullable=False)
    phone      = Column(String,   default="")
    notes      = Column(Text,     default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    leads    = relationship("Lead",            back_populates="client")
    sessions = relationship("TutoringSession", back_populates="client")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "phone": self.phone, "notes": self.notes,
            "session_count": len(self.sessions) if self.sessions else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Tutor(Base):
    """A tutor employed by the business to deliver sessions."""
    __tablename__ = "tutors"

    id         = Column(Integer,  primary_key=True)
    name       = Column(String,   nullable=False)
    email      = Column(String,   nullable=False)
    phone      = Column(String,   default="")
    rate               = Column(Float,   default=0.0)   # default $/hr paid to this tutor
    notes              = Column(Text,    default="")
    active             = Column(Boolean, default=True)
    # Subjects this tutor can teach – comma-separated course names.
    # Example: "Calculus I–III, Linear Algebra, Probability & Statistics"
    subjects           = Column(Text,    default="")
    # Earliest time the tutor is available to start a session (24-hour "HH:MM" or
    # 12-hour "H:MM AM/PM").  Used for matching against a lead's preferred start time.
    # Example: "15:00"  means available from 3 PM onward.
    earliest_available = Column(String,  default="")
    # Tally Submission ID stored here so the sync endpoint can skip rows already
    # imported without relying on email alone (supports re-submissions with edits).
    tally_id           = Column(String,  nullable=True)
    created_at         = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("TutoringSession", back_populates="tutor")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "phone": self.phone, "rate": self.rate, "notes": self.notes,
            "active": self.active,
            "subjects": self.subjects,
            "earliest_available": self.earliest_available,
            "tally_id": self.tally_id,
            "session_count": len(self.sessions) if self.sessions else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TutoringSession(Base):
    """One tutoring appointment: a client, a tutor, a date, and the rates charged/paid."""
    __tablename__ = "tutoring_sessions"

    id           = Column(Integer,  primary_key=True)
    client_id    = Column(Integer,  ForeignKey("clients.id"), nullable=False)
    tutor_id     = Column(Integer,  ForeignKey("tutors.id"),  nullable=False)
    course       = Column(String,   default="")
    date         = Column(Date)
    duration_hrs = Column(Float,    default=1.0)
    client_rate  = Column(Float,    default=0.0)  # $/hr charged to client
    tutor_rate   = Column(Float,    default=0.0)  # $/hr paid to tutor
    notes        = Column(Text,     default="")
    created_at   = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="sessions")
    tutor  = relationship("Tutor",  back_populates="sessions")

    def to_dict(self):
        return {
            "id": self.id, "client_id": self.client_id, "tutor_id": self.tutor_id,
            "course": self.course,
            "date": self.date.isoformat() if self.date else None,
            "duration_hrs": self.duration_hrs,
            "client_rate": self.client_rate, "tutor_rate": self.tutor_rate,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(Base):
    """
    A cash movement.
      direction='in'  → received from a client  (counts as Revenue)
      direction='out' → paid to a tutor          (counts as COGS)
    """
    __tablename__ = "payments"

    id         = Column(Integer,  primary_key=True)
    session_id = Column(Integer,  ForeignKey("tutoring_sessions.id"), nullable=True)
    amount     = Column(Float,    default=0.0)
    direction  = Column(String,   default="in")   # 'in' | 'out'
    method     = Column(String,   default="")     # venmo / cash / zelle / card
    date       = Column(Date)
    notes      = Column(Text,     default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "session_id": self.session_id, "amount": self.amount,
            "direction": self.direction, "method": self.method,
            "date": self.date.isoformat() if self.date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Expense(Base):
    """An operating cost not tied to a session (marketing, software, travel, etc.)."""
    __tablename__ = "expenses"

    id          = Column(Integer,  primary_key=True)
    category    = Column(String,   default="")   # marketing | tools | travel | misc
    description = Column(String,   default="")
    amount      = Column(Float,    default=0.0)
    date        = Column(Date)
    notes       = Column(Text,     default="")
    created_at  = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "category": self.category, "description": self.description,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# create_all only adds missing tables; it never drops or alters existing ones.
# Safe to redeploy: existing data is preserved (on non-ephemeral storage).
Base.metadata.create_all(engine)


def run_migrations(eng):
    """
    Add columns that are new since the initial schema.
    SQLite's ALTER TABLE can only add columns, so this is safe to run on every
    startup.  Each ALTER is wrapped in try/except so it's a no-op if the
    column already exists.
    """
    stmts = [
        "ALTER TABLE leads   ADD COLUMN tally_id            VARCHAR",
        "ALTER TABLE tutors  ADD COLUMN subjects            TEXT    DEFAULT ''",
        "ALTER TABLE tutors  ADD COLUMN earliest_available  VARCHAR DEFAULT ''",
        "ALTER TABLE tutors  ADD COLUMN tally_id            VARCHAR",
    ]
    with eng.connect() as conn:
        for stmt in stmts:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # column already exists – safe to ignore


run_migrations(engine)


# =============================================================================
# RATE LIMITING  (identical to original)
# =============================================================================

RATE_LIMIT_MAX    = 2      # max submissions per IP per window
RATE_LIMIT_WINDOW = 3600   # seconds
rate_limit_store  = {}     # ip → [timestamps]


def get_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    return xff.split(",")[0].strip() if xff else (request.remote_addr or "unknown")


def check_rate_limit(ip):
    now        = time.time()
    timestamps = [t for t in rate_limit_store.get(ip, []) if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        return False
    timestamps.append(now)
    rate_limit_store[ip] = timestamps
    return True


# =============================================================================
# CLIENT EMAIL DRAFT TEMPLATE
# =============================================================================
# This is the draft email included at the bottom of every new-lead notification.
# Edit the body below to change the default message sent to new clients.
#
# Supported placeholders (all safe to leave in – missing values show as "—"):
#   {client_name}     Lead's full name
#   {course}          Subject they need help with
#   {mode}            "In-person (DC area)" or "Online (Zoom)"
#   {time_pref}       Their preferred start time (e.g. "3:00 PM")
#   {tutor_name}      Matched tutor's name
#   {tutor_subjects}  Tutor's listed subjects
#   {tutor_rate}      Tutor's hourly rate (number)
#
# See README → "Client email draft template" to find this section quickly.
# =============================================================================

CLIENT_EMAIL_DRAFT = """\
Hi {client_name},

Thank you for reaching out to Math Tutor DC! We received your request for \
help with {course} and we're excited to connect you with a tutor.

We'd like to match you with {tutor_name}, who specializes in {tutor_subjects} \
and is available for {mode} sessions starting at {time_pref}.

Our rate is ${tutor_rate}/hr. Please reply to confirm your first session, or \
let us know if you have any questions!

Looking forward to working with you,
Math Tutor DC
"""


# =============================================================================
# TUTOR MATCHING HELPERS
# =============================================================================

def parse_time_str(time_str):
    """
    Convert a time string such as '3:00 PM' or '15:00' into minutes since
    midnight.  Returns None if the string cannot be parsed.
    """
    if not time_str:
        return None
    s = time_str.strip()
    for fmt in ("%I:%M %p", "%H:%M", "%I %p", "%I:%M%p", "%I%p"):
        try:
            t = datetime.strptime(s, fmt)
            return t.hour * 60 + t.minute
        except ValueError:
            continue
    return None


def match_tutor(course, time_pref, db):
    """
    Find the best active tutor for a given course and preferred start time.

    Scoring (higher is better):
      +10  tutor's subjects list contains the requested course (substring match,
           case-insensitive)
      +5   tutor's earliest_available is at or before the lead's preferred time
           (i.e. the tutor CAN start when the lead wants to start)

    Ties broken by hourly rate ascending (cheapest match first).
    Falls back to the first active tutor alphabetically if no scores > 0.
    Returns None when there are no active tutors in the database.

    Note on time semantics: the lead's time_pref is the EARLIEST they can start
    on a given day.  A tutor matches on time when tutor.earliest_available <=
    lead.time_pref (tutor is free by the time the lead is available).
    """
    tutors = db.execute(
        select(Tutor).where(Tutor.active == True).order_by(Tutor.name)
    ).scalars().all()

    if not tutors:
        return None

    lead_mins  = parse_time_str(time_pref)
    course_lc  = (course or "").lower().strip()

    scored = []
    for t in tutors:
        score    = 0
        subjects = [s.strip().lower() for s in (t.subjects or "").split(",") if s.strip()]

        # Course match: any subject overlaps with the requested course
        for subj in subjects:
            if course_lc and (course_lc in subj or subj in course_lc):
                score += 10
                break

        # Availability match: tutor can start at or before lead's preferred time
        if lead_mins is not None and t.earliest_available:
            tutor_mins = parse_time_str(t.earliest_available)
            if tutor_mins is not None and tutor_mins <= lead_mins:
                score += 5

        scored.append((score, t.rate or 0, t))

    # Sort: highest score first, then cheapest rate
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2]


# =============================================================================
# RESEND EMAIL
# =============================================================================

def send_email_via_resend(name, email, phone, course, mode, time_pref, message, src="",
                          matched_tutor=None):
    """
    Send a new-lead notification to the admin via Resend.
    Includes:
      1. Lead details
      2. Best-matched tutor (if any active tutors exist)
      3. A pre-drafted email ready to copy/paste and send to the client
    """
    src_line = f"\nSource: {src}" if src else ""

    # ── Tutor match block ────────────────────────────────────────────────────
    SEP = "=" * 54
    if matched_tutor:
        avail = matched_tutor.earliest_available or "not set"
        tutor_block = (
            f"\n{SEP}\n"
            f"SUGGESTED TUTOR\n"
            f"{SEP}\n"
            f"Name:      {matched_tutor.name}\n"
            f"Email:     {matched_tutor.email}\n"
            f"Subjects:  {matched_tutor.subjects or '(not listed)'}\n"
            f"Rate:      ${matched_tutor.rate or '?'}/hr\n"
            f"Earliest:  {avail}\n"
            f"{SEP}\n"
        )
        tutor_name     = matched_tutor.name
        tutor_subjects = matched_tutor.subjects or "various subjects"
        tutor_rate     = matched_tutor.rate or 40
    else:
        tutor_block = (
            f"\n{SEP}\n"
            f"SUGGESTED TUTOR\n"
            f"{SEP}\n"
            f"No active tutors in the database yet.\n"
            f"Add tutors via Export DB → DB Browser → tutors table.\n"
            f"{SEP}\n"
        )
        tutor_name     = "a member of our team"
        tutor_subjects = "math and related subjects"
        tutor_rate     = 40

    # ── Draft email to client ────────────────────────────────────────────────
    draft_body = CLIENT_EMAIL_DRAFT.format(
        client_name    = name,
        course         = course   or "your subject",
        mode           = mode     or "in-person or online",
        time_pref      = time_pref or "your preferred time",
        tutor_name     = tutor_name,
        tutor_subjects = tutor_subjects,
        tutor_rate     = tutor_rate,
    )
    draft_block = (
        f"\n{SEP}\n"
        f"DRAFT EMAIL TO CLIENT  (copy/paste → send from your inbox)\n"
        f"{SEP}\n"
        f"To:      {email}\n"
        f"Subject: Your Math Tutor DC Request\n\n"
        f"{draft_body}"
        f"{SEP}\n"
    )

    # ── Full notification body ───────────────────────────────────────────────
    body = (
        f"New tutoring request:\n\n"
        f"Name:   {name}\n"
        f"Email:  {email}\n"
        f"Phone:  {phone}\n"
        f"Course: {course}\n"
        f"Mode:   {mode}\n"
        f"Time:   {time_pref}{src_line}\n\n"
        f"Additional details:\n{message}\n"
        f"{tutor_block}"
        f"{draft_block}"
    )

    payload = {
        "from":    "Math Tutor DC <onboarding@resend.dev>",
        "to":      EMAIL_TO.split(","),
        "subject": f"New Tutoring Request – {name}{f' [{src}]' if src else ''}",
        "text":    body,
    }
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type":  "application/json",
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
    """Health check. Admin page hits this on load to pre-warm Render's free tier."""
    return jsonify({"ok": True, "ts": time.time()})


@app.post("/contact")
def contact():
    """
    Accept a tutoring request. Identical behaviour to the original endpoint.
    Logs to the leads table (SQLAlchemy) before emailing so the record is
    never lost if Resend fails.
    """
    data = request.get_json() or {}
    ip   = get_client_ip()

    if not check_rate_limit(ip):
        print(f"[RATE LIMIT] Blocked IP: {ip}")
        return jsonify({"error": "Too many submissions. Please try again in 1 hour."}), 429

    required = ["name", "email", "phone", "class", "mode", "time", "message"]
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    name      = data["name"]
    email     = data["email"]
    phone     = data["phone"]
    course    = data["class"]
    mode      = data["mode"]
    time_pref = data["time"]
    message   = data["message"]
    src       = data.get("src", "")[:64]  # optional; capped to prevent abuse

    print(f"[CONTACT] {name} <{email}> | course={course} | src={src or 'direct'} | IP={ip}")

    tutor = None
    try:
        with SessionLocal() as db:
            tutor = match_tutor(course, time_pref, db)
            lead  = Lead(
                name=name, email=email, phone=phone, course=course,
                mode=mode, time_pref=time_pref, message=message, src=src,
            )
            db.add(lead)
            db.commit()
    except Exception as e:
        print("[DB ERROR]", e)  # non-fatal – proceed to email

    ok = send_email_via_resend(name, email, phone, course, mode, time_pref, message, src,
                               matched_tutor=tutor)
    if not ok:
        return jsonify({"error": "Email send failed."}), 500

    return jsonify({"ok": True})


# =============================================================================
# ADMIN AUTH
# =============================================================================

@app.post("/admin/login")
def admin_login():
    """Validate admin password → return 8-hour JWT on success."""
    data     = request.get_json() or {}
    password = data.get("password", "")
    if not password:
        return jsonify({"error": "Password required"}), 400
    # Trigger: env vars missing → fail loudly so misconfiguration is obvious
    # Why: a silent 401 loop during setup wastes hours of debugging time
    # Outcome: 503 with a clear message pointing to Render's env dashboard
    if not ADMIN_PASSWORD_HASH or not JWT_SECRET:
        print("[ADMIN] ADMIN_PASSWORD_HASH or JWT_SECRET not set")
        return jsonify({"error": "Admin not configured on server"}), 503
    if not bcrypt.checkpw(password.encode(), ADMIN_PASSWORD_HASH.encode()):
        return jsonify({"error": "Invalid password"}), 401
    token = jwt.encode(
        {"admin": True, "exp": datetime.now(timezone.utc) + timedelta(hours=8)},
        JWT_SECRET, algorithm="HS256",
    )
    return jsonify({"token": token})


def require_auth(f):
    """
    Decorator: verify JWT signature and expiry on admin-only routes.
    Accepts the token via Authorization header OR ?token= query param.
    The query-param path exists for the /admin/db/export endpoint, which
    is triggered by a browser navigation that cannot set custom headers.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            raw_token = auth[7:]
        else:
            # Fallback: query param used by browser-navigation download links
            raw_token = request.args.get("token", "")

        if not raw_token:
            return jsonify({"error": "Unauthorized – login required"}), 401
        try:
            jwt.decode(raw_token, JWT_SECRET, algorithms=["HS256"])
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
    """Validate tutor password → return 12-hour JWT on success."""
    data     = request.get_json() or {}
    password = data.get("password", "")
    if not password:
        return jsonify({"error": "Password required"}), 400
    if not TUTOR_PASSWORD_HASH or not JWT_SECRET:
        print("[TUTOR] TUTOR_PASSWORD_HASH or JWT_SECRET not set")
        return jsonify({"error": "Tutor portal not configured on server"}), 503
    if not bcrypt.checkpw(password.encode(), TUTOR_PASSWORD_HASH.encode()):
        return jsonify({"error": "Invalid password"}), 401
    token = jwt.encode(
        {"role": "tutor", "exp": datetime.now(timezone.utc) + timedelta(hours=12)},
        JWT_SECRET, algorithm="HS256",
    )
    return jsonify({"token": token})


# =============================================================================
# ADMIN ENDPOINTS – LEADS
# =============================================================================

@app.get("/admin/leads")
@require_auth
def admin_leads():
    """All leads, newest first. The primary leads endpoint."""
    with SessionLocal() as db:
        rows = db.execute(
            select(Lead).order_by(Lead.created_at.desc()).limit(1000)
        ).scalars().all()
    return jsonify([r.to_dict() for r in rows])


@app.get("/admin/submissions")
@require_auth
def admin_submissions():
    """Backward-compat alias for /admin/leads (admin.html JS calls this URL)."""
    return admin_leads()


@app.get("/admin/stats")
@require_auth
def admin_stats():
    """Aggregate lead counts and per-source breakdown for QR attribution."""
    with SessionLocal() as db:
        total  = db.execute(select(func.count()).select_from(Lead)).scalar() or 0
        recent = db.execute(
            select(func.count()).select_from(Lead)
            .where(Lead.created_at > func.datetime("now", "-7 days"))
        ).scalar() or 0

        by_src_rows = db.execute(
            select(
                func.coalesce(func.nullif(Lead.src, ""), "direct").label("source"),
                func.count().label("count"),
                func.max(Lead.created_at).label("last_seen"),
            )
            .group_by("source")
            .order_by(func.count().desc())
        ).fetchall()

    return jsonify({
        "total":     total,
        "recent_7d": recent,
        "by_source": [
            {"source": r.source, "count": r.count, "last_seen": r.last_seen}
            for r in by_src_rows
        ],
    })


# =============================================================================
# ADMIN ENDPOINTS – CLIENTS & TUTORS
# =============================================================================

@app.get("/admin/clients")
@require_auth
def admin_clients():
    """All clients, most recently added first."""
    with SessionLocal() as db:
        rows = db.execute(
            select(Client).order_by(Client.created_at.desc())
        ).scalars().all()
    return jsonify([r.to_dict() for r in rows])


@app.get("/admin/tutors")
@require_auth
def admin_tutors():
    """All tutors, sorted by name."""
    with SessionLocal() as db:
        rows = db.execute(
            select(Tutor).order_by(Tutor.name)
        ).scalars().all()
    return jsonify([r.to_dict() for r in rows])


# =============================================================================
# ADMIN ENDPOINTS – FINANCIALS
# =============================================================================

@app.get("/admin/financials")
@require_auth
def admin_financials():
    """
    Income statement derived from logged payments + expenses.

    Revenue      = SUM of payments where direction='in'  (client → us)
    COGS         = SUM of payments where direction='out' (us → tutor)
    Gross Profit = Revenue − COGS
    OpEx         = SUM of all expense records
    Net Income   = Gross Profit − OpEx

    Also returns the lead funnel (counts by status) and a monthly
    revenue/COGS breakdown for trend analysis.
    """
    with SessionLocal() as db:
        revenue = float(db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.direction == "in")
        ).scalar())

        cogs = float(db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .where(Payment.direction == "out")
        ).scalar())

        opex = float(db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0))
        ).scalar())

        # Lead funnel: count each status bucket
        funnel_rows = db.execute(
            select(Lead.status, func.count().label("count"))
            .group_by(Lead.status)
        ).fetchall()
        funnel = {"new": 0, "contacted": 0, "converted": 0, "lost": 0}
        for row in funnel_rows:
            if row.status in funnel:
                funnel[row.status] = row.count

        total_leads = db.execute(select(func.count()).select_from(Lead)).scalar() or 0

        # Monthly revenue trend (SQLite strftime groups by YYYY-MM)
        monthly_rev = db.execute(
            select(
                func.strftime("%Y-%m", Payment.date).label("month"),
                func.sum(Payment.amount).label("total"),
            )
            .where(Payment.direction == "in")
            .where(Payment.date.isnot(None))
            .group_by("month")
            .order_by("month")
        ).fetchall()

        monthly_cogs = db.execute(
            select(
                func.strftime("%Y-%m", Payment.date).label("month"),
                func.sum(Payment.amount).label("total"),
            )
            .where(Payment.direction == "out")
            .where(Payment.date.isnot(None))
            .group_by("month")
            .order_by("month")
        ).fetchall()

    gross_profit = revenue - cogs
    net_income   = gross_profit - opex

    return jsonify({
        "income_statement": {
            "revenue":      revenue,
            "cogs":         cogs,
            "gross_profit": gross_profit,
            "opex":         opex,
            "net_income":   net_income,
        },
        "lead_funnel": {
            "total":     total_leads,
            "new":       funnel["new"],
            "contacted": funnel["contacted"],
            "converted": funnel["converted"],
            "lost":      funnel["lost"],
        },
        "monthly_revenue": [
            {"month": r.month, "total": float(r.total or 0)} for r in monthly_rev
        ],
        "monthly_cogs": [
            {"month": r.month, "total": float(r.total or 0)} for r in monthly_cogs
        ],
    })


# =============================================================================
# ADMIN ENDPOINTS – DATABASE EXPORT
# =============================================================================

@app.get("/admin/db/export")
@require_auth
def admin_db_export():
    """
    Stream the raw SQLite file as a browser download.
    Use this to pull a local copy for offline analysis, backup, or
    to open in DB Browser for SQLite to manually enter session/payment data.

    Reminder: Render free tier resets the file on every redeploy.
    Download before deploying, or use Render Persistent Disk + DB_PATH=/data/math_tutor.db.
    """
    abs_path = os.path.abspath(DB_PATH)
    if not os.path.exists(abs_path):
        return jsonify({"error": "Database file not found on server"}), 404
    return send_file(
        abs_path,
        as_attachment=True,
        download_name="math_tutor.db",
        mimetype="application/octet-stream",
    )


# =============================================================================
# ADMIN ENDPOINTS – GOOGLE SHEETS SYNC  (tutor onboarding)
# =============================================================================
#
# Flow:
#   Tutor fills out Tally application form
#   → Tally writes each submission as a row in Google Sheets (native integration)
#   → Admin clicks "⟳ Sync Tally" in the dashboard
#   → POST /admin/sync-sheets reads new rows and inserts them into the tutors table
#   → New tutors are created as INACTIVE (active=0) pending admin review
#   → Admin reviews new tutors in the Tutors table and activates them manually
#
# Client intake (contact form on index.html) is handled by POST /contact, NOT here.
#
# Required env vars:
#   GOOGLE_CREDS_JSON   Full JSON of a Google Service Account key file.
#                       Go to Google Cloud Console → IAM → Service Accounts →
#                       Create key (JSON) → paste entire file content here.
#                       Share the Google Sheet with the service account email.
#   GOOGLE_SHEET_ID     The spreadsheet ID from its URL:
#                       https://docs.google.com/spreadsheets/d/<ID>/edit
#
# Optional env vars (defaults match Tally's auto-generated column names):
#   GOOGLE_SHEET_NAME   Tab name (default: Sheet1)
#   COL_TALLY_ID        Submission ID column header  (default: "Submission ID")
#   COL_NAME            Name column header            (default: "Name")
#   COL_EMAIL           Email column header           (default: "Email")
#   COL_PHONE           Phone column header           (default: "Phone")
#   COL_SUBJECTS        Subjects/courses they teach   (default: "Subjects")
#   COL_AVAILABLE       Earliest available time       (default: "Earliest Available")
#   COL_RATE            Hourly rate requested         (default: "Rate")
#   COL_NOTES           Additional notes / bio        (default: "Notes")


def _sheets_service():
    """Build and return an authenticated Google Sheets API service object."""
    if not HAS_GOOGLE_SHEETS:
        raise RuntimeError(
            "Google API libraries not installed. "
            "Run: pip install google-auth google-auth-httplib2 google-api-python-client"
        )
    raw = os.environ.get("GOOGLE_CREDS_JSON", "").strip()
    if not raw:
        raise RuntimeError(
            "GOOGLE_CREDS_JSON env var is not set. "
            "Paste the full service account JSON into Render's Environment dashboard."
        )
    try:
        creds_dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GOOGLE_CREDS_JSON is not valid JSON: {exc}") from exc

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    return goog_build("sheets", "v4", credentials=creds)


@app.post("/admin/sync-sheets")
@require_auth
def admin_sync_sheets():
    """
    Pull new tutor applications from Google Sheets and import them into the
    tutors table.  New tutors are created as INACTIVE (active=False) so the
    admin can review each one and activate them when ready.

    Deduplication uses tally_id first (when present in the sheet), then falls
    back to email so re-syncing the same sheet is always safe.

    This endpoint does NOT send per-row Resend emails.  The admin sees the
    summary in the dashboard UI and can review new tutors in the Tutors table.
    """
    sheet_id   = os.environ.get("GOOGLE_SHEET_ID",   "").strip()
    sheet_name = os.environ.get("GOOGLE_SHEET_NAME",  "Sheet1").strip()

    if not sheet_id:
        return jsonify({
            "error": "GOOGLE_SHEET_ID env var is not set. Add it in Render's Environment dashboard."
        }), 503

    # Column name mapping – every key can be overridden via an env var.
    # Set the matching env var in Render if your Tally form uses different labels.
    COL = {
        "tally_id":  os.environ.get("COL_TALLY_ID",  "Submission ID"),
        "name":      os.environ.get("COL_NAME",      "Name"),
        "email":     os.environ.get("COL_EMAIL",     "Email"),
        "phone":     os.environ.get("COL_PHONE",     "Phone"),
        "subjects":  os.environ.get("COL_SUBJECTS",  "Subjects"),
        "available": os.environ.get("COL_AVAILABLE", "Earliest Available"),
        "rate":      os.environ.get("COL_RATE",      "Rate"),
        "notes":     os.environ.get("COL_NOTES",     "Notes"),
    }

    try:
        service = _sheets_service()
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503

    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f"{sheet_name}!A:Z",
        ).execute()
        values = result.get("values", [])
    except Exception as exc:
        return jsonify({"error": f"Could not read Google Sheet: {exc}"}), 500

    if len(values) < 2:
        return jsonify({
            "imported": 0, "skipped": 0,
            "message": "Sheet is empty or contains only a header row.",
        })

    headers = [h.strip() for h in values[0]]

    def cell(row, key):
        """Return the trimmed cell value for a named column, or '' if missing."""
        col_name = COL[key]
        try:
            idx = headers.index(col_name)
        except ValueError:
            return ""
        return row[idx].strip() if idx < len(row) else ""

    imported = 0
    skipped  = 0
    errors   = []
    new_names = []  # for the summary message

    with SessionLocal() as db:
        for row_num, row in enumerate(values[1:], start=2):
            # Skip completely empty rows
            if not any(c.strip() for c in row if c):
                skipped += 1
                continue

            tally_id = cell(row, "tally_id")
            email    = cell(row, "email")
            name     = cell(row, "name")

            # Every tutor row must have at least a name and email
            if not name or not email:
                skipped += 1
                continue

            # ── Deduplication ────────────────────────────────────────────────
            # 1. Prefer tally_id match (most reliable)
            if tally_id:
                already = db.execute(
                    select(Tutor).where(Tutor.tally_id == tally_id)
                ).scalar()
                if already:
                    skipped += 1
                    continue

            # 2. Fall back to email match (catches manual entries and re-submissions
            #    from Tally forms that don't provide a Submission ID)
            already = db.execute(
                select(Tutor).where(Tutor.email == email)
            ).scalar()
            if already:
                skipped += 1
                continue

            # ── Parse rate ────────────────────────────────────────────────────
            rate_str = cell(row, "rate")
            rate = 0.0
            if rate_str:
                # Strip currency symbols and parse the first numeric token
                import re as _re
                m = _re.search(r"[\d]+(?:\.\d+)?", rate_str.replace(",", ""))
                if m:
                    try:
                        rate = float(m.group())
                    except ValueError:
                        pass

            subjects  = cell(row, "subjects")
            available = cell(row, "available")
            notes     = cell(row, "notes")
            phone     = cell(row, "phone")

            try:
                tutor = Tutor(
                    name               = name,
                    email              = email,
                    phone              = phone,
                    subjects           = subjects,
                    earliest_available = available,
                    rate               = rate,
                    notes              = notes,
                    tally_id           = tally_id or None,
                    active             = False,  # Requires admin activation before matching
                )
                db.add(tutor)
                db.commit()

                imported  += 1
                new_names.append(name)
                print(f"[SYNC] Imported tutor row {row_num}: {name} <{email}> (inactive, pending review)")

            except Exception as exc:
                errors.append(f"Row {row_num} ({email}): {exc}")
                db.rollback()
                print(f"[SYNC ERROR] Row {row_num}: {exc}")

    if imported > 0:
        names_str = ", ".join(new_names)
        summary = (
            f"Imported {imported} new tutor application(s): {names_str}. "
            f"They are INACTIVE – go to the Tutors table to review and activate them. "
            f"{skipped} row(s) skipped (already in DB or missing data)."
        )
    else:
        summary = f"No new tutor applications found. {skipped} row(s) skipped (already in DB or missing data)."

    print(f"[SYNC COMPLETE] {summary}")
    return jsonify({
        "imported": imported,
        "skipped":  skipped,
        "errors":   errors,
        "message":  summary,
    })


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
