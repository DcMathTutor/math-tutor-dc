Math Tutor DC
=============

A tutoring business website hosted on GitHub Pages. The goal is to expand to
$200k+ monthly revenue by matching recently graduated college professionals with
high school and early college students needing math and statistics tutoring.

Business model: we source clients, match them with tutors, collect payments,
handle scheduling, and provide tutoring materials — taking a margin.

Live site:         https://dcmathtutor.github.io/math-tutor-dc/
Admin:             https://dcmathtutor.github.io/math-tutor-dc/admin.html
Tutor portal:      https://dcmathtutor.github.io/math-tutor-dc/tutors.html
Backend:           https://math-tutor-backend-y3uz.onrender.com
Tutor application: https://tally.so/r/LZdE4p  ← tutors fill this out (NOT clients)

All scheduling and payment collection is done manually for now.


Project structure
-----------------

    index.html          Public-facing website with contact form for prospective clients.
    admin.html          Secure admin dashboard (login required, JWT via backend)
    tutors.html         Tutor-only portal (login required, JWT via backend)
    assets/             Images (logo, tutor photos, favicon)
    backend/
      app.py            Python/Flask API – deployed to Render.com
      requirements.txt  Python dependencies (flask, sqlalchemy, bcrypt, PyJWT,
                        google-auth, google-api-python-client…)
      .env.example      Environment variable template – set real values in Render
      .env              NOT in git. Contains secrets. See setup below.


How the two intake flows work
------------------------------

There are two separate intake flows — one for clients and one for tutors.

CLIENT INTAKE  (index.html → /contact → email notification)
  1. A prospective client visits the site, fills out the contact form, and submits.
  2. The browser POSTs the data to POST /contact on the backend.
  3. The backend logs the submission as a new "lead" in the database.
  4. The backend runs tutor matching and sends you a Resend notification email
     containing the lead details, the best-matched tutor, and a draft client reply.
  5. You copy/paste the draft, send it from your inbox, and follow up manually.

  QR code attribution: QR codes link to index.html?src=flyer_a etc.  The page
  reads the ?src= parameter and stores it in the contact form's hidden field.
  When the form is submitted the src value is saved on the lead record and shown
  in the admin dashboard's Source Breakdown section.

