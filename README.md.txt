Math Tutor DC
=============

A tutoring business website hosted on GitHub Pages. The goal is to expand to $200k+ monthly revenue by matching recently graduated college professionals with high school and early college students needing math and statistics tutoring.

Business model: we source clients, match them with tutors, collect payments, handle scheduling, and provide tutoring materials—taking a small margin.

Live site: https://dcmathtutor.github.io/math-tutor-dc/
Admin:     https://dcmathtutor.github.io/math-tutor-dc/admin.html
Backend:   https://math-tutor-backend-y3uz.onrender.com (see Desktop/backend-tutor for the separate repo)

All scheduling and payment collection is done manually for now.


Project structure
-----------------

    index.html          Public-facing website + contact form
    admin.html          Secure admin dashboard (login required)
    assets/             Images (logo, tutor photos, favicon)
    backend/
      app.py            Python/Flask API (to replace Desktop/backend-tutor on Render)
      requirements.txt  Python dependencies
      .env.example      Environment variable template – set real values in Render's dashboard
      .env              NOT in git. Contains secrets. See setup below.
    old_backend.py      Original backend – kept for reference


Backend setup (Render.com)
--------------------------

The backend is Python/Flask. Currently deployed from Desktop/backend-tutor.
To switch to this repo (recommended – keeps everything in one place):

1. In Render, update the service: Connected Repo → this repo, Root Directory = backend
2. Build command:  pip install -r requirements.txt
3. Start command:  gunicorn app:app
4. In Render's "Environment" tab – existing vars stay, add two new ones:

   RESEND_API_KEY        Already set – no change
   EMAIL_TO              Already set – no change
   ADMIN_PASSWORD_HASH   NEW – bcrypt hash of your admin password
                         Generate: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
   JWT_SECRET            NEW – long random string
                         Generate: python -c "import secrets; print(secrets.token_hex(48))"

Set these directly in Render's dashboard – never in a local file – to keep
the password hidden from AI assistants and out of version control.


Admin page
----------

URL: https://dcmathtutor.github.io/math-tutor-dc/admin.html

Features:
  - Secure login (JWT session, password stored only as bcrypt hash in Render)
  - Overview stats: total leads, last 7 days, sources tracked
  - QR Code Generator: pre-built codes for Flyer A/B, Instagram, Facebook, Google, Referral
    Add custom sources; download any code as high-res PNG
  - Source breakdown table with lead counts per campaign
  - All Leads: searchable/filterable table with email links


QR Code / Campaign tracking
----------------------------

Each QR code points to:
  https://dcmathtutor.github.io/math-tutor-dc/?src=flyer_a

The ?src= value is silently captured in a hidden form field. On submission it is
logged to the database and appended to the email subject:
  "New Math Tutoring Request [flyer_a]"

All QR codes are visible and downloadable from the admin page.


TODO
----

- Portal to add/edit tutors
- Log payments in SQL backend
- Tutor schedules / availability
- Graphic design Claude skill
- Deploy
