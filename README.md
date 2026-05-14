<div align="center">

# Pelotão System

**Web operations system for internal police platoon management**  
Tactical unit / ROCAM · roster · profiles · patrol vehicles · logs

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docs.docker.com/compose/)
[![Tailwind](https://img.shields.io/badge/Tailwind-4-06B6D4?style=flat-square&logo=tailwindcss)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**[Portuguese version (pt-BR) →](READMEptbr.md)**

</div>

---

## Overview

**Pelotão System** is an internal **full-stack** application: **JWT** authentication, signup with **command-level approval**, granular **RBAC**, an operations dashboard, **roster** ordering by rank with persisted **drag-and-drop** seniority, detailed **officer profiles**, a **patrol vehicle** module (FT and ROCAM) with automatic **operational history and logs**, and a **dashboard** feed of recent fleet events.

The UI uses a **dark** operational theme, a **responsive sidebar** (hamburger menu on mobile), and **Docker** packaging.

### Motivation

The project aims to **ease repetitive platoon workflows**, make them **more dynamic**, and give time back to the roster. The data model reflects **real operations** during shifts and how the platoon actually works.

This is not a commercial product: **AI-assisted development** (*vibe coding*) was used to move faster and review LLM-generated code, always with human oversight. Prompts follow a **fixed template**, changing only the goal of each task. **Cursor MCPs** supported the workflow—especially **Context7** for up-to-date documentation; the **Playwright** MCP was used to assist UI testing when it fit the task.

---

## Operational goals

Centralize, with traceability:

- who is on the roster, in what hierarchical order, and with which personnel data;
- vehicle state (in service, out of service, maintenance, reserve) and **who** changed **what** and **why**;
- access driven by the officer’s **application role** (do not confuse institutional **rank** with app **role**).

---

## Screenshots

[Login](docs/screenshots/login.png)
[Dashboard](docs/screenshots/dashboard.png)
[Roster] |(docs/screenshots/efetivo.png)
[Vehicles](docs/screenshots/viaturas.png)
[Profile](docs/screenshots/perfil.png)

---

## Stack

| Layer | Technology |
|-------|------------|
| API | **FastAPI** 0.115, **Uvicorn**, **Pydantic** v2 |
| ORM / DB | **SQLAlchemy** 2.0, **Alembic**, **PostgreSQL** 16, **psycopg** 3 |
| Auth | **JWT** (`python-jose`), **bcrypt** passwords |
| Frontend | **React** 19, **TypeScript**, **Vite** 6, **react-router-dom** 7 |
| UI | **Tailwind CSS** 4 (`@tailwindcss/vite`), **Lucide** icons |
| DnD | **@dnd-kit** (core, sortable, utilities) |
| Local deploy | **Docker Compose** (Postgres + API + static Nginx) |

---

## Architecture

```
┌─────────────┐     HTTPS/HTTP      ┌──────────────┐
│   Browser   │ ◄──────────────────► │  Nginx :80   │  (Vite static build)
└──────┬──────┘                      └──────┬───────┘
       │                                    │
       │  VITE_API_URL (build)              │  browser → API (configure CORS)
       ▼                                    ▼
┌──────────────┐   JSON + Bearer JWT   ┌──────────────┐
│ React (SPA)  │ ◄──────────────────► │ FastAPI :8000│
└──────────────┘                      └──────┬───────┘
                                              │
                                              ▼ SQL (psycopg)
                                       ┌──────────────┐
                                       │ PostgreSQL   │
                                       └──────────────┘
```

- The **SPA** calls the REST API; the JWT lives in `localStorage` (`Authorization: Bearer`).
- The **backend** validates JWT, applies RBAC dependencies per route, and persists with SQLAlchemy.
- **Alembic migrations** version the schema (including native PostgreSQL ENUMs without duplicating `CREATE TYPE` in existing migrations).
- **Backend container startup** runs `alembic upgrade head` in the entrypoint before Uvicorn.

---

## Repository layout (summary)

```text
pelotao-system/
├── backend/
│   ├── alembic/              # env.py + versions (001…003)
│   ├── auth/                 # JWT, deps, password hashing
│   ├── core/                 # config, ranks (rank ordering)
│   ├── database/             # Base, session
│   ├── models/               # User, Vehicle, VehicleLog
│   ├── routes/               # auth, users, vehicles
│   ├── schemas/              # Pydantic
│   ├── services/             # business rules
│   ├── main.py
│   ├── requirements.txt
│   └── docker-entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── components/       # ProtectedRoute, SortablePoliceRow, vehicle/…
│   │   ├── constants/        # ranks.ts
│   │   ├── hooks/            # AuthContext
│   │   ├── layouts/          # OperationalLayout (sidebar)
│   │   ├── pages/            # Login, Register, Dashboard, Efetivo, Viaturas, Perfil, PendingUsers
│   │   ├── services/         # api, authApi, usersApi, vehiclesApi
│   │   └── types.ts + types/vehicle.ts
│   ├── package.json
│   └── nginx.conf            # nginx stage of the frontend Dockerfile
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docs/screenshots/         # screenshot placeholders
├── prompts/                  # prompt drafts (not used at runtime)
├── .env.example
├── LICENSE
├── README.md                 # this file (en-US)
└── READMEptbr.md             # Portuguese documentation
```

---

## Implemented features

| Module | What exists today |
|--------|-------------------|
| Authentication | Signup (`PENDING`); login only for `APPROVED` + `is_active`; JWT HS256; configurable expiry (`access_token_expire_minutes`, default 24h). |
| Approvals | Pending list; approve with required **role** or reject (`ADMIN`, `N90`, `TAT_CMD`). |
| Admin bootstrap | If `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set in `.env`, creates an admin on startup (if the email does not exist). |
| Dashboard | Welcome + **latest vehicle logs** (`GET /vehicles/recent-logs`). |
| Layout | Sidebar: Dashboard, Roster, Vehicles, Profile + **Approvals** (approvers only). |
| Roster | Approved users grouped by rank; **DnD** per rank (command); persisted `display_order`. |
| Profile | Operational fields (full name, ID number, address, etc.); edits per RBAC. |
| Vehicles | **FT** / **ROCAM** listing; create / edit status (with reason); per-vehicle log timeline; global feed. |
| Health | `GET /health` |

---

## RBAC (`UserRole`)

| Role | Main effect in the current codebase |
|------|-------------------------------------|
| **ADMIN** | Full access to approvals, roster (reorder + profiles + `is_active`), vehicles (CRUD + status). |
| **N90** | Same as approver / roster staff / vehicles. |
| **TAT_CMD** | Same. |
| **BRACAL** | Edits **own** profile; cannot change `is_active`; can **create/update vehicles** and status; cannot reorder roster or approve signups. |
| **ESTAGIO** | Edits **own** profile; **read-only** on vehicles (no create/status change); cannot reorder roster. |

> Institutional **rank** (text field) ≠ application **role** (enum).

Backend dependencies:

- `require_approver` / `STAFF_EDITOR_ROLES` → approvals + `PUT /users/efetivo/reorder` + broad profile edits.
- `require_vehicle_editor` (`VEHICLE_EDITOR_ROLES`) → `POST/PATCH` on `/vehicles`.

---

## Authentication flow

1. `POST /auth/register` → user is `PENDING`.  
2. Approver calls `POST /users/approve/{id}` with `decision` + `role` (when approving).  
3. `POST /auth/login` → JWT `access_token` (`sub` = user id; `role` claim).  
4. Protected routes: `Authorization: Bearer <token>` header.  
5. `get_current_user` validates JWT and loads `User`; `get_current_approved_user` requires `APPROVED` + `is_active`.  
6. Logout on the client clears `localStorage`.

Interactive API docs: **`http://localhost:8000/docs`** (Swagger UI).

---

## Core data model

### `users`

Notable fields: `email` (unique), `hashed_password`, `patente`, `nome_guerra`, profile fields (`full_name`, `re`, `address`, `phone`, `birth_date`, `blood_type`), `display_order`, `is_active`, `role` (PG `userrole` ENUM), `status` (PG `userstatus` ENUM), `created_at`.

### `vehicles` / `vehicle_logs`

- **Vehicle**: unique `placa` and `prefixo`, `modelo`, `modalidade` (`FT` \| `ROCAM`), `status` (`OPERANDO` \| `BAIXADA` \| `MANUTENCAO` \| `RESERVA`), `baixada_at`, `retorno_operacao_at`, timestamps.  
- **Log**: `vehicle_id`, `user_id`, `action_type` (`CREATED`, `STATUS_CHANGED`, `RETURNED`, `UPDATED`), `description`, `motivo`, `old_status`, `new_status`, `created_at`.

Alembic migrations: `001_initial` (users + user ENUMs), `002_profile` (profile fields + order), `003_vehicles` (fleet ENUMs + tables).

---

## Roster module

- Route: `GET /users/efetivo` (approved, active).  
- Server ordering: rank hierarchy (`core/ranks.py` / `constants/ranks.ts`) + `display_order` + name.  
- **Reorder**: `PUT /users/efetivo/reorder` with body `{ patente, ordered_user_ids }` (`ADMIN` / `N90` / `TAT_CMD` only).  
- Frontend: `/efetivo`, cards by rank, **@dnd-kit** per group, drawer with record and permission-based edit.

---

## Vehicles module

- Page `/viaturas`: **FT** and **ROCAM** sections, status badges, create modal, status-change modal (reason required), drawer with timeline (`GET /vehicles/{id}/logs`).  
- API (prefix `/vehicles`): see **REST API** below.

---

## Operational logs

- Created in **services** when a vehicle is created, fields change (`UPDATED`), or status changes (`STATUS_CHANGED` / `RETURNED` when returning to operations from `BAIXADA` or `MANUTENCAO`).  
- Aggregated feed: `GET /vehicles/recent-logs?limit=…` (used on the dashboard).

---

## Operations dashboard

- Frontend route: `/dashboard`.  
- Besides static copy, shows **recent fleet events** with a subtle icon per event type.

---

## REST API (current)

### Auth — prefix `/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Signup (pending). |
| POST | `/auth/login` | Login (approved + active) → JWT. |

### Users — prefix `/users`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/users/me` | Approved, active. |
| GET | `/users/pending` | Approver. |
| GET | `/users/efetivo` | Approved, active. |
| PUT | `/users/efetivo/reorder` | Staff (`ADMIN` / `N90` / `TAT_CMD`). |
| POST | `/users/approve/{user_id}` | Approver. |
| GET | `/users/{user_id}` | Approved profile. |
| PATCH | `/users/{user_id}` | Rules in `user_service.update_user_profile`. |

### Vehicles — prefix `/vehicles`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/vehicles/recent-logs` | Approved, active. |
| GET | `/vehicles/` | List. |
| POST | `/vehicles/` | Fleet editor. |
| GET | `/vehicles/{vehicle_id}` | Detail. |
| PATCH | `/vehicles/{vehicle_id}` | Fleet editor. |
| PATCH | `/vehicles/{vehicle_id}/status` | Fleet editor (+ log). |
| GET | `/vehicles/{vehicle_id}/logs` | History. |

### Other

| Method | Path |
|--------|------|
| GET | `/health` |

---

## Running locally

### Prerequisites

- Python **3.12+**, **Node.js** 20+ (or 22 to match the frontend Dockerfile), **PostgreSQL** 16 (or Docker only).

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
# Create backend/.env from the repo root example (Settings uses env_file=".env" relative to backend CWD)
cp ../.env.example .env
# Edit backend/.env: SECRET_KEY, local DATABASE_URL, CORS_ORIGINS, etc.
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> `Settings` (`core/config.py`) uses `env_file=".env"`: when running `uvicorn` from **`backend/`**, expect **`backend/.env`**. **Docker Compose** still loads the **root `.env`** via `env_file`—keep them in sync or export variables in your shell.

### Frontend

```bash
cd frontend
npm install
# set API URL (dev)
set VITE_API_URL=http://localhost:8000   # Windows CMD
# export VITE_API_URL=http://localhost:8000  # Linux/macOS
npm run dev
```

Open **`http://localhost:5173`**. Ensure backend `CORS_ORIGINS` includes that origin.

---

## `.env` configuration

See **[`.env.example`](.env.example)** at the repository root. Backend variables (`pydantic-settings`):

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing secret (`secret_key` in code). |
| `DATABASE_URL` | PostgreSQL DSN (psycopg3). |
| `CORS_ORIGINS` | Comma-separated list. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Optional admin bootstrap. |
| `ADMIN_PATENTE` / `ADMIN_NOME_GUERRA` | Rank and war name for bootstrap admin. |

Optional defaults in `core/config.py`: `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

---

## Docker

From the **`docker/`** directory:

```bash
cd docker
docker compose up --build
```

Services:

| Service | Port | Notes |
|---------|------|-------|
| `db` | 5432 | Compose-fixed user/password/db: `pelotao` / `pelotao` / `pelotao`. |
| `backend` | 8000 | Injects `DATABASE_URL` to host `db`. Runs migrations on entrypoint. |
| `frontend` | 80 | Build uses compose `VITE_API_URL` (`http://localhost:8000`). |

Root `.env` is referenced by Compose `env_file` (`SECRET_KEY`, `CORS_ORIGINS`, admin bootstrap, etc.).

---

## Common commands

| Location | Command |
|----------|---------|
| Backend | `alembic revision --autogenerate -m "msg"` / `alembic upgrade head` |
| Backend | `uvicorn main:app --reload` |
| Frontend | `npm run dev` / `npm run build` |
| Docker | `docker compose up --build` (from `docker/`) |

---

## Roadmap (ideas)

- Automated tests (pytest + Vitest/Playwright).  
- Pagination and filters for roster and logs.  
- Exportable audit trail (CSV/PDF).  
- Real-time notifications (WebSocket) for the operations feed.  
- Password policy and 2FA for sensitive accounts.

---

## Planned technical improvements

- Commit **`package-lock.json`** consistently with the frontend Dockerfile.  
- CI (lint + test + build) on GitHub Actions or similar.  
- Document **`VITE_API_URL`** for staging/production domains.

---

## Security

- **bcrypt** passwords; **HS256** JWT; token validation on protected routes.  
- **Inactive** or **non-approved** accounts cannot use `get_current_approved_user` routes.  
- CORS limited to configured origins.  
- Do **not** commit real secrets in `.env` (use `.env.example`).  
- Production: HTTPS reverse proxy, rotate `SECRET_KEY`, Postgres backups, least privilege for roles.

---

## License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE).

---

## Author
Vinícius Pires
[E-mail](viinycampos19@hotmail.com)
[LinkedIN](https://www.linkedin.com/in/vin%C3%ADcius-pires-544a88241/)
**Pelotão System** — code and docs maintained in this repository.  


---

<div align="center">

<sub>English (en-US) documentation aligned with the current repository (FastAPI + React + PostgreSQL + Docker). Portuguese: [READMEptbr.md](READMEptbr.md).</sub>

</div>