TUTOR INTAKE  (Tally form → Google Sheets → Sync → tutors table)
  1. A prospective tutor fills out the Tally application at https://tally.so/r/LZdE4p.
  2. Tally automatically appends each submission as a new row in Google Sheets
     (configured via Tally's Integrations tab → Google Sheets).
  3. When you click "⟳ Sync Tally" in the admin dashboard the backend reads
     the sheet, imports any new rows as INACTIVE tutors, and shows a summary.
  4. You review new tutors in the admin Tutors table and set active=1 on the ones
     you want to enable. Only active tutors are considered for client matching.


Google Sheets integration setup  (tutor onboarding)
----------------------------------------------------

1. Create a Google Cloud project (or reuse an existing one):
     https://console.cloud.google.com/

2. Enable the Google Sheets API:
     APIs & Services → Library → search "Google Sheets API" → Enable

3. Create a Service Account:
     IAM & Admin → Service Accounts → + Create Service Account
     Name it anything (e.g. "math-tutor-sheets-reader").
     Skip optional steps → Done.

4. Generate a key:
     Click the service account → Keys tab → Add Key → Create new key → JSON
     Save the downloaded .json file (keep it secret – never commit it).

5. Share your Google Sheet with the service account email:
     Open the sheet → Share → paste the service account email (looks like
     name@project-id.iam.gserviceaccount.com) → Viewer access is enough.

6. Add these env vars in Render's Environment dashboard:

     GOOGLE_CREDS_JSON     Paste the entire contents of the .json key file.
                           Render supports multi-line env vars – just paste it.
     GOOGLE_SHEET_ID       The spreadsheet ID from its URL:
                           docs.google.com/spreadsheets/d/<ID>/edit


Google Sheets column mapping  (tutor application form)
-------------------------------------------------------

The sync endpoint maps Google Sheet column headers to tutor fields. The defaults
match typical Tally column names. If your Tally form uses different question
labels, override any of these in Render's Environment dashboard:

  COL_TALLY_ID   = "Submission ID"      (Tally auto-adds this column)
  COL_NAME       = "Name"
  COL_EMAIL      = "Email"
  COL_PHONE      = "Phone"
  COL_SUBJECTS   = "Subjects"           (courses the tutor can teach)
  COL_AVAILABLE  = "Earliest Available" (earliest start time, e.g. "3:00 PM")
  COL_RATE       = "Rate"               (desired $/hr – numbers parsed automatically)
  COL_NOTES      = "Notes"              (bio, availability notes, etc.)

GOOGLE_SHEET_NAME defaults to "Sheet1". Set it if your tab has a different name.


Backend setup (Render.com)
--------------------------

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
                        For persistent storage set to /data/math_tutor.db and
                        enable Render Persistent Disk
  GOOGLE_CREDS_JSON     Service account JSON for Google Sheets API (see above)
  GOOGLE_SHEET_ID       Google Sheets spreadsheet ID (see above)
  GOOGLE_SHEET_NAME     (optional) Sheet tab name. Default: Sheet1
  COL_*                 (optional) Column name overrides (see above)


Database (SQLAlchemy + SQLite)
------------------------------

The backend uses SQLAlchemy with SQLite. Created automatically on first run.
New columns are added via run_migrations() on every startup (safe to redeploy).

Tables:

  leads              – every client contact form submission (top of the sales funnel)
                       columns: name, email, phone, course, mode, time_pref,
                                message, src, tally_id, status, client_id
  clients            – leads that have been converted to paying clients
                       columns: name, email, phone, notes
  tutors             – tutors employed by the business
                       columns: name, email, phone, rate ($/hr), notes, active,
                                subjects, earliest_available, tally_id
  tutoring_sessions  – individual sessions linking a client and a tutor
                       columns: client_id, tutor_id, course, date, duration_hrs,
                                client_rate, tutor_rate
  payments           – cash movements: in (from clients) or out (to tutors)
                       columns: session_id, amount, direction (in|out), method, date
  expenses           – operating costs not tied to a session
                       columns: category, description, amount, date


How to enter data (manual workflow for now)
-------------------------------------------

Client leads come in automatically via the contact form on index.html.
Tutor applications come in via Tally → Google Sheets → Sync button.
Everything else is entered manually by editing the SQLite database file.

Step-by-step:

  1. Log in at admin.html and click "⬇ Export DB" (top-right header).
     This downloads math_tutor.db to your computer.

  2. Open math_tutor.db in DB Browser for SQLite (free):
       https://sqlitebrowser.org/

  3. Click "Browse Data" and pick the table to edit:

     tutors
       Tutors are added automatically via the Tally sync (see above), but you
       can also add them manually here. After a sync, newly imported tutors
       have active=0 — set it to 1 to enable them for client matching.
       Required:  name, email
       Optional:  phone, rate ($/hr), notes, active (default 0 on sync, 1 if manual)
       Matching fields:
         subjects           Comma-separated list of courses this tutor can teach.
                            Must match (or closely overlap) the course names used
                            in the client contact form.
                            Example: "Calculus I–III, Linear Algebra, Probability & Statistics"
         earliest_available Earliest time the tutor can start a session, in
                            12-hour (e.g. "3:00 PM") or 24-hour (e.g. "15:00") format.
                            A tutor matches when their earliest <= lead's earliest.
                            Example: "15:00"

     clients
       Add when a lead converts to a paying client.
       Required:  name, email
       Optional:  phone, notes

     tutoring_sessions
       One row per session delivered. Links a client and a tutor.
       Required:  client_id (from clients table), tutor_id (from tutors table),
                  date (YYYY-MM-DD)
       Optional:  course, duration_hrs (default 1.0), client_rate ($/hr charged),
                  tutor_rate ($/hr paid), notes

     payments
       Record cash movements to drive the Financial Overview.
         direction='in'  → money received FROM a client  (counts as Revenue)
         direction='out' → money paid TO a tutor          (counts as COGS)
       Required:  amount, direction ('in' or 'out'), date (YYYY-MM-DD)
       Optional:  session_id (links to a session), method (zelle/cash/venmo), notes

     expenses
       Operating costs not tied to a session (marketing, tools, etc.).
       Required:  amount, date (YYYY-MM-DD)
       Optional:  category (marketing|tools|travel|misc), description, notes

  4. After editing, click File → Write Changes in DB Browser.

  5. Re-upload to Render via the Shell tab:
       a. Go to Render service → Shell tab.
       b. Run:  cat > math_tutor.db
       c. In a local terminal: base64 math_tutor.db | pbcopy  (Mac)
                           or: base64 math_tutor.db  (copy output manually)
       d. Paste into the Render shell, press Ctrl+D.

     Easier (Render Persistent Disk):
       Enable a Persistent Disk in service settings.
       Set DB_PATH=/data/math_tutor.db in Environment variables.
       DB then survives redeploys; edit via Shell directly.

IMPORTANT – Render free tier:
  The SQLite file resets to empty on every redeploy unless you use Persistent
  Disk. Always export a copy before deploying new backend code.

DB file is gitignored (*.db) – never committed.


Tutor matching
--------------

When a client submits the contact form (POST /contact), the backend automatically
picks the best active tutor and includes them in the notification email.

Matching algorithm (backend/app.py → match_tutor() function):

  Score +10  if tutor.subjects contains the requested course (case-insensitive
             substring match in either direction).
  Score +5   if tutor.earliest_available <= lead's preferred time
             (tutor can start when the client is available).
  Ties broken by rate ascending (cheapest tutor first).
  Fallback: if no tutor scores > 0, the first active tutor alphabetically is
            suggested (so you always get a recommendation even with sparse data).

To make matching work: make sure each tutor has subjects and earliest_available
filled in (either via the Tally sync or manually in DB Browser), and that
active=1.


Client email draft template
----------------------------

*** EDIT THIS TO CHANGE THE EMAIL FORMAT ***

Location: backend/app.py → search for CLIENT_EMAIL_DRAFT

The constant is defined near the top of the "RESEND EMAIL" section, clearly
marked with a comment block. It is a plain Python string with {placeholders}.
Edit the body text, keep the {placeholders} you want, and remove the ones you
don't need.

Available placeholders:
  {client_name}     Lead's full name
  {course}          Subject they need help with
  {mode}            "In-person (DC area)" or "Online (Zoom)"
  {time_pref}       Their preferred start time
  {tutor_name}      Matched tutor's name
  {tutor_subjects}  Tutor's listed subjects
  {tutor_rate}      Tutor's hourly rate (number)

The draft appears at the bottom of every new-lead notification email under
"DRAFT EMAIL TO CLIENT – copy/paste → send from your inbox".


Admin page
----------

URL: https://dcmathtutor.github.io/math-tutor-dc/admin.html
Auth: password → backend validates → JWT stored in sessionStorage (8hr expiry)

Features:
  - ⟳ Sync Tally button (top-right): pulls new tutor applications from Google
    Sheets, imports them as inactive tutors for your review
  - ⬇ Export DB button (top-right): downloads the raw SQLite file
  - Overview stats: total leads, last 7 days, sources tracked, revenue, net income
  - Financial Overview: income statement (revenue / COGS / gross profit / opex / net)
  - Lead Funnel: count of leads by status (new → contacted → converted → lost)
  - All Leads: searchable/filterable table with status and email links
  - Clients: table of all clients with session counts
  - Tutors: table of all tutors with rates, subjects, and session counts
    (set active=1 here after reviewing a synced tutor application)
  - QR Code Generator: codes for Flyer A/B, Instagram, Facebook, Google, Referral
    Right-click a QR code to save it as an image
  - Source Breakdown: lead counts per campaign


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

The landing page (index.html) reads ?src= and stores it in the contact form's
hidden "src" field. When the client submits the form the src value is sent to
the backend and saved on the lead record, then shown in the Source Breakdown
section of the admin dashboard.

All QR codes are managed from the admin page. New sources can be added with a
descriptive name and short key.


TODO
----

- Add real meeting spots to tutors.html
- Add Google Drive links to course materials in tutors.html
- Admin UI forms to add clients, tutors, sessions, payments (currently via DB export + re-upload)
- Admin UI: one-click activate/deactivate for tutors synced from Tally
- Tutor schedules / availability calendar
- Graphic design Claude skill
