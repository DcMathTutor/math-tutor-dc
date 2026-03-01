Math Tutor DC
=============

A tutoring business website hosted on GitHub Pages. The goal is to expand to $200k+ monthly revenue by matching recently graduated college professionals with high school and early college students needing math and statistics tutoring.

Business model: we source clients, match them with tutors, collect payments, handle scheduling, and provide tutoring materials—taking a small margin.

Live site:    https://dcmathtutor.github.io/math-tutor-dc/
Admin:        https://dcmathtutor.github.io/math-tutor-dc/admin.html
Tutor portal: https://dcmathtutor.github.io/math-tutor-dc/tutors.html
Backend:      https://math-tutor-backend-y3uz.onrender.com

All scheduling and payment collection is done manually for now.


Project structure
-----------------

    index.html          Public-facing website + contact form
    admin.html          Secure admin dashboard (login required, JWT via backend)
    tutors.html         Tutor-only portal (login required, JWT via backend)
    assets/             Images (logo, tutor photos, favicon)
    backend/
      app.py            Python/Flask API – deployed to Render.com
      requirements.txt  Python dependencies (flask, sqlalchemy, bcrypt, PyJWT…)
      .env.example      Environment variable template – set real values in Render's dashboard
      .env              NOT in git. Contains secrets. See setup below.
    old_backend.py      Original backend – kept for reference


Backend setup (Render.com)
--------------------------

The backend is Python/Flask. Deployed from this repository.

Build command:  pip install -r requirements.txt
Start command:  gunicorn app:app
Root directory: backend

