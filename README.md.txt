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
    tutors.html         Tutor-only portal (login required, client-side SHA-256 hash)
    assets/             Images (logo, tutor photos, favicon)
    backend/
      app.py            Python/Flask API – deployed to Render.com
      requirements.txt  Python dependencies
      .env.example      Environment variable template – set real values in Render's dashboard
      .env              NOT in git. Contains secrets. See setup below.
    old_backend.py      Original backend – kept for reference


Backend setup (Render.com)
--------------------------

The backend is Python/Flask. Currently deployed from this repository.

Build command:  pip install -r requirements.txt
Start command:  gunicorn app:app
Root directory: backend

Environment variables (set in Render's dashboard, never in a local file):

  RESEND_API_KEY        Already set – no change
  EMAIL_TO              Already set – no change
  ADMIN_PASSWORD_HASH   bcrypt hash of admin password
                        Generate: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
  JWT_SECRET            Long random string for signing session tokens
                        Generate: python -c "import secrets; print(secrets.token_hex(48))"


Admin page
----------

URL: https://dcmathtutor.github.io/math-tutor-dc/admin.html
Auth: password → backend validates → JWT stored in sessionStorage (8hr expiry)

Features:
  - Overview stats: total leads, last 7 days, sources tracked
  - QR Code Generator: pre-built codes for Flyer A/B, Instagram, Facebook, Google, Referral
    Two-field form (descriptive name + short key); codes downloadable as high-res PNG
  - Source breakdown table with lead counts per campaign
  - All Leads: searchable/filterable table with email links


Tutor portal
------------

URL: https://dcmathtutor.github.io/math-tutor-dc/tutors.html
Auth: client-side SHA-256 hash stored in tutors.html (separate password from admin)

To set the tutor password:
  1. Run: node -e "const c=require('crypto'); console.log(c.createHash('sha256').update('yourpassword').digest('hex'))"
  2. Paste the output into the PASSWORD_HASH constant in tutors.html

Features:
  - Meeting Spots: list of good locations to meet students (edit directly in HTML)
  - Course Materials (In Development): one card per course with a Google Drive link
    To add a link, find the course in COURSE_MATERIALS in tutors.html and fill in the url field


QR Code / Campaign tracking
----------------------------

Each QR code points to:
  https://dcmathtutor.github.io/math-tutor-dc/?src=flyer_a

The ?src= value is silently captured in a hidden form field. On submission it is
logged to the database and appended to the email subject:
  "New Math Tutoring Request [flyer_a]"

All QR codes are visible and downloadable from the admin page.
New sources can be added from the admin page with a descriptive name and short key.


TODO
----

- Add real meeting spots to tutors.html
- Add Google Drive links to course materials in tutors.html
- Portal to add/edit tutors
- Log payments in SQL backend
- Tutor schedules / availability
- Graphic design Claude skill
