# LifeQuest

A gamified productivity web app built with Django. Turn your daily tasks into quests, earn XP, level up your character, and compete on the leaderboard with other adventurers.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
  - [5. Set Up PostgreSQL](#5-set-up-postgresql)
  - [6. Run Migrations](#6-run-migrations)
  - [7. Start the Development Server](#7-start-the-development-server)
- [Environment Variables Reference](#environment-variables-reference)
- [Project Structure](#project-structure)
- [Game System](#game-system)
- [Pages & URLs](#pages--urls)
- [API Endpoints (AJAX)](#api-endpoints-ajax)
- [Contributing](#contributing)
- [Common Commands](#common-commands)

---

## Features

- **Quest Board** — Add, complete, and delete quests with real-time AJAX updates (no page reload)
- **XP & Leveling System** — Earn experience points by completing quests; level up with a scaling formula
- **Difficulty Tiers** — Easy / Medium / Hard / Epic, each awarding different XP
- **Hall of Fame Leaderboard** — Podium-style top-3 display + ranked list for all players
- **Completed Quests Log** — Full history grouped by completion date
- **Email Verification** — New accounts must verify their email before logging in
- **Password Reset** — Secure reset flow via Gmail SMTP
- **Google OAuth** — One-click sign-in via Google (django-allauth)
- **Responsive Design** — Works on mobile, tablet, and desktop
- **Mobile Side Menu** — Off-canvas hamburger navigation with live EXP bar

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0 (Python 3.8+) |
| Database | PostgreSQL |
| Authentication | django-allauth 65.x + Django built-in auth |
| Frontend | Vanilla HTML / CSS / JavaScript (no framework) |
| Icons | Font Awesome 6.4 (CDN) |
| Fonts | Poppins + VT323 (Google Fonts CDN) |
| Email | Gmail SMTP (TLS, port 587) |
| Environment | python-dotenv |

---

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.8+** — [python.org/downloads](https://www.python.org/downloads/)
- **PostgreSQL 13+** — [postgresql.org/download](https://www.postgresql.org/download/)
- **Git** — [git-scm.com](https://git-scm.com/)
- A **Gmail account** with an App Password enabled (for email verification / password reset)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd LifeQuest
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt once active.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in every value. See the [Environment Variables Reference](#environment-variables-reference) section below for details on each key.

> **Important:** Never commit `.env` to version control. It is already in `.gitignore`. If you accidentally push it, rotate all secrets immediately.

### 5. Set Up PostgreSQL

Open `psql` (or any PostgreSQL client) and create the database:

```sql
CREATE DATABASE lifequest_db;
```

The app connects to `localhost:5432` with user `postgres` and the password from your `.env` file (`DB_PASSWORD`). If your PostgreSQL setup uses a different user, host, or port, edit the `DATABASES` block in `life_quest/settings.py`.

### 6. Run Migrations

```bash
python manage.py migrate
```

Optionally create a superuser to access the Django admin panel:

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

Open **http://localhost:8000** in your browser.

---

## Environment Variables Reference

Your `.env` file (at the project root) must contain these keys:

```env
# ── Django Core ────────────────────────────────────────────────────────────────
SECRET_KEY=your-long-random-secret-key-here
DEBUG=True

# ── Database (PostgreSQL) ───────────────────────────────────────────────────────
DB_PASSWORD=your-postgres-password

# ── Email — Gmail SMTP ──────────────────────────────────────────────────────────
# Use a Gmail App Password, NOT your normal Gmail password.
# Enable App Passwords at: https://myaccount.google.com/apppasswords
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# ── Google OAuth (optional) ─────────────────────────────────────────────────────
# Create credentials at: https://console.cloud.google.com/
# Authorised redirect URI: http://localhost:8000/accounts/google/login/callback/
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

> Google OAuth is optional. If you leave `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` empty, the site still works with username/password authentication.

---

## Project Structure

```
LifeQuest/
│
├── life_quest/                   # Django project configuration package
│   ├── settings.py               # All settings — reads values from .env
│   ├── urls.py                   # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                         # The main (and only) Django app
│   ├── models.py                 # UserProfile, Task
│   ├── views.py                  # All views: dashboard, auth, tasks, leaderboard
│   ├── forms.py                  # RegisterForm, LoginForm
│   ├── admin.py                  # Django admin registration
│   │
│   ├── migrations/               # Database migration files (commit these)
│   │   ├── 0001_initial.py
│   │   ├── 0002_task_completed_at.py
│   │   └── 0003_add_epic_difficulty.py
│   │
│   ├── templates/core/           # HTML templates — each page is standalone
│   │   ├── dashboard.html        # Main quest board
│   │   ├── leaderboard.html      # Hall of Fame / podium page
│   │   ├── completed_quests.html # Full quest history grouped by date
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── forgot_password.html
│   │   ├── reset_password.html
│   │   └── reset_password_done.html
│   │
│   └── static/core/
│       ├── css/
│       │   ├── dashboard.css     # Main styles, CSS variables, responsive rules
│       │   ├── leaderboard.css   # Podium animations, leaderboard responsive
│       │   ├── auth.css          # Login / register page styles
│       │   └── style.css         # Shared / global styles
│       ├── js/
│       │   ├── dashboard.js      # AJAX quest actions, mobile menu, EXP updates
│       │   ├── leaderboard.js    # Floating particle animation system
│       │   ├── auth.js           # Auth page interactions
│       │   └── form.js           # General form helpers
│       └── images/
│           └── LogoLifeQuest.png
│
├── manage.py
├── requirements.txt
├── .env.example                  # Template — copy to .env and fill in
├── .env                          # Your local secrets — DO NOT COMMIT
└── db.sqlite3                    # SQLite fallback (not used; PostgreSQL is active)
```

---

## Game System

### Difficulty Tiers & XP Rewards

| Difficulty | XP Reward | Suggested Task Size |
|---|---|---|
| ⚡ Easy | +10 XP | Quick tasks, minor habits (< 15 min) |
| 🔥 Medium | +30 XP | Standard daily tasks (15–60 min) |
| 💀 Hard | +50 XP | Complex tasks, deep focus (1–3 hrs) |
| ⚔️ Epic | +100 XP | Boss-level projects & milestones (> 3 hrs) |

### Level-Up Formula

```
EXP required to reach next level = current_level × 123
```

| Current Level | EXP Needed |
|---|---|
| 1 | 123 XP |
| 5 | 615 XP |
| 10 | 1,230 XP |
| 20 | 2,460 XP |

When a completed quest is **undone**, the XP is deducted. If the deduction drops the player below 0 EXP for their current level, the system automatically de-levels and recalculates — a player can never go below Level 1 / 0 EXP.

### Avatar Tiers

The player's avatar style changes automatically based on their level:

| Level Range | Avatar |
|---|---|
| 1 – 5 | Freshy |
| 6 – 15 | Engineer (with gear) |
| 16 + | Graduate |

---

## Pages & URLs

| URL | View | Login Required | Description |
|---|---|---|---|
| `/` | `dashboard_view` | Yes | Quest Board |
| `/login/` | `login_view` | No | Login page |
| `/register/` | `register_view` | No | Registration + email verification |
| `/logout/` | Django built-in | — | Logs out, redirects to `/login/` |
| `/leaderboard/` | `leaderboard_view` | Yes | Hall of Fame podium + ranked list |
| `/completed/` | `completed_quests_view` | Yes | Full quest history by date |
| `/forgot-password/` | `forgot_password` | No | Request a password-reset email |
| `/reset-password/<uidb64>/<token>/` | `reset_password` | No | Set a new password from email link |
| `/reset-password/done/` | `reset_password_done` | No | Confirmation after successful reset |
| `/admin/` | Django admin | Superuser | Site administration panel |
| `/accounts/` | allauth | — | Google OAuth callback + email confirmation |

---

## API Endpoints (AJAX)

These endpoints are called by `dashboard.js` via `fetch()` and return JSON. All require the user to be logged in and a valid CSRF token in the `X-CSRFToken` request header.

| URL | Method | Description | Key Response Fields |
|---|---|---|---|
| `/add-task/` | POST | Create a new quest | `status`, `quest` |
| `/complete/<id>/` | POST | Complete a quest and award XP | `status`, `quest`, `new_exp`, `new_level`, `exp_percentage`, `leveled_up`, `xp_gained` |
| `/delete/<id>/` | POST | Permanently delete a quest | `status`, `quest_id` |
| `/uncomplete_task/<id>/` | POST | Undo a completion and deduct XP | `status`, `quest`, `next_completed`, `new_exp`, `new_level`, `exp_percentage`, `xp_lost` |

---

## Contributing

1. **Fork** the repository and create a branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Set up your environment** following the [Getting Started](#getting-started) steps.

3. **Make your changes.** Keep pull requests focused — one feature or fix per PR.

4. **Test manually** in the browser on both desktop and mobile before opening a PR. There is currently no automated test suite, so please verify all affected pages.

5. **Create a migration** if you changed any model:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Push your branch** and open a Pull Request against `main`. Clearly describe what changed and why.

### Code Conventions

| Area | Convention |
|---|---|
| Templates | Each page is a standalone HTML file — no shared base template |
| CSS | Theme colours and sizes are CSS custom properties in `dashboard.css :root` — use variables, don't hardcode values |
| JavaScript | Vanilla JS only — no jQuery or frameworks; AJAX uses `fetch()` with CSRF tokens |
| Views | Business logic lives in views; AJAX endpoints return JSON responses |
| Branch names | `feature/<name>`, `fix/<name>`, `hotfix/<name>` |

---

## Common Commands

```bash
# Activate the virtual environment (run this first every session)
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

# Start the development server
python manage.py runserver

# Create and apply migrations after changing a model
python manage.py makemigrations
python manage.py migrate

# Open the Django interactive shell
python manage.py shell

# Create a superuser for the admin panel
python manage.py createsuperuser

# Collect static files (needed for production deployments)
python manage.py collectstatic

# Run the test suite
python manage.py test
```
