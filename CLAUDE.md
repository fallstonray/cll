# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CLL** is a Django web app for Classic Landscape Landscaping — an internal business tool for managing customers, maintenance contracts, site visits, and employees. It is a server-rendered HTML app (no REST API consumed by a frontend; `djangorestframework` is installed but unused).

## Common Commands

```bash
# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create a new migration after model changes
python manage.py makemigrations <app_name>

# Run tests (test files exist but are currently empty)
python manage.py test maintenance
python manage.py test visits
python manage.py test employee

# Open Django shell
python manage.py shell
```

## Environment Setup

Requires a `.env` file at the project root (see `.env.example`). Key variables:

```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=cll2023
DB_USER=postgres
DB_PASSWORD=...
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

Database: **PostgreSQL** via `psycopg2-binary`. Django is pinned to **4.2 LTS** for PostgreSQL 12 compatibility.

## Architecture

### App Structure

| App | Purpose |
|---|---|
| `maintenance` | Customers, contracts, dashboard — the core app. Hosts the base template. |
| `visits` | Individual site visit records linked to a contract |
| `employee` | Employee and position management |

All apps follow the same pattern: `models.py` → `forms.py` → `filters.py` → `views.py` → `urls.py` → `templates/<app>/`.

### Data Model Relationships

```
Customer (maintenance)
  └── Contract (maintenance)  [site_customer FK]
        ├── Soldby             [salesrep FK]
        ├── Mulchcolor         [mulch_color FK]
        └── Visit (visits)     [visit_contract FK]
              ├── VisitType    [visit_type_name FK]
              └── Employee     [crew_leader FK]
                    └── Position [employee_title FK]
```

All core models use a `uuid` field (not the PK) for URL routing — URLs use `<uuid:uuid>` patterns. `is_active` booleans soft-delete Contracts and Employees.

### URL Routing

Root `cll/urls.py` includes all three app `urls.py` files at the root prefix (no path prefix). Key URL patterns:

- `/`, `/home` — dashboard
- `/customers/`, `/customer/<uuid>/` — customer management
- `/maintenance/`, `/view_contract/<uuid>/` — contract management
- `/visits/`, `/view_visit/<uuid>/` — visit management
- `/employees/`, `/employees/inactive/` — employee management
- `/login`, `/logout`, `/sign-up`, `/password-reset/` — auth

### Templates

Base template: `maintenance/templates/maintenance/main.html`  
Navbar: `maintenance/templates/maintenance/navbar.html`  
Frontend: **Bootstrap 5.3** via CDN + `crispy-bootstrap5` for form rendering.

All templates extend `maintenance/main.html`. Date values should be formatted with Django's `|date:"F j, Y"` filter (e.g. "May 26, 2026") — this is the standard used throughout the app.

### Authentication & Security

- All views protected with `@login_required(login_url="/login")`
- Some views also use `@permission_required`
- `django-axes` provides brute-force protection: 5 failed attempts locks the account for 1 hour, keyed on IP + username
- `AxesStandaloneBackend` must remain in `AUTHENTICATION_BACKENDS` alongside `ModelBackend`
- Logout uses POST (not GET) — required for Django 5.x compatibility (already implemented)
- Password reset via Gmail SMTP on port 587 with TLS

### Forms & Filtering

Forms use `ModelForm` subclasses in each app's `forms.py`. New user registration uses a custom `RegisterForm` in `maintenance/forms.py`.

List views use `django-filter` — filter classes are in each app's `filters.py` and passed as `myFilter` context. Current filters: `ContractFilter` (by `site_name`), `CustomerFilter` (by `name`), `VisitsFilter`.
