<div align="center">

# Pelotão System

**Web operations system for internal police platoon management**  
Tactical unit / ROCAM · roster · profiles · patrol vehicles · leaves & compensations · vacations & LP · service scales · logs

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

**Pelotão System** is an internal **full-stack** application: **JWT** authentication, signup with **command-level approval**, granular **RBAC**, an operations dashboard, **roster** with visual grouping and persisted **drag-and-drop** seniority, **role management** for staff, detailed **officer profiles**, a **patrol vehicle** module (FT and ROCAM) with automatic **operational history and logs**, operational **leaves & compensations**, **vacations & LP (Licença Prêmio)** with operational calendars and review rules, **service scales** (FT/ROCAM teams, publication, audit logs, WhatsApp-ready export), and a **dashboard** with fleet events, scale activity, and absence indicators (including **critical days** for command).

The UI uses a **dark** operational theme, a **responsive sidebar** (hamburger menu on mobile), and **Docker** packaging.

### Motivation

The project aims to **ease repetitive platoon workflows**, make them **more dynamic**, and give time back to the roster. The data model reflects **real operations** during shifts and how the platoon actually works.

This is not a commercial product: **AI-assisted development** (*vibe coding*) was used to move faster and review LLM-generated code, always with human oversight. Prompts follow a **fixed template**, changing only the goal of each task. **Cursor MCPs** supported the workflow—especially **Context7** for up-to-date documentation; the **Playwright** MCP was used to assist UI testing when it fit the task.

---

## Operational goals

Centralize, with traceability:

- who is on the roster, in what hierarchical order, and with which personnel data;
- vehicle state (in service, out of service, maintenance, reserve) and **who** changed **what** and **why**;
- monthly leave requests, compensation credits, vacations, and LP, with command approval and an auditable trail;
- daily **service scales** (FT and ROCAM teams, missions, vehicles/motorcycles, publication);
- access driven by the officer’s **application role** (do not confuse institutional **rank** with app **role**).

---

## Screenshots

[Login](docs/screenshots/login.png)  
[Dashboard](docs/screenshots/dashboard.png)  
[Roster](docs/screenshots/efetivo.png)  
[Vehicles](docs/screenshots/viaturas.png)  
[Profile](docs/screenshots/perfil.png)  
[Vacations & LP](docs/screenshots/ferias.png)  
[Service scale](docs/screenshots/escala-servico.png)  
[Scale export (WhatsApp)](docs/screenshots/escala-export.png)

