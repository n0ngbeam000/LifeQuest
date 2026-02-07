# LifeQuest

Django-based web application for LifeQuest.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd LifeQuest
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
# Copy the .env.example to .env
cp .env.example .env

# Edit .env file and set your configuration
# - SECRET_KEY: Generate a new secret key for production
# - DEBUG: Set to False for production
```

### 5. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Project Structure

```
LifeQuest/
├── core/                    # Main Django app
│   ├── models.py           # Database models
│   ├── views.py            # View logic
│   ├── forms.py            # Form definitions
│   ├── urls.py             # URL routing
│   ├── static/             # Static files (CSS, JS, images)
│   └── templates/          # HTML templates
├── life_quest/             # Project settings
│   ├── settings.py         # Django configuration
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI configuration
├── manage.py               # Django management script
├── db.sqlite3              # SQLite database
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
└── .gitignore              # Git ignore rules
```

## Admin Panel

Access the admin panel at `http://localhost:8000/admin/` with your superuser credentials.

## Common Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Start development server
python manage.py runserver
```

## Notes for Collaborators

1. Always activate the virtual environment before working
2. Create `.env` file from `.env.example` and set your local configuration
3. Run migrations after pulling changes
4. Do not commit `.env`, `venv/`, or `db.sqlite3` (already in .gitignore)

## License


