# JobTrack - Web-based Python prototype

A web-based JobTrack prototype using FastAPI, Jinja2, CSS, and SQLite. No XAMPP is required. This is a local development prototype and is **not production-ready**.

## Run on Windows

1. Install Python 3.10+ (check `python --version`).
2. Extract this folder.
3. Open a terminal in this folder.
4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```
5. (Optional) Create demo records and demo accounts:

   ```bash
   python seed.py
   ```
6. Run the web server:

   ```bash
   python -m uvicorn main:app --reload
   ```
7. Open `http://127.0.0.1:8000` in your browser. Swagger API docs: `http://127.0.0.1:8000/docs`.

## Demo logins (created by seed.py)

- Admin: `admin@jobtrack.local` / `Admin123!`
- JO personnel: `personnel@jobtrack.local` / `Personnel123!`
- Applicant: `applicant@jobtrack.local` / `Applicant123!`

Registering through the site creates an applicant account.

## Use across computers on a local network

For a local demonstration on a shared Wi-Fi network, run the server on the host computer with:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then access it on another computer using the host computer's local IP address and port 8000. Keep the host computer/server running. This is a development/demo arrangement; don't expose it to the internet as-is.

## Prototype functions

- Applicant account registration and login
- Applicant dashboard and application tracking
- Open vacancy listing and application submission
- Optional resume upload (PDF/DOC/DOCX, max 5 MB)
- Admin vacancy creation and open/close status
- Admin review and application status/note updates
- Admin assignment record creation; selected account is converted to JO personnel role
- JO personnel dashboard to view assignment records and announcements
- Admin announcement posting
- JSON endpoints at `/api/vacancies` and `/api/announcements`
- Swagger API documentation at `/docs`

## Important limitations

This starter prototype needs additional security and functional work before real use: production session secret, CSRF protection, strict file scanning and file-serving controls, access audit logs, secure deployment, backups, data privacy policies and controls, application validation, assignment editing, and verification of real government workflows. Demo seed credentials must not be used in a real deployment. SQLite is a local prototype database.