> Placeholder paths for new captures — add PNGs under `docs/screenshots/` when available.

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
│   ├── alembic/              # env.py + versions (001…007)
│   ├── auth/                 # JWT, deps (approver, scale editor, vehicle editor, …)
│   ├── core/                 # config, ranks, leave booking policy, compensation labels
│   ├── database/             # Base, session
│   ├── models/               # User, Vehicle, Leave, Vacation, ServiceScale, …
│   ├── routes/               # auth, users, vehicles, leaves, compensations, vacations, service_scales
│   ├── schemas/              # Pydantic DTOs per domain
│   ├── services/             # domain services + scale_export_service.py
│   ├── main.py
│   ├── requirements.txt
│   └── docker-entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── components/       # efetivo, vehicle/, folgas/, vacations/, service-scales/ (export modal, DnD)
│   │   ├── constants/        # ranks.ts (visual groups)
│   │   ├── hooks/            # AuthContext
│   │   ├── layouts/          # OperationalLayout (sidebar)
│   │   ├── pages/            # Dashboard, Efetivo, Viaturas, Folgas, Férias, Escala, Perfil, Approvals
│   │   ├── services/         # api clients per module
│   │   └── types.ts + types/*.ts
│   ├── package.json
│   └── nginx.conf
├── docker/
├── docs/screenshots/
├── prompts/
├── .env.example
├── LICENSE
├── README.md
└── READMEptbr.md
```

---

## Implemented features

| Module | What exists today |
|--------|-------------------|
| Authentication | Signup (`PENDING`); login only for `APPROVED` + `is_active`; JWT HS256; configurable expiry. |
| Approvals | Pending list; approve with required **role** or reject (`ADMIN`, `N90`, `TAT_CMD`). |
| Admin bootstrap | Optional admin on startup via `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`, …). |
| Dashboard | Welcome; **3 latest vehicle logs**; **3 latest scale events**; command **away today** (leaves / vacations / LP split); critical-day alerts. |
| Layout | Sidebar: Dashboard, Roster, **Service scale**, Vehicles, Leaves, **Vacations**, Profile, **Approvals**. |
| Roster | Visual groups (Officers, NCOs, Enlisted, **Internship**); DnD seniority per rank; staff **role** editing; optimistic reorder. |
| Profile | Operational fields; edits per RBAC. |
| Vehicles | FT / ROCAM listing; create / edit status (with reason); per-vehicle log timeline; global feed. |
| Leaves & compensations | Monthly calendar; monthly or compensation-credit requests; automatic **REVIEW** when limits exceeded; approval hub. |
| Vacations & LP | Monthly calendar; **15- or 30-day** periods; max **2** simultaneous officers (Férias/LP); statuses + command review; roster availability flags. |
| Service scales | Monthly calendar; multiple teams/day; FT (vehicle + up to 4 officers) and ROCAM (up to 3 officers, **individual motorcycles**); draft/publish; audit logs; history; **operational export**. |
| Health | `GET /health` |

---

## RBAC (`UserRole`)

| Role | Main effect in the current codebase |
|------|-------------------------------------|
| **ADMIN** | Full access to approvals, roster (reorder + profiles + `is_active` + **role** of others), vehicles, **service scales** (N90-level). |
| **N90** | Same as approver / roster staff / vehicles / **scale editor** (`SCALE_EDITOR_ROLES`). |
| **TAT_CMD** | Approver; roster staff; vehicles; **view** published scales (no scale editing). |
| **BRACAL** | Own profile; vehicles CRUD; compensation events; leaves/vacations requests; **no** scale editing. |
| **ESTAGIO** | Own profile; read-only vehicles; leaves/vacations requests; shown in separate roster group; **no** scale editing. |

> Institutional **rank** (text field) ≠ application **role** (enum).

Backend dependencies:

- `require_approver` / `STAFF_EDITOR_ROLES` → signups, pending leaves/compensations/vacations, `PUT /users/efetivo/reorder`, broad profile edits (including **role** for others, not self).
- `require_scale_editor` (`SCALE_EDITOR_ROLES`: **ADMIN**, **N90**) → create/publish/edit/delete scales and teams.
- `require_vehicle_editor` → `POST/PATCH` on `/vehicles`.
- `require_compensation_creator` (excludes `ESTAGIO`) → `POST /compensations`.

---

## Authentication flow

1. `POST /auth/register` → user is `PENDING`.  
2. Approver calls `POST /users/approve/{id}` with `decision` + `role` (when approving).  
3. `POST /auth/login` → JWT `access_token` (`sub` = user id; `role` claim).  
4. Protected routes: `Authorization: Bearer <token>` header.  
5. `get_current_approved_user` requires `APPROVED` + `is_active`.  
6. Logout on the client clears `localStorage`.

Interactive API docs: **`http://localhost:8000/docs`** (Swagger UI).

---

## Core data model

### `users`

`email`, `patente`, `nome_guerra`, profile fields, `display_order`, `is_active`, `role` (`userrole`), `status` (`userstatus`), timestamps.

### `vehicles` / `vehicle_logs`

Fleet units (FT/ROCAM) and immutable-style operational logs per change.

### Leaves / compensations

`leave_requests`, `leave_approval_logs`, `compensation_events`, `user_compensations` — see existing migrations `004`, `005`.

### Vacations / LP

- **`vacation_requests`**: `vacation_type` (`FERIAS` \| `LP`), `start_date`, `end_date`, `total_days` (**15** or **30**), `status` (`PENDING` \| `REVIEW` \| `APPROVED` \| `REJECTED` \| `CANCELLED`), review/decision fields, `vacation_approval_logs` for audit.

### Service scales

- **`service_scales`**: one row per calendar day (`scale_date` unique), `title`, `status` (`DRAFT` \| `PUBLISHED`), `published_at`, `created_by_id`.
- **`scale_teams`**: `modality` (`FT` \| `ROCAM`), optional `vehicle_id` (**FT only**; **NULL for ROCAM**), `start_datetime`, `end_datetime`, `mission_name`, `notes`.
- **`scale_team_members`**: `user_id`, optional `assigned_vehicle_id` (**ROCAM motorcycle** per officer).
- **`scale_logs`**: audit trail (`TEAM_ADDED`, `PUBLISHED`, `MEMBERS_CHANGED`, …).

Alembic: `006_vacations.py`, `007_service_scales.py` (after `001`–`005`).

---

## Roster module

- Route: `GET /users/efetivo` (approved users).
- Server ordering: rank hierarchy + `display_order` + name.
- **Visual grouping** (frontend only): Officers · SubTen/Sergeants · Corporals/Soldiers · **Internship** (`role === ESTAGIO`).
- **Reorder**: `PUT /users/efetivo/reorder` with `{ patente, ordered_user_ids }` (staff only); optimistic UI without full-page reload.
- **Role editing**: `PATCH /users/{id}` with `role` (staff; not on self).
- Frontend: `/efetivo`, **@dnd-kit**, operational drawer.

---

## Vacations & LP module

- **Calendar** (`GET /vacations/calendar`): month view; entries for **Férias** and **LP**; command summary (pending count, **away today**, critical days when **≥2** simultaneous Férias/LP on a day).
- **Request** (`POST /vacations/request`): periods of **15 or 30** consecutive days; operational rule: max **2** officers on Férias/LP at once per day → may enter **`REVIEW`** with `review_reason`.
- **Statuses**: `PENDING`, `REVIEW`, `APPROVED`, `REJECTED`, `CANCELLED`.
- **Command**: `PATCH /vacations/{id}/approve|reject`; officer `PATCH /vacations/{id}/cancel` on own pending/review.
- **Roster integration**: calendar/roster views flag officers with active leave/vacation on a date.
- Frontend: `/ferias` (calendar + request modal); approvals tab for pending vacations.

---

## Service scales module

### Operational calendar

- Route: `/escala-servico` — monthly calendar (`GET /service-scales/calendar`).
- Day drawer: create scale (draft), add/edit/remove teams, publish, delete scale, **export** (when published).

### Team structure

| Modality | Vehicle | Personnel | Notes |
|----------|---------|-----------|--------|
| **FT** | One **main patrol vehicle** (required, `OPERANDO`, FT) | Up to **4** officers | Mission presets (Tático Comando, Supervisor Tático, Força Tática) or custom |
| **ROCAM** | **No team vehicle** (`vehicle_id = NULL`) | Up to **3** officers | Each officer has an **individual ROCAM motorcycle** (`assigned_vehicle_id`, required) |

### Rules enforced (frontend + backend)

- **Unique FT vehicle** per published scale (no duplicate patrol car across teams).
- **Unique ROCAM motorcycle** per scale (no duplicate bike across members).
- **Unique officer** per scale (cannot appear in two teams the same day).
- Real-time filtering of unavailable vehicles, motorcycles, and roster when building teams.
- **Edit team** without remove/recreate: patch team metadata and members in place.

### Publication & audit

- Draft scales visible only to **scale editors** (`ADMIN` / `N90`).
- `POST /service-scales/{id}/publish` — requires at least one team; sets `PUBLISHED` + `published_at`.
- Every change appends to **`scale_logs`** (actor, action, description).

### Automatic absence cancellation

When an officer is added to a scale on date **D**, active **leaves** and **vacations/LP** covering **D** for that officer are **automatically cancelled** (with audit reason), preserving operational flexibility.

### Operational export (WhatsApp-ready)

- Available only for **`PUBLISHED`** scales.
- `GET /service-scales/{id}/export` → `{ "text": "…" }` (plain text, line breaks preserved).
- Formatter in **`services/scale_export_service.py`** (decoupled for future WhatsApp/IA integration).
- Frontend: **Export** button → modal with preview + **Copy** + “Copied” feedback.

Example export (abbreviated):

```text
💀 ESCALA DE SERVIÇO 💀
1° PELOTÃO DE FORÇA TÁTICA

Dia 07 de Março de 2026
Qtr: 12:45hs

I-03027
Ten Carvalho
Sd Martins

ROCAM 1
Cb Broisler -> Moto I-03066-11
Sd Bispo -> Moto I-03067-11

Folga do mês:
Sd De Paula

Férias:
Cb Araújo

LP:
Sd Custódio
```

Non-default shift hours (outside 06:00–18:00 on scale day) show mission name + time range before the team block.

---

## Vehicles module

- Page `/viaturas`: FT and ROCAM sections, status workflow, logs, feed.

---

## Operational logs

| Domain | Mechanism |
|--------|-----------|
| Vehicles | `vehicle_logs` + `GET /vehicles/recent-logs` |
| Leaves | `leave_approval_logs` |
| Vacations | `vacation_approval_logs` |
| Service scales | `scale_logs` + `GET /service-scales/recent-events` |

---

## Leaves & compensations module

- **Calendar** (`GET /leaves/calendar`): monthly leave view; **≥4** officers out on a day → **critical** (dashboard).
- **Requests**, **compensations**, **approvals** — unchanged core behavior; see prior README sections.
- Frontend: `/folgas`, `/admin/pending-users`.

---

## Operations dashboard

- Route: `/dashboard`.
- **Service scales**: last **3** operational events; quick **export** icon per event (opens export modal when scale is published).
- **Vehicles**: last **3** fleet log entries.
- **Command — away today**: separate lists for **Leaves**, **Férias**, and **LP** (approved, current date).
- Critical-day banners for leaves (≥4) and vacations/LP (≥2).

---

## REST API (current)

### Auth — `/auth`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Signup (pending). |
| POST | `/auth/login` | Login → JWT. |

### Users — `/users`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/users/me` | Approved, active. |
| GET | `/users/pending` | Approver. |
| GET | `/users/efetivo` | Approved roster. |
| PUT | `/users/efetivo/reorder` | Staff. |
| POST | `/users/approve/{user_id}` | Approver. |
| GET | `/users/{user_id}` | Profile. |
| PATCH | `/users/{user_id}` | Profile + **role** (staff rules). |

### Vehicles — `/vehicles`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/vehicles/recent-logs` | Feed (`limit`). |
| GET/POST/PATCH | `/vehicles/…` | Fleet editors. |
| GET | `/vehicles/{id}/logs` | Timeline. |

### Leaves — `/leaves`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/leaves/calendar` | Month view. |
| GET | `/leaves/pending` | Approver. |
| POST | `/leaves/request` | Create request. |
| PATCH | `/leaves/{id}/approve\|reject\|cancel` | Workflow. |

### Compensations — `/compensations`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/compensations/pending` | Approver. |
| GET | `/compensations/available` | Own credits. |
| POST | `/compensations/` | Creator (not `ESTAGIO`). |
| PATCH | `/compensations/{id}/approve\|reject` | Approver. |

### Vacations — `/vacations`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/vacations/calendar` | Month view (`year`, `month`). |
| GET | `/vacations/pending` | Approver. |
| POST | `/vacations/request` | 15- or 30-day period. |
| PATCH | `/vacations/{id}/approve` | Approver. |
| PATCH | `/vacations/{id}/reject` | Approver. |
| PATCH | `/vacations/{id}/cancel` | Owner (pending/review). |

### Service scales — `/service-scales`

| Method | Path | Auth / notes |
|--------|------|----------------|
| GET | `/service-scales/calendar` | Month calendar. |
| GET | `/service-scales/{date}` | Day detail (scale, roster, vehicles). |
| GET | `/service-scales/history` | Paginated history. |
| GET | `/service-scales/recent-events` | Audit feed. |
| GET | `/service-scales/presets/missions` | FT / ROCAM mission presets. |
| POST | `/service-scales/` | Scale editor — create scale. |
| PATCH | `/service-scales/{id}` | Scale editor — metadata. |
| POST | `/service-scales/{id}/publish` | Scale editor. |
| POST | `/service-scales/{id}/teams` | Scale editor — add team. |
| PATCH | `/service-scales/team/{id}` | Scale editor — edit team (+ optional `members`). |
| PATCH | `/service-scales/team/{id}/members` | Scale editor — replace members. |
| PATCH | `/service-scales/team/{id}/remove` | Scale editor — remove team. |
| DELETE | `/service-scales/{id}` | Scale editor — delete scale. |
| GET | `/service-scales/{id}/export` | **Published only** → `{ "text": "…" }`. |

### Other

| Method | Path |
|--------|------|
| GET | `/health` |

---

## Running locally

### Prerequisites

- Python **3.12+**, **Node.js** 20+ (or 22), **PostgreSQL** 16 (or Docker only).

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> Run `uvicorn` from **`backend/`** with **`backend/.env`**. Docker Compose uses root **`.env`** — keep them aligned.

### Frontend

```bash
cd frontend
npm install
export VITE_API_URL=http://localhost:8000
npm run dev
```

Open **`http://localhost:5173`**. Ensure `CORS_ORIGINS` includes that origin.

---

## `.env` configuration

See **[`.env.example`](.env.example)**. Key variables: `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_PATENTE`, `ADMIN_NOME_GUERRA`.

---

## Docker

```bash
cd docker
docker compose up --build
```

| Service | Port |
|---------|------|
| `db` | 5432 |
| `backend` | 8000 |
| `frontend` | 80 |

---

## Common commands

| Location | Command |
|----------|---------|
| Backend | `alembic upgrade head` / `uvicorn main:app --reload` |
| Frontend | `npm run dev` / `npm run build` |
| Docker | `docker compose up --build` |

---

## Roadmap (ideas)

- Automated tests (pytest + Vitest/Playwright).  
- **WhatsApp / IA**: send export text via bot using `scale_export_service`.  
- PDF export of published scales.  
- Real-time notifications (WebSocket) for approval queues.  
- Password policy and 2FA.

---

## Planned technical improvements

- Commit **`package-lock.json`** consistently.  
- CI (lint + test + build).  
- Staging/production **`VITE_API_URL`** documentation.

---

## Security

- **bcrypt** + **JWT**; RBAC per route.  
- Scale export and draft scales respect role and publication state.  
- Do **not** commit secrets in `.env`.  
- Production: HTTPS, rotate `SECRET_KEY`, Postgres backups.

---

## License

**MIT License** — see [`LICENSE`](LICENSE).

---

## Author

Vinícius Pires · [E-mail](viinycampos19@hotmail.com) · [LinkedIn](https://www.linkedin.com/in/vin%C3%ADcius-pires-544a88241/)

---

<div align="center">

<sub>English (en-US) documentation aligned with the current repository. Portuguese: [READMEptbr.md](READMEptbr.md).</sub>

</div>
