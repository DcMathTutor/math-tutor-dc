Math Tutor DC
=============

A tutoring business hosted on GitHub Pages targeting $200k+ monthly revenue.
We source clients, match them with tutors, collect payments, handle scheduling,
and provide tutoring materials — keeping a margin on every session.

Live site:         https://dcmathtutor.github.io/math-tutor-dc/
Admin:             https://dcmathtutor.github.io/math-tutor-dc/admin.html
Tutor portal:      https://dcmathtutor.github.io/math-tutor-dc/tutors.html
Backend:           https://math-tutor-backend-y3uz.onrender.com
Tutor application: https://tally.so/r/LZdE4p  <- tutors fill this out (NOT clients)

All scheduling and payment collection is done manually (Zelle / Venmo / cash).


================================================================
BUSINESS PLAN
================================================================

POSITIONING
-----------
Math Tutor DC undercuts private tutoring agencies (typically $80-120/hr) while
paying tutors significantly more than they'd earn via platforms like Wyzant or
Tutor.com (which pay $15-25/hr).  Our pricing creates a durable competitive moat:

  Client rate:    $50/hr   (in-person or Zoom)
  Tutor rate:     $35/hr   (paid weekly via Zelle)
  Gross margin:   $15/hr   (30%)

  4-session bundle: $180 ($45/hr, save $20) -> encourages commitment, reduces churn
  Resume / PS review: $50 flat -> high-margin, fast, great for high school seniors


PAYMENT FLOW (anti-poaching sequence)
---------------------------------------
The order of operations matters. We never give the client the tutor's contact
information until payment is received, and we never give the tutor the client's
full contact information until the session is confirmed. This prevents tutors
from soliciting clients directly and clients from bypassing us.

  Step 1: Client submits contact form on the website.
  Step 2: Backend emails us with lead details + matched tutor + draft reply.
  Step 3: We send the draft email to the client (copy-paste from our inbox).
          Draft shows: matched tutor first name + subjects + rate -- but NOT
          the tutor's phone/email yet.
  Step 4: Client replies with preferred times.
  Step 5: We confirm the time slot and send Zelle payment instructions.
          Zelle: [our handle] -- use client's name as memo.
  Step 6: Client sends Zelle. We confirm receipt.
  Step 7: We intro the client to the tutor via email/text, including both
          parties' contact info. Session is now fully booked.
  Step 8: After session, we pay the tutor ($35/hr) in the weekly Zelle run.

Weekly tutor payment run: every Sunday, pay all tutors for sessions completed
that week.  Include Zelle memo: "MTD [TutorLastName] [dates]".

Log every payment (in and out) in the admin dashboard ($ Payment button) so
the P&L stays accurate.


ANTI-POACHING STRATEGY
-----------------------
1. Information sequencing (above): client gets tutor info only post-payment.
2. Non-solicitation reminder: in the welcome email to tutors, include one line:
   "By accepting sessions through Math Tutor DC you agree not to independently
   solicit or accept direct payment from clients we have introduced to you."
3. Rate incentive: we pay $35/hr -- competitive enough that tutors prefer staying
   in the network vs. taking a $50/hr client on the side and losing the flow.
4. Volume: once we have 20+ active clients, no single client relationship is
   worth a tutor burning the bridge.
5. Relationship ownership: all scheduling goes through us. Tutors never own the
   client relationship -- we do.


REVENUE ROADMAP TO $200k / MONTH
----------------------------------
At $50/hr and 30% margin the unit math is straightforward:

  To earn $X gross profit you need:   X / 15  hours/month delivered

Phase 1 -- Launch (months 0-3)
  Target: 20 sessions/month -> $1,000 revenue -> $300 gross profit
  Actions: Post flyers at GWU, Georgetown, American, Howard.
           Set up 3-5 active tutors.
           Run 2-3 QR-code flyer campaigns (track via admin Source Breakdown).

Phase 2 -- Traction (months 3-6)
  Target: 80 sessions/month -> $4,000 revenue -> $1,200 gross profit
  Actions: Referral program -- clients who refer get $25 credit.
           Instagram / Facebook ads ($200/mo budget, test creatives).
           Expand to STEM subjects beyond math (stats, physics, CS).

