# HireHub — Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Deploy to Railway](#deploy-to-railway)
3. [Deploy to Render](#deploy-to-render)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Post-Deploy Checklist](#post-deploy-checklist)

---

## Local Development

### 1. Clone & install
```bash
git clone https://github.com/your-username/job-portal.git
cd job-portal

python -m venv venv
# Windows:
venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Create your `.env` file
```bash
cp .env.example .env
```
Open `.env` and set at minimum:
```
SECRET_KEY=any-random-string-here
DJANGO_SETTINGS_MODULE=job_portal.settings.development
```

### 3. Run migrations & start
```bash
python manage.py migrate
python manage.py createsuperuser   # optional — for admin panel
python manage.py runserver
```
Visit → http://127.0.0.1:8000

> **Chat feature locally:** WebSockets use an in-memory channel layer in
> development — no Redis needed. Simply run `python manage.py runserver`.

---

## Deploy to Railway

Railway is the easiest option. It gives you a free PostgreSQL database,
free Redis, and auto-deploys from GitHub.

### Step 1 — Push your code to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/job-portal.git
git push -u origin main
```

### Step 2 — Create a Railway project
1. Go to [railway.app](https://railway.app) → **New Project**
2. Choose **Deploy from GitHub repo** → select your repository
3. Railway detects `nixpacks.toml` and builds automatically

### Step 3 — Add PostgreSQL
1. Inside your project → **+ New** → **Database** → **PostgreSQL**
2. Railway auto-injects `DATABASE_URL` into your service — done

### Step 4 — Add Redis
1. **+ New** → **Database** → **Redis**
2. Railway auto-injects `REDIS_URL` — done

### Step 5 — Set environment variables
Go to your web service → **Variables** tab → add:

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `job_portal.settings.production` |
| `SECRET_KEY` | *(generate one — see below)* |
| `ALLOWED_HOSTS` | `your-app-name.up.railway.app` |

**Generate a secret key:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Step 6 — Generate a domain
Service → **Settings** → **Networking** → **Generate Domain**

Your site is live at `https://your-app.up.railway.app` 🎉

---

## Deploy to Render

### Step 1 — Push to GitHub (same as Railway Step 1 above)

### Step 2 — Create services from `render.yaml`
1. Go to [render.com](https://render.com) → **New** → **Blueprint**
2. Connect your GitHub repo — Render reads `render.yaml` automatically
3. It creates: **Web Service + PostgreSQL + Redis** in one click

### Step 3 — Set environment variables
In the Web Service → **Environment** tab:

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `job_portal.settings.production` |
| `SECRET_KEY` | *(generate — see above)* |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` |

`DATABASE_URL` and `REDIS_URL` are linked automatically by `render.yaml`.

### Step 4 — First deploy
Render runs the build command automatically:
```
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
```
Then starts Daphne. Check **Logs** tab for any errors.

---

## Environment Variables Reference

| Variable | Required | Dev default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Django secret key. Generate fresh for prod. |
| `DJANGO_SETTINGS_MODULE` | ✅ | `job_portal.settings.development` | Which settings file to load |
| `DATABASE_URL` | Prod only | SQLite | Postgres connection string |
| `REDIS_URL` | Prod only | In-memory | Redis for WebSocket chat |
| `ALLOWED_HOSTS` | Prod only | `*` | Comma-separated domain list |
| `EMAIL_HOST_USER` | Optional | — | SMTP username |
| `EMAIL_HOST_PASSWORD` | Optional | — | SMTP app password |
| `DEFAULT_FROM_EMAIL` | Optional | — | From address for emails |
| `GOOGLE_CLIENT_ID` | Optional | — | For Google OAuth login |
| `GOOGLE_CLIENT_SECRET` | Optional | — | For Google OAuth login |

---

## Post-Deploy Checklist

After your first successful deploy:

- [ ] Visit `/admin/` — log in with superuser credentials
- [ ] **Sites** → change `example.com` to your actual domain
      (required for Google OAuth and allauth to work correctly)
- [ ] **Social Applications** → add Google credentials if using OAuth
- [ ] Create job categories at `/admin/jobs/category/add/`
- [ ] Test register → login → post job → apply flow end to end
- [ ] Test the chat room (needs Redis — check Railway/Render Redis logs)
- [ ] Set `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` in `base.py`
      once your SMTP email is configured

### Change admin password
```bash
# On Railway — open a shell in your service
python manage.py changepassword admin
```

---

## Useful Commands (Railway Shell / Render Shell)

```bash
# Create superuser
python manage.py createsuperuser

# Run migrations manually
python manage.py migrate

# Check for any configuration errors
python manage.py check --deploy

# Open Django shell
python manage.py shell
```

---

## Architecture Overview

```
Browser ──HTTPS──▶ Railway/Render (SSL termination)
                        │
                        ▼
              Daphne (ASGI server)
             ╱                    ╲
        HTTP requests        WebSocket /ws/chat/
             │                       │
        Django Views           Channels Consumer
             │                       │
        PostgreSQL              Redis Channel Layer
```

Static files are served by **WhiteNoise** — no separate CDN or S3 needed.