Environment variables (set in Render's dashboard, never in a local file):

  RESEND_API_KEY        Already set – no change
  EMAIL_TO              Already set – no change
  ADMIN_PASSWORD_HASH   bcrypt hash of admin password
                        Generate: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
  TUTOR_PASSWORD_HASH   bcrypt hash of tutor portal password (separate from admin)
                        Generate same way as above
  JWT_SECRET            Long random string for signing session tokens
                        Generate: python -c "import secrets; print(secrets.token_hex(48))"
  DB_PATH               (optional) Path to SQLite file. Default: math_tutor.db
                        For persistent storage set to /data/math_tutor.db and enable Render Persistent Disk


Database (SQLAlchemy + SQLite)
------------------------------

The backend uses SQLAlchemy with SQLite. The file is created automatically on first run.

Tables:

  leads              – every contact form submission (top of the sales funnel)
                       columns: name, email, phone, course, mode, time_pref, message,
                                src, status (new|contacted|converted|lost), client_id
  clients            – leads that have been converted to paying clients
                       columns: name, email, phone, notes
  tutors             – tutors employed by the business
                       columns: name, email, phone, rate ($/hr), notes, active
  tutoring_sessions  – individual sessions linking a client and a tutor
                       columns: client_id, tutor_id, course, date, duration_hrs,
                                client_rate, tutor_rate
  payments           – cash movements: in (from clients) or out (to tutors)
                       columns: session_id, amount, direction (in|out), method, date
  expenses           – operating costs not tied to a session
                       columns: category, description, amount, date

How to enter data (manual workflow for now):

  Leads come in automatically via the contact form and appear instantly in the
  Admin dashboard. Everything else (clients, tutors, sessions, payments,
  expenses) is entered manually by editing the SQLite database file.

  Step-by-step:

  1. Log in at admin.html and click "⬇ Export DB" (top-right header).
     This downloads math_tutor.db to your computer.

     NOTE: If "Export DB" returns an error, the backend may not yet have the
     export route deployed. Trigger a manual redeploy on Render (Dashboard →
     your service → Manual Deploy → Deploy latest commit), wait for it to
     finish, then try again.

  2. Open math_tutor.db in DB Browser for SQLite (free):
       https://sqlitebrowser.org/

  3. Click the "Browse Data" tab and pick the table you want to edit:

     clients
       Add a row here when a lead converts to a paying client.
       Required: name, email
       Optional: phone, notes

     tutors
       One row per tutor. Set active=1 (active) or active=0 (inactive).
       Required: name, email
       Optional: phone, rate ($/hr default), notes

     tutoring_sessions
       One row per session delivered. Links a client and a tutor.
       Required: client_id (from clients table), tutor_id (from tutors table),
                 date (YYYY-MM-DD)
       Optional: course, duration_hrs (default 1.0), client_rate ($/hr charged),
                 tutor_rate ($/hr paid), notes

     payments
       Record cash movements here to drive the Financial Overview.
         direction='in'  → money received FROM a client  (counts as Revenue)
         direction='out' → money paid TO a tutor          (counts as COGS)
       Required: amount, direction ('in' or 'out'), date (YYYY-MM-DD)
       Optional: session_id (links payment to a session), method (zelle/cash/venmo), notes

     expenses
       Operating costs not tied to a specific session (marketing, tools, etc.).
       Required: amount, date (YYYY-MM-DD)
       Optional: category (marketing|tools|travel|misc), description, notes

  4. After making edits, click File → Write Changes in DB Browser.

  5. Re-upload the file to Render via the Shell tab:
       a. Go to your Render service → Shell tab (top nav).
       b. Run:  cat > math_tutor.db
       c. Open a second terminal, run:  base64 math_tutor.db | pbcopy  (Mac)
                                    or: base64 math_tutor.db  (copy the output)
       d. Paste into the Render shell and press Ctrl+D.

     Easier alternative (Render Persistent Disk):
       Enable a Persistent Disk in your Render service settings.
       Set DB_PATH=/data/math_tutor.db in Environment variables.
       The DB then survives redeploys and can be edited via the Shell directly.

IMPORTANT – Render free tier:
  The SQLite file resets to empty on every redeploy unless you use Persistent
  Disk. Always export a copy before deploying new backend code.

DB file is gitignored (*.db) – it is never committed to git.


Admin page
----------

URL: https://dcmathtutor.github.io/math-tutor-dc/admin.html
Auth: password → backend validates → JWT stored in sessionStorage (8hr expiry)

Features:
  - Overview stats: total leads, last 7 days, sources tracked, revenue, net income
  - Financial Overview: income statement (revenue / COGS / gross profit / opex / net income)
  - Lead Funnel: count of leads by status (new → contacted → converted → lost)
  - All Leads: searchable/filterable table with status column and email links
  - Clients: table of all clients with session counts
  - Tutors: table of all tutors with rates and session counts
  - QR Code Generator: pre-built codes for Flyer A/B, Instagram, Facebook, Google, Referral
    Two-field form (descriptive name + short key); right-click a QR code to save as image
  - Source breakdown table with lead counts per campaign
  - Export DB button (top right): downloads the SQLite file from the server


Tutor portal
------------

URL: https://dcmathtutor.github.io/math-tutor-dc/tutors.html
Auth: password → backend validates (TUTOR_PASSWORD_HASH) → JWT stored in sessionStorage (12hr)

To set the tutor password:
  1. Generate hash: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
  2. Set TUTOR_PASSWORD_HASH in Render's environment dashboard

Features:
  - Meeting Spots: list of good locations to meet students (edit directly in HTML)
  - Course Materials (In Development): one card per course with a Google Drive link
    To add a link, find the course in COURSE_MATERIALS in tutors.html and fill in the url field


QR Code / Campaign tracking
----------------------------

Each QR code points to:
  https://dcmathtutor.github.io/math-tutor-dc/?src=flyer_a

The ?src= value is silently captured in a hidden form field. On submission it is
logged to the leads table and appended to the email subject:
  "New Math Tutoring Request [flyer_a]"

All QR codes are visible and downloadable from the admin page.
New sources can be added from the admin page with a descriptive name and short key.


TODO
----

- Add real meeting spots to tutors.html
- Add Google Drive links to course materials in tutors.html
- Admin UI forms to add clients, tutors, sessions, payments (currently done via DB export + re-upload)
- Tutor schedules / availability
- Graphic design Claude skill