Phase 3 -- Growth (months 6-12)
  Target: 200 sessions/month -> $10,000 revenue -> $3,000 gross profit
  Actions: Hire part-time admin to handle scheduling + payment tracking.
           Build out Course Materials section in tutor portal (Google Drive links).
           Add group sessions (3 clients, 1 tutor, $35/hr each -> $105/hr rev).
           Partner with DC-area schools and college counselors for referrals.

Phase 4 -- Scale (months 12-18)
  Target: 600 sessions/month -> $30,000 revenue -> $9,000 gross profit
  Actions: Automate session booking (Calendly integration).
           Add Stripe payment option alongside Zelle.
           Dedicated tutor quality review (observe sessions, rating system).
           Expand geography: Arlington, Bethesda, NoVA, Northern MD.

Phase 5 -- $200k/month (months 18-24)
  Target: 4,000 sessions/month -> $200,000 revenue -> $60,000 gross profit
  Actions: Franchise / sub-market model (Baltimore, Philly, NYC).
           Enterprise contracts with school districts and tutoring centers.
           Content / curriculum products (study guides, practice sets).
           Requires 100+ active tutors and dedicated operations staff.

See finances.xlsx (3yr Base Case tab) for a month-by-month projection at 15%
MoM session growth starting from 20 sessions.


EMAIL TEMPLATES
----------------

-- New lead notification (sent to us by backend) --
Subject: [New Lead] {client_name} - {course}
Body: Auto-generated by backend. Includes lead details, matched tutor, and
draft reply. See backend/app.py -> CLIENT_EMAIL_DRAFT.

-- Draft reply to client (copy-paste, send from your inbox) --
Hi {client_name},

Great news -- we reviewed your request for {course} tutoring and we have a
match ready for you.

We'd like to pair you with {tutor_name}, who specializes in {tutor_subjects}.

Here's how it works:
  1. Reply with two or three times that work for you this week.
  2. We'll confirm the session and send Zelle payment instructions.
  3. Payment of $50/hr is due before the session ({mode}).
  4. Once payment is confirmed, we'll send your tutor's contact info
     so you can connect directly.

Looking forward to working with you,
Math Tutor DC

-- Zelle payment request (text or email) --
Hi {client_name}, confirming your {course} session with {tutor_first_name} on
{date} at {time} ({mode}).  Please Zelle ${amount} to [your Zelle handle] with
memo "MTD {client_last_name} {date}".  Session confirmed once payment received.

-- Post-session intro (send after payment clears) --
Hi {client_name}, your payment is confirmed -- thank you!
Here is your tutor's contact info:
  {tutor_name} - {tutor_email} - {tutor_phone}
Please reach out directly to coordinate the details.
We look forward to supporting your {course} journey!

-- Weekly tutor payment (text or Zelle memo) --
Hi {tutor_name}, your payment for sessions this week ({date_range}) is on the
way -- ${amount} via Zelle.  Memo: "MTD {tutor_last_name} {date_range}".
Thanks for the great work!

-- Referral incentive (when a converted client refers someone) --
Hi {client_name}, thank you for referring {referred_name}!
Once they complete their first session, you'll receive a $25 credit toward
your next session.  We really appreciate the word of mouth!


KEY METRICS TO TRACK WEEKLY
------------------------------
  Sessions delivered this week
  Revenue collected (Zelle ins)
  Tutor payments sent (Zelle outs)
  Gross profit (revenue minus tutor payments)
  New leads this week (from admin dashboard)
  Lead-to-client conversion rate
  Active tutors vs. active clients ratio (target: 1 tutor per 4-5 clients)

Update finances.xlsx -> Monthly P&L sheet and Dashboard KPIs monthly.


================================================================
PROJECT STRUCTURE
================================================================

    index.html          Public-facing website with contact form for prospective clients.
    admin.html          Secure admin dashboard (login required, JWT via backend)
    tutors.html         Tutor-only portal (login required, JWT via backend)
    finances.xlsx       10-sheet financial model and business projections
    generate_finances.py  Regenerate finances.xlsx with Python/openpyxl
    assets/             Images (logo, tutor photos, favicon)
    backend/
      app.py            Python/Flask API -- deployed to Render.com
      requirements.txt  Python dependencies
      .env.example      Environment variable template
      .env              NOT in git. Contains secrets.


