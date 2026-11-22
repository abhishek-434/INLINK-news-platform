# INKLINE — Digital News & Article Publishing Platform

> **Tagline:** *Stories worth your time. Ideas worth remembering.*

INKLINE is a full-featured, production-grade digital newspaper and magazine publishing web application built with **Python 3.11** and **Django 4.2 LTS**. It bridges the elegance of print editorial journalism with modern role-based access control, rich publishing pipelines, and server-side content protection.

---

## 1. Core Principles & Access Control Architecture

INKLINE implements a strict, server-side content protection model:

1. **Public Discovery:**
   - Anyone can browse the homepage, section indices, categories, tags, search results, headlines, cover photographs, and short teasers/excerpts.
2. **Server-Side Protected Content Gating:**
   - Full article content is **strictly withheld on the server side** (`full_content = None` in Django views) for unauthenticated visitors.
   - An editorial access barrier is displayed: *"Enjoying this story? Create a free account or log in to continue reading the complete article."*
   - Safe internal redirect preservation (`next={{ request.path|urlencode }}`) securely redirects readers back to the exact story they were reading after authentication or registration.
   - Open Redirect vulnerabilities are mitigated via `django.utils.http.url_has_allowed_host_and_scheme`.
3. **Controlled Editorial Publishing Pipeline:**
   - Authors cannot publish directly to the live platform.
   - Article lifecycle: `DRAFT` ➔ `SUBMITTED` ➔ `CHANGES_REQUESTED` ➔ `APPROVED` ➔ `PUBLISHED` (or `REJECTED` / `ARCHIVED`).
   - If an author modifies an already published article, it must be returned to editorial review to prevent unauthorized alterations.

---

## 2. User Roles & Capabilities

| Role | Access & Capabilities |
| :--- | :--- |
| **Reader** | Free account registration, browse public previews, read full articles after login, bookmark stories, participate in threaded comments, follow favorite authors, track reading history, report inappropriate content, manage notifications. |
| **Author** | Apply to become an author with professional bio, portfolio, and pitch; once approved by an administrator, access the dedicated Author Studio to compose stories with rich text, save drafts, view editor feedback, track story views, and resubmit revised drafts. |
| **Administrator** | Access custom Administrator Dashboard (powered by PostgreSQL/database-driven analytics and Chart.js), manage reader accounts, review author applications, moderate review queue (Approve & Publish, Request Changes with feedback, Reject), manage featured hero stories and Editor's Picks, moderate comments and reported content. |

---

## 3. Technology Stack

- **Backend:** Python 3.11.8, Django 4.2.30 LTS
- **Database:** PostgreSQL (production ready via `psycopg2-binary` and `dj-database-url`), with seamless local development fallback to SQLite3 (`db.sqlite3`)
- **Frontend:** HTML5, CSS3 (Custom Editorial Design System), Bootstrap 5.3, Bootstrap Icons 1.11.3
- **Typography:** *Playfair Display* (Editorial Headlines), *Inter* (Body Copy & UI), *JetBrains Mono* (Code)
- **Data Visualizations:** Chart.js 4.4
- **Security & Sanitization:** `bleach` (sanitizes rich-text input, removes executable scripts, invalidates event handlers and pseudo-protocols)
- **Static Assets:** WhiteNoise 6.6

---

## 4. Quick Start & Local Setup

### Step 1: Clone and Navigate to Project
```powershell
cd "d:\New folder"
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy the `.env.example` file to `.env`:
```powershell
cp .env.example .env
```
*(Default settings use SQLite3 automatically for zero-configuration local execution. To connect PostgreSQL, set `DATABASE_URL=postgres://user:password@localhost:5432/inkline_db`)*.

