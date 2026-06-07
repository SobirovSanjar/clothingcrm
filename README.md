# ClothCRM — Cloud CRM (FastAPI + PostgreSQL)

A server-rendered CRM web application for a **wholesale clothing company**, built
for the BTEC **Unit 6: Networking in the Cloud** scenario (migrating ERP / CRM /
WMS systems to a cloud platform). This repository is the **CRM** dynamic website
that is deployed and tested as part of the networking solution
(criteria C.P5 / C.P6 — *design and implement a networked cloud solution*).

## Features

- **Authentication** — session-based login with PBKDF2-hashed passwords.
- **Dashboard** — KPIs, sales pipeline overview, recent orders/activity, low-stock alerts.
- **Customers** — full CRUD for wholesale accounts (retailers, distributors, boutiques, online stores).
- **Contacts** — people linked to each customer.
- **Pipeline (Leads/Opportunities)** — Kanban board + list view across 7 stages.
- **Products** — clothing catalogue with SKU, size, colour, price and stock.
- **Orders** — orders with line items and automatic total calculation.
- **Activities** — calls, emails, meetings, tasks and notes with due dates.
- **JSON REST API** — under `/api` (plus interactive docs at `/docs`) for ERP/WMS integration and load testing.

## Tech stack

| Layer     | Technology |
|-----------|------------|
| Web       | FastAPI, Starlette sessions, Jinja2 templates |
| Database  | PostgreSQL via SQLAlchemy 2.0 (async, asyncpg) |
| Server    | Uvicorn (ASGI) |
| Frontend  | Server-rendered HTML + a single hand-written CSS file (no build step) |

> Note: Jinja templates use `[[ ... ]]` for variable output (configured in
> `app/templating.py`) while control tags stay as `{% ... %}`.

## Project layout

```
crm-app/
├─ app/
│  ├─ main.py            # FastAPI app, middleware, route registration
│  ├─ config.py          # Environment-driven settings
│  ├─ database.py        # Async engine, session, table creation
│  ├─ models.py          # SQLAlchemy ORM models
│  ├─ security.py        # PBKDF2 password hashing
│  ├─ dependencies.py    # Current-user dependency
│  ├─ templating.py      # Jinja2 setup + filters
│  ├─ seed.py            # Demo data loader
│  ├─ routers/           # auth, dashboard, customers, contacts, leads,
│  │                      #   products, orders, activities, api
│  ├─ templates/         # Jinja2 HTML templates
│  └─ static/css/        # Stylesheet
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ .env.example
└─ run.sh
```

## Quick start (Docker — recommended)

This builds the app and a PostgreSQL database, seeds demo data and serves the site.

```bash
docker compose up --build
```

Then open <http://localhost:8000> and sign in with:

- **admin@clothcrm.local** / **admin123**
- **sales@clothcrm.local** / **sales123**

## Quick start (local Python)

Requires Python 3.11+ and a running PostgreSQL instance.

```bash
# 1. Create a database and user (example using psql)
#    CREATE USER crm WITH PASSWORD 'crm';
#    CREATE DATABASE crm OWNER crm;

# 2. Set up the project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL if needed

# 3. Seed demo data and run
python -m app.seed
uvicorn app.main:app --reload
```

Or simply: `./run.sh`

## Configuration

All configuration is read from environment variables (see `.env.example`):

| Variable          | Default | Description |
|-------------------|---------|-------------|
| `DATABASE_URL`    | `postgresql+asyncpg://crm:crm@localhost:5432/crm` | Async PostgreSQL URL |
| `SECRET_KEY`      | `dev-secret-change-me` | Session cookie signing key |
| `APP_NAME`        | `ClothCRM` | Display name |
| `SESSION_MAX_AGE` | `28800` | Session lifetime (seconds) |
| `DB_POOL_SIZE`    | `10` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `20` | Extra pooled connections under load |

## REST API

| Method | Path             | Description |
|--------|------------------|-------------|
| GET    | `/api/health`    | Liveness + DB connectivity check (public) |
| GET    | `/api/stats`     | Aggregate counts and open pipeline value |
| GET    | `/api/customers` | List customers as JSON |
| GET    | `/api/products`  | List products as JSON |
| GET    | `/api/orders`    | List orders as JSON |

Interactive Swagger docs are available at `/docs`.

## How this maps to the cloud networking assignment

- The app is **stateless** (sessions are signed cookies, all data in PostgreSQL),
  so it can sit behind a **load balancer** and scale horizontally across multiple
  instances — directly supporting the auto-scaling / load-balancing requirements.
- `DATABASE_URL` points at a managed database that would live in a **private subnet**
  of a VPC, while the web tier sits in a **public subnet** behind the load balancer.
- `/api/health` provides the health-check endpoint a load balancer / target group
  uses to route traffic only to healthy instances.
- Connection pooling (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`) tunes behaviour under load
  for the performance/scalability testing tasks (M3 / D2 / M4).

## Notes

- Tables are created automatically on startup (`Base.metadata.create_all`). For a
  production deployment you would add Alembic migrations.
- Passwords are hashed with PBKDF2-SHA256 from the standard library (no native
  build dependencies required).


nima gap?