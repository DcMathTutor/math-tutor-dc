import os
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# -----------------------------
# APP + CORS
# -----------------------------
app = Flask(__name__)
CORS(app)  # Allow all origins for now

# -----------------------------
# ENV VARS
# -----------------------------
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_TO = os.environ.get("EMAIL_TO")  # e.g. "you@gmail.com,partner@gmail.com"

if not RESEND_API_KEY:
    raise Exception("Missing RESEND_API_KEY env var in Render!")

if not EMAIL_TO:
    raise Exception("Missing EMAIL_TO env var in Render!")


# -----------------------------
# SIMPLE RATE LIMITING
# -----------------------------
RATE_LIMIT_MAX = 2            # max submissions
RATE_LIMIT_WINDOW = 3600      # seconds (1 hour)
rate_limit_store = {}         # ip → [timestamps]


def get_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def check_rate_limit(ip):
    now = time.time()
    timestamps = rate_limit_store.get(ip, [])

    # keep only events in last hour
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

    if len(timestamps) >= RATE_LIMIT_MAX:
        return False  # rate limited

    timestamps.append(now)
    rate_limit_store[ip] = timestamps
    return True


# -----------------------------
# RESEND EMAIL SENDER
# -----------------------------
def send_email_via_resend(name, email, phone, course, mode, time_pref, message):
    """Send email using Resend API."""
    payload = {
        "from": "Math Tutor DC <onboarding@resend.dev>",  # works without domain setup
        "to": EMAIL_TO.split(","),  # convert string to list
        "subject": "New Math Tutoring Request",
        "text": f"""
New tutoring request:

Name: {name}
Email: {email}
Phone: {phone}
Class: {course}
Mode: {mode}
Preferred time: {time_pref}

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


# -----------------------------
# MAIN CONTACT ROUTE
# -----------------------------
@app.post("/contact")
def contact():
    data = request.get_json() or {}
    ip = get_client_ip()

    # Rate limit check
    if not check_rate_limit(ip):
        print(f"[RATE LIMIT] Blocked IP: {ip}")
        return jsonify({"error": "Too many submissions. Please try again in 1 hour."}), 429

    required = ["name", "email", "phone", "class", "mode", "time", "message"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        print("[VALIDATION ERROR]", missing)
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    name = data["name"]
    email = data["email"]
    phone = data["phone"]
    course = data["class"]
    mode = data["mode"]
    time_pref = data["time"]
    message = data["message"]

    print(f"[CONTACT] {name} <{email}> | Course={course} | IP={ip}")

    # Send email
    ok = send_email_via_resend(name, email, phone, course, mode, time_pref, message)
    if not ok:
        return jsonify({"error": "Email send failed."}), 500

    return jsonify({"ok": True})