================================================================
HOW THE TWO INTAKE FLOWS WORK
================================================================

There are two separate intake flows -- one for clients and one for tutors.

CLIENT INTAKE  (index.html -> /contact -> email notification)
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

TUTOR INTAKE  (Tally form -> Google Sheets -> Sync -> tutors table)
  1. A prospective tutor fills out the Tally application at https://tally.so/r/LZdE4p.
  2. Tally automatically appends each submission as a new row in Google Sheets
     (configured via Tally's Integrations tab -> Google Sheets).
  3. When you click "Sync Tally" in the admin dashboard the backend reads
     the sheet, imports any new rows as INACTIVE tutors, and shows a summary.
  4. You review new tutors in the admin Tutors table and click Activate on the
     ones you want to enable.  Only active tutors are considered for client matching.


================================================================
GOOGLE SHEETS INTEGRATION SETUP  (tutor onboarding)
================================================================

1. Create a Google Cloud project (or reuse an existing one):
     https://console.cloud.google.com/

2. Enable the Google Sheets API:
     APIs & Services -> Library -> search "Google Sheets API" -> Enable

3. Create a Service Account:
     IAM & Admin -> Service Accounts -> + Create Service Account
     Name it anything (e.g. "math-tutor-sheets-reader").
     Skip optional steps -> Done.

4. Generate a key:
     Click the service account -> Keys tab -> Add Key -> Create new key -> JSON
     Save the downloaded .json file (keep it secret -- never commit it).

5. Share your Google Sheet with the service account email:
     Open the sheet -> Share -> paste the service account email (looks like
     name@project-id.iam.gserviceaccount.com) -> Viewer access is enough.

6. Add these env vars in Render's Environment dashboard:

     GOOGLE_CREDS_JSON     Paste the entire contents of the .json key file.
     GOOGLE_SHEET_ID       The spreadsheet ID from its URL:
                           docs.google.com/spreadsheets/d/<ID>/edit


================================================================
GOOGLE SHEETS COLUMN MAPPING  (tutor application form)
================================================================

The sync endpoint maps Google Sheet column headers to tutor fields. The defaults
match typical Tally column names. If your Tally form uses different question
labels, override any of these in Render's Environment dashboard:

  COL_TALLY_ID   = "Submission ID"      (Tally auto-adds this column)
  COL_NAME       = "Name"
  COL_EMAIL      = "Email"
  COL_PHONE      = "Phone"
  COL_SUBJECTS   = "Subjects"           (courses the tutor can teach)
  COL_AVAILABLE  = "Earliest Available" (earliest start time, e.g. "3:00 PM")
  COL_RATE       = "Rate"               (desired $/hr -- numbers parsed automatically)
  COL_NOTES      = "Notes"              (bio, availability notes, etc.)

GOOGLE_SHEET_NAME defaults to "Sheet1". Set it if your tab has a different name.


================================================================
BACKEND SETUP (Render.com)
================================================================

Build command:  pip install -r requirements.txt
Start command:  gunicorn app:app
Root directory: backend

Environment variables (set in Render's dashboard, never in a local file):

  RESEND_API_KEY        Already set -- no change
  EMAIL_TO              Already set -- no change
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


================================================================
DATABASE (SQLAlchemy + SQLite)
================================================================

The backend uses SQLAlchemy with SQLite. Created automatically on first run.
New columns are added via run_migrations() on every startup (safe to redeploy).

Tables:

  leads              -- every client contact form submission (top of the sales funnel)
                        columns: name, email, phone, course, mode, time_pref,
                                 message, src, referred_by, tally_id, status, client_id
  clients            -- leads that have been converted to paying clients
                        columns: name, email, phone, notes
  tutors             -- tutors employed by the business
                        columns: name, email, phone, rate ($/hr), notes, active,
                                 subjects, earliest_available, tally_id
  tutoring_sessions  -- individual sessions linking a client and a tutor
                        columns: client_id, tutor_id, course, date, duration_hrs,
                                 client_rate, tutor_rate
  payments           -- cash movements: in (from clients) or out (to tutors)
                        columns: session_id, amount, direction (in|out), method, date
  expenses           -- operating costs not tied to a session
                        columns: category, description, amount, date


================================================================
HOW TO ENTER DATA (manual workflow)
================================================================

Client leads come in automatically via the contact form on index.html.
Tutor applications come in via Tally -> Google Sheets -> Sync button.

PREFERRED: Use the admin dashboard directly for sessions and payments.
  - Click "+ Session" in the header to log a completed tutoring session.
    Default rates are pre-filled ($50 client / $35 tutor).  Margin preview
    updates live as you type.
  - Click "$ Payment" to log a Zelle payment in or out.
  - Click the status dropdown next to any lead to move it through the funnel.
  - Click Activate / Deactivate on any tutor row to toggle matching eligibility.

DB BROWSER fallback (for clients table and anything not yet in the UI):
  1. Log in at admin.html and click "Export DB" (top-right header).
     This downloads math_tutor.db to your computer.
  2. Open math_tutor.db in DB Browser for SQLite (free):
       https://sqlitebrowser.org/
  3. Click "Browse Data" and pick the table to edit.

     clients
       Add when a lead converts to a paying client.
       Required:  name, email
       Optional:  phone, notes

     tutoring_sessions (use admin UI instead when possible)
       One row per session delivered. Links a client and a tutor.
       Required:  client_id (from clients table), tutor_id (from tutors table),
                  date (YYYY-MM-DD)
       Optional:  course, duration_hrs (default 1.0), client_rate ($/hr charged),
                  tutor_rate ($/hr paid), notes

     payments (use admin UI instead when possible)
       Record cash movements to drive the Financial Overview.
         direction='in'  -> money received FROM a client  (counts as Revenue)
         direction='out' -> money paid TO a tutor          (counts as COGS)
       Required:  amount, direction ('in' or 'out'), date (YYYY-MM-DD)
       Optional:  session_id (links to a session), method (zelle/cash/venmo), notes

     expenses
       Operating costs not tied to a session (marketing, tools, etc.).
       Required:  amount, date (YYYY-MM-DD)
       Optional:  category (marketing|tools|travel|misc), description, notes

  4. After editing, click File -> Write Changes in DB Browser.
  5. Re-upload to Render via the Shell tab:
       a. Go to Render service -> Shell tab.
       b. Run:  cat > math_tutor.db
       c. In a local terminal: base64 math_tutor.db | pbcopy  (Mac)
                           or: base64 math_tutor.db  (copy output manually)
       d. Paste into the Render shell, press Ctrl+D.

IMPORTANT -- Render free tier:
  The SQLite file resets to empty on every redeploy unless you use Persistent
  Disk.  Always export a copy before deploying new backend code.

DB file is gitignored (*.db) -- never committed.


================================================================
TUTOR MATCHING ALGORITHM
================================================================

When a client submits the contact form (POST /contact), the backend automatically
picks the best active tutor and includes them in the notification email.

Matching algorithm (backend/app.py -> match_tutor() function):

  Score +10  if tutor.subjects contains the requested course (case-insensitive
             substring match in either direction).
  Score +5   if tutor.earliest_available <= lead's preferred time
             (tutor can start when the client is available).
  Ties broken by rate ascending (cheapest tutor first).
  Fallback: if no tutor scores > 0, the first active tutor alphabetically is
            suggested (so you always get a recommendation even with sparse data).

To make matching work: make sure each tutor has subjects and earliest_available
filled in (either via the Tally sync or manually), and that active=1.


================================================================
CLIENT EMAIL DRAFT TEMPLATE
================================================================

*** EDIT THIS TO CHANGE THE EMAIL FORMAT ***

Location: backend/app.py -> search for CLIENT_EMAIL_DRAFT

The constant is defined near the top of the "RESEND EMAIL" section, clearly
marked with a comment block.  It is a plain Python string with {placeholders}.
Edit the body text, keep the {placeholders} you want, and remove the ones you
don't need.

Available placeholders:
  {client_name}     Lead's full name
  {course}          Subject they need help with
  {mode}            "In-person (DC area)" or "Online (Zoom)"
  {time_pref}       Their preferred start time
  {tutor_name}      Matched tutor's name
  {tutor_subjects}  Tutor's listed subjects
  {client_rate}     Our hourly rate charged to the client (from CLIENT_HOURLY_RATE constant)

NOTE: {client_rate} pulls from CLIENT_HOURLY_RATE = 50 in app.py.
The tutor's actual pay rate ($35) is intentionally NOT exposed in the draft.

The draft appears at the bottom of every new-lead notification email under
"DRAFT EMAIL TO CLIENT -- copy/paste -> send from your inbox".


================================================================
ADMIN PAGE
================================================================

URL: https://dcmathtutor.github.io/math-tutor-dc/admin.html
Auth: password -> backend validates -> JWT stored in sessionStorage (8hr expiry)

Features:
  + Session button (header): log a completed tutoring session (client ID, tutor ID,
    date, course, duration, rates). Margin preview updates live as you type.
  $ Payment button (header): log a Zelle payment in or out with method + session link.
  Sync Tally button: pulls new tutor applications from Google Sheets, imports
    them as inactive tutors for your review.
  Export DB button: downloads the raw SQLite file.
  Overview stats: total leads, last 7 days, sources tracked, revenue, net income.
  Financial Overview: income statement (revenue / COGS / gross profit / opex / net).
  Lead Funnel: count of leads by status (new -> contacted -> converted -> lost).
  All Leads: searchable/filterable table with inline status dropdown (updates DB live).
             Referral source shown beneath lead name if provided.
  Clients: table of all clients with session counts.
  Tutors: table of all tutors with subjects, rates, session counts, and
          Activate / Deactivate toggle button (updates DB live).
  QR Code Generator: codes for Flyer A/B, Instagram, Facebook, Google, Referral.
    Right-click a QR code to save it as an image.
  Source Breakdown: lead counts per campaign.


================================================================
TUTOR PORTAL
================================================================

URL: https://dcmathtutor.github.io/math-tutor-dc/tutors.html
Auth: password -> backend validates (TUTOR_PASSWORD_HASH) -> JWT stored in sessionStorage (12hr)

To set the tutor password:
  1. Generate hash: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
  2. Set TUTOR_PASSWORD_HASH in Render's environment dashboard

Features:
  - Meeting Spots: list of good locations to meet students (edit directly in HTML)
  - Course Materials (In Development): one card per course with a Google Drive link
    To add a link, find the course in COURSE_MATERIALS in tutors.html and fill in the url field


================================================================
QR CODE / CAMPAIGN TRACKING
================================================================

Each QR code points to:
  https://dcmathtutor.github.io/math-tutor-dc/?src=flyer_a

The landing page (index.html) reads ?src= and stores it in the contact form's
hidden "src" field. When the client submits the form the src value is sent to
the backend and saved on the lead record, then shown in the Source Breakdown
section of the admin dashboard.

All QR codes are managed from the admin page. New sources can be added with a
descriptive name and short key.


================================================================
FINANCES SPREADSHEET  (finances.xlsx)
================================================================

Regenerate:  python generate_finances.py

12 sheets:

  Dashboard         KPI boxes (update monthly), revenue roadmap phases 1-5
  Monthly P&L       12-column income statement; enter actuals each month
  3yr Conservative  Month-by-month projection at 8% MoM session growth
  3yr Base Case     Month-by-month projection at 15% MoM session growth
  3yr Aggressive    Month-by-month projection at 25% MoM session growth
  Lead Funnel       Monthly new / contacted / converted / lost counts
  Tutor Roster      Planning reference (live data is in backend DB)
  Client Roster     Planning reference (live data is in backend DB)
  Session Log       Log every session here AND in admin dashboard
  Payment Log       Log every Zelle transfer here AND in admin dashboard
  Expense Log       Track operating costs by category
  Pricing Calculator  Yellow input cells -- model different rate scenarios


================================================================
TODO
================================================================

- Add real meeting spots to tutors.html
- Add Google Drive links to course materials in tutors.html
- Admin UI form to add clients manually (currently via DB export + re-upload)
- Stripe payment integration (in addition to Zelle)
- Calendly / scheduling automation
- Tutor quality scoring + rating system
- Group session pricing and booking flow
- Referral credit tracking in admin dashboard
- Automated weekly tutor payment reminders
- Expand geography (Arlington, Bethesda, NoVA, Northern MD)