### Step 4: Run Database Migrations
```powershell
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Populate Demonstration Publishing Data
Run the built-in management command to seed categories, tags, sample authors, editors, readers, articles across categories, and analytics telemetry:
```powershell
python manage.py populate_sample_data
```

### Step 6: Collect Static Files
```powershell
python manage.py collectstatic --noinput
```

### Step 7: Launch the Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.

---

## 5. Demonstration Accounts

The sample data command pre-configures test accounts for all roles:

| Role | Username | Password | Email | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `AdminPassword123!` | `editor.in.chief@inkline.press` | Full superuser and administrator access |
| **Author (Tech)** | `maya_lin` | `AuthorPassword123!` | `maya.lin@inkline.press` | Dr. Maya Lin (Computing & AI beats) |
| **Author (Economics)** | `julian_sterling` | `AuthorPassword123!` | `julian.sterling@inkline.press` | Julian Sterling (Trade & Markets) |
| **Author (Culture)** | `elena_rostova` | `AuthorPassword123!` | `elena.rostova@inkline.press` | Elena Rostova (Architecture & Culture) |
| **Reader 1** | `clara_b` | `ReaderPassword123!` | `clara@example.com` | Has pending author application in review queue |
| **Reader 2** | `marcus_a` | `ReaderPassword123!` | `marcus@example.com` | Active reader with saved bookmarks |

To create a new custom superuser:
```powershell
python manage.py createsuperuser
```

---

## 6. Automated Test Suite

INKLINE includes an automated test suite with 24 test cases covering authentication, server-side content protection, editorial workflows, author permissions, reader features, and security defenses:

```powershell
python manage.py test tests
```

### Test Coverage Highlights:
- **`tests/test_authentication.py`**: Reader registration, login/logout, duplicate email prevention, invalid credentials, safe post-login redirection.
- **`tests/test_permissions.py`**: Reader isolation from author/admin areas, author isolation from other authors' drafts, rejection of non-staff administrative access.
- **`tests/test_publishing_workflow.py`**: Saving drafts, submitting for review, administrator approval & immediate publishing, change request feedback loops, rejection handling.
- **`tests/test_access_restriction.py`**: Strict server-side verification that unauthenticated visitors cannot access full article bodies in the HTTP response; verified delivery to authenticated members.
- **`tests/test_reader_features.py`**: Bookmark toggling, comment creation and owner deletion, author following and unfollowing.
- **`tests/test_security.py`**: Open redirect attack neutralization, HTML XSS injection stripping (removing `<script>`, event handlers, and javascript pseudo-protocols), role escalation prevention.

---

## 7. Production Deployment Preparation

1. **Environment Variables**:
   - Set `DEBUG=False` in `.env`.
   - Set `ALLOWED_HOSTS` to your production domain(s) (e.g. `ALLOWED_HOSTS=inkline.press,www.inkline.press`).
   - Generate a cryptographically secure `SECRET_KEY`.
   - Provide your PostgreSQL connection string:
     ```bash
     DATABASE_URL=postgres://inkline_prod_user:StrongPassword@postgres.internal:5432/inkline_production
     ```
2. **Security Headers**:
   - When `DEBUG=False`, INKLINE automatically enforces:
     - `SECURE_BROWSER_XSS_FILTER = True`
     - `SECURE_CONTENT_TYPE_NOSNIFF = True`
     - `X_FRAME_OPTIONS = 'DENY'`
     - `SESSION_COOKIE_SECURE = True`
     - `CSRF_COOKIE_SECURE = True`
3. **WSGI / ASGI & Reverse Proxy**:
   - Serve application via Gunicorn / Uvicorn behind Nginx or Caddy:
     ```bash
     gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
     ```
4. **Static & Media Files**:
   - Static assets are compressed and fingerprinted by WhiteNoise (`CompressedManifestStaticFilesStorage`).
   - Media uploads (`/media/`) should be served via persistent volume storage or S3-compatible object storage (e.g., AWS S3 via `django-storages`).

---

## 8. Editorial Design System

INKLINE utilizes a high-contrast editorial aesthetic:
- **Palette:** Warm Ivory (`#F8F7F3`), Deep Charcoal (`#1E1E1E`), Editorial Burgundy (`#800020`), Muted Amber (`#D97706`), Warm Border (`#E6E4DC`).
- **Typography:** High-contrast serif headlines (*Playfair Display*) paired with clean neutral grotesk UI typography (*Inter*).
- **Interactions:** Top reading progress indicator bar, animated bookmark toggles, instant client-side word count & reading time estimation, responsive editorial grid layouts across desktop, tablet, and mobile displays.
