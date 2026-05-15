<div align="center">

# Pelotão System

**Sistema operacional web para gestão interna de pelotão policial**  
Força Tática / ROCAM · efetivo · perfis · viaturas · folgas e compensações · logs

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docs.docker.com/compose/)
[![Tailwind](https://img.shields.io/badge/Tailwind-4-06B6D4?style=flat-square&logo=tailwindcss)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**[English version (en-US) →](README.md)**

</div>

---

## Descrição

O **Pelotão System** é uma aplicação **full-stack** pensada para uso interno: autenticação **JWT**, cadastro com **aprovação por perfil de comando**, **RBAC** granular, painel operacional, **efetivo** com ordenação por patente e **drag-and-drop** de antiguidade (persistido), **perfis policiais** detalhados, módulo de **viaturas** (FT e ROCAM) com **histórico e logs operacionais** automáticos, módulo operacional de **folgas e compensações** (calendário mensal, solicitações, fila de review, créditos de compensação) e **dashboard** com feed de frota e indicadores de folga — inclusive **dias críticos** para o comando.

Interface em **tema escuro** (operacional), **sidebar responsiva** (menu hamburger no mobile) e empacotamento via **Docker**.

### Motivação

O projeto busca **aliviar rotinas exaustivas** do pelotão, tornando-as **mais dinâmicas** e devolvendo tempo ao efetivo. A modelagem reflete a **realidade operacional** vivida durante os turnos e a dinâmica do pelotão.

Sem fins comerciais, usei **desenvolvimento assistido por IA** (*vibe coding*) para acelerar entregas e inspecionar a qualidade do código gerado, sempre com revisão humana. Os prompts seguem **uma estrutura fixa**, variando apenas o objetivo de cada tarefa; no Cursor, as **MCPs** apoiaram o fluxo — em especial o **Context7** para documentação atualizada; o **Playwright** (MCP) foi utilizado como apoio a testes de interface quando coube no escopo da tarefa.

---

## Objetivo operacional

Centralizar, com rastreabilidade:

- quem está no efetivo, em que ordem hierárquica e com quais dados cadastrais;
- estado das viaturas (operando, baixada, manutenção, reserva) e **quem** alterou **o quê** e **por quê**;
- folgas mensais e compensações, com aprovação do comando e trilha de auditoria;
- acesso condicionado ao **papel** do policial no sistema (não confundir **patente** institucional com **role** de aplicação).

---

## Screenshots

[Login](docs/screenshots/login.png)
[Dashboard](docs/screenshots/dashboard.png)
[Efetivo](docs/screenshots/efetivo.png)
[Viaturas](docs/screenshots/viaturas.png)
[Perfil](docs/screenshots/perfil.png)

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| API | **FastAPI** 0.115, **Uvicorn**, **Pydantic** v2 |
| ORM / DB | **SQLAlchemy** 2.0, **Alembic**, **PostgreSQL** 16, **psycopg** 3 |
| Auth | **JWT** (`python-jose`), senhas **bcrypt** |
| Frontend | **React** 19, **TypeScript**, **Vite** 6, **react-router-dom** 7 |
| UI | **Tailwind CSS** 4 (`@tailwindcss/vite`), **Lucide** ícones |
| DnD | **@dnd-kit** (core, sortable, utilities) |
| Deploy local | **Docker Compose** (Postgres + API + Nginx estático) |

---

## Arquitetura

```
┌─────────────┐     HTTPS/HTTP      ┌──────────────┐
│   Browser   │ ◄──────────────────► │  Nginx :80   │  (build Vite estático)
└──────┬──────┘                      └──────┬───────┘
       │                                    │
       │  VITE_API_URL (build)              │  proxy implícito: browser → API
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

- **SPA** consome a API REST; token JWT armazenado em `localStorage` (`Authorization: Bearer`).
- **Backend** valida JWT, aplica dependências de RBAC por rota e persiste com SQLAlchemy.
- **Migrations Alembic** versionam o schema (incluindo ENUMs nativos PostgreSQL sem duplicar `CREATE TYPE` nas migrations existentes).
- **Subida do container backend**: `alembic upgrade head` no entrypoint antes do Uvicorn.

---

## Estrutura de pastas (resumo)

```text
pelotao-system/
├── backend/
│   ├── alembic/              # env.py + versions (001…005)
│   ├── auth/                 # JWT, deps, senha
│   ├── core/                 # config, ranks, janela de folgas, rótulos de compensação
│   ├── database/             # Base, session
│   ├── models/               # User, Vehicle, VehicleLog, LeaveRequest, CompensationEvent, …
│   ├── routes/               # auth, users, vehicles, leaves, compensations
│   ├── schemas/              # Pydantic (users, vehicles, leaves, compensations)
│   ├── services/             # user, vehicle, leave, compensation services
│   ├── main.py
│   ├── requirements.txt
│   └── docker-entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── components/       # ProtectedRoute, SortablePoliceRow, vehicle/, folgas/…
│   │   ├── constants/        # ranks.ts
│   │   ├── hooks/            # AuthContext
│   │   ├── layouts/          # OperationalLayout (sidebar)
│   │   ├── pages/            # Login, Register, Dashboard, Efetivo, Viaturas, Folgas, Perfil, PendingUsers
│   │   ├── services/         # api, authApi, usersApi, vehiclesApi, leavesApi, compensationsApi
│   │   └── types.ts + types/vehicle.ts + types/leaves.ts
│   ├── package.json
│   └── nginx.conf            # usado no estágio nginx do Dockerfile
├── docker/
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docs/screenshots/         # placeholders de capturas
├── prompts/                  # rascunhos de prompts (não usado em runtime)
├── .env.example
├── LICENSE
├── README.md              # documentação em inglês (en-US)
└── READMEptbr.md          # esta versão em português
```

---

## Funcionalidades implementadas

| Módulo | O que existe hoje |
|--------|-------------------|
| Autenticação | Registro (`PENDING`), login só para `APPROVED` + `is_active`; JWT HS256; expiração configurável (`access_token_expire_minutes`, padrão 24h). |
| Aprovação | Lista de pendentes, aprovar com **role** obrigatório ou rejeitar (`ADMIN`, `N90`, `TAT_CMD`). |
| Bootstrap admin | Se `ADMIN_EMAIL` e `ADMIN_PASSWORD` estiverem definidos no `.env`, cria admin na subida (se e-mail não existir). |
| Dashboard | Boas-vindas + **últimos logs de viaturas** (`GET /vehicles/recent-logs`). |
| Layout | Sidebar com Dashboard, Efetivo, Viaturas, **Folgas**, Perfil + **Aprovações** (comando e quem registra compensação). |
| Efetivo | Lista aprovados, agrupados por patente; **DnD** por patente (comando); `display_order` persistido. |
| Perfil | Dados operacionais (nome completo, RE, endereço, etc.); edição conforme RBAC. |
| Viaturas | Listagem **FT** / **ROCAM**; criar/editar status (com motivo); timeline de logs por viatura; feed global. |
| Folgas e compensações | **Calendário operacional** mensal (`/folgas`); solicitação de folga mensal ou por crédito; status **REVIEW** automático ao estourar limites; hub **Aprovações** (cadastros, folgas pendentes, compensações pendentes); registro e consumo de créditos. |
| Saúde | `GET /health` |

---

## RBAC (papéis `UserRole`)

| Role | Efeito principal no código atual |
|------|----------------------------------|
| **ADMIN** | Acesso total às operações de aprovação, efetivo (reorder + perfis + `is_active`), viaturas (CRUD + status). |
| **N90** | Idem aprovador / staff de efetivo / viaturas. |
| **TAT_CMD** | Idem. |
| **BRACAL** | Edita **próprio** perfil; **não** altera `is_active`; pode **criar/alterar viaturas** e status; pode **registrar eventos de compensação** (ficam pendentes até o comando); **não** reordena efetivo nem aprova cadastros/folgas/compensações. |
| **ESTAGIO** | Edita **próprio** perfil; **somente leitura** em viaturas; pode **solicitar folgas**; **não** registra compensações; **não** reordena efetivo. |

> **Patente** (campo textual do policial) ≠ **role** (enum de aplicação).

Dependências principais no backend:

- `require_approver` / `STAFF_EDITOR_ROLES` → cadastros, folgas/compensações pendentes, `PUT /users/efetivo/reorder`, edição ampla de perfil.
- `require_vehicle_editor` (`VEHICLE_EDITOR_ROLES`) → `POST/PATCH` em `/vehicles`.
- `require_compensation_creator` (`COMPENSATION_CREATOR_ROLES`, exceto `ESTAGIO`) → `POST /compensations`.

---

## Fluxo de autenticação

1. `POST /auth/register` → usuário `PENDING`.  
2. Aprovador `POST /users/approve/{id}` com `decision` + `role` (se aprovar).  
3. `POST /auth/login` → `access_token` JWT (`sub` = id do usuário; claim `role`).  
4. Rotas protegidas: header `Authorization: Bearer <token>`.  
5. `get_current_user` → valida JWT e carrega `User`; `get_current_approved_user` exige `APPROVED` + `is_active`.  
6. Logout no front remove token do `localStorage`.

Documentação interativa da API: **`http://localhost:8000/docs`** (Swagger UI).

---

## Modelagem principal

### `users`

Campos relevantes: `email` (único), `hashed_password`, `patente`, `nome_guerra`, dados de perfil (`full_name`, `re`, `address`, `phone`, `birth_date`, `blood_type`), `display_order`, `is_active`, `role` (`userrole` ENUM PG), `status` (`userstatus` ENUM PG), `created_at`.

### `vehicles` / `vehicle_logs`

- **Viatura**: `placa` e `prefixo` **únicos**, `modelo`, `modalidade` (`FT` \| `ROCAM`), `status` (`OPERANDO` \| `BAIXADA` \| `MANUTENCAO` \| `RESERVA`), `baixada_at`, `retorno_operacao_at`, timestamps.  
- **Log**: `vehicle_id`, `user_id`, `action_type` (`CREATED`, `STATUS_CHANGED`, `RETURNED`, `UPDATED`), `description`, `motivo`, `old_status`, `new_status`, `created_at`.

Migrations Alembic: `001_initial` (users + ENUMs usuário), `002_profile` (campos de perfil + ordem), `003_vehicles` (ENUMs frota + tabelas), `004_leaves_compensations`, `005_user_compensation_display_label`.

### Folgas / compensações

- **`leave_requests`**: `leave_on`, `leave_type` (`MONTHLY` \| `COMPENSATION`), `user_compensation_id` opcional, `status` (`PENDING` \| `REVIEW` \| `APPROVED` \| `REJECTED` \| `CANCELLED`), `review_reason`, campos de decisão, timestamps.  
- **`leave_approval_logs`**: auditoria por solicitação (`action`, `from_status` / `to_status`, `motivo`, `details`, `actor_id`).  
- **`compensation_events`** + **`compensation_event_participants`**: evento operacional (`CPJ_SUPPORT`, `WEAPON_OCCURRENCE`, etc.) com `PENDING` / `APPROVED` / `REJECTED`.  
- **`user_compensations`**: crédito por policial (`AVAILABLE` \| `USED`), `display_label`, vínculo ao evento e à folga que consumiu o crédito.

---

## Módulo de efetivo

- Rota: `GET /users/efetivo` (aprovado ativo).  
- Ordenação servidor: hierarquia de patentes (`core/ranks.py` / `constants/ranks.ts`) + `display_order` + nome.  
- **Reordenação**: `PUT /users/efetivo/reorder` com corpo `{ patente, ordered_user_ids }` (somente `ADMIN`/`N90`/`TAT_CMD`).  
- Front: `/efetivo`, cards por patente, **@dnd-kit** por grupo, drawer com ficha e edição conforme permissão.

---

## Módulo de viaturas

- Página `/viaturas`: seções **FT** e **ROCAM**, badges de status, modal de cadastro, modal de mudança de status (motivo obrigatório), drawer com timeline (`GET /vehicles/{id}/logs`).  
- API (prefixo `/vehicles`): ver tabela na seção **API REST** abaixo.

---

## Logs operacionais

- **Viaturas**: gerados no **service** ao criar/alterar viatura ou status; feed em `GET /vehicles/recent-logs?limit=…`.  
- **Folgas**: cada criação/aprovação/indeferimento/cancelamento grava em `leave_approval_logs` (ator, transição de status, motivo).

---

## Módulo de folgas e compensações

- **Calendário** (`GET /leaves/calendar`): visão mensal; entradas ordenadas por prioridade operacional — **folga mensal antes de folga por compensação**, depois `display_order` do efetivo, depois `nome_guerra`. Dias com **≥4** solicitações ativas são **críticos** (resumo no dashboard para o comando).  
- **Solicitação** (`POST /leaves/request`): folga mensal ou folga vinculada a crédito **AVAILABLE**; janela em `core/leave_booking_policy.py` (mês corrente; mês seguinte liberado a partir do dia **25**).  
- **Review operacional**: acima de **2** folgas/mês por policial ou **>4** policiais no mesmo dia → status **`REVIEW`** com `review_reason` (comando decide aprovar ou indeferir).  
- **Compensações**: `POST /compensations` registra evento com participantes; na aprovação, gera créditos; crédito é consumido ao agendar folga `COMPENSATION`.  
- **Aprovações**: comando (`ADMIN` / `N90` / `TAT_CMD`) — `PATCH /leaves/{id}/approve|reject`, `PATCH /compensations/{id}/approve|reject`; policial cancela a própria solicitação pendente/review com `PATCH /leaves/{id}/cancel`.  
- Front: `/folgas` (calendário + modal); `/admin/pending-users` com abas *Cadastros*, *Folgas pendentes*, *Compensações pendentes*.

---

## Dashboard operacional

- Rota front: `/dashboard`.  
- **Frota**: últimos registros com ícone por tipo de evento.  
- **Folgas**: cards de pendências do policial; para o comando — filas de folgas/compensações e alerta de **dias com efetivo crítico** (≥4 policiais de folga no mês).

---

## API REST (estado atual)

### Auth — prefixo `/auth`

| Método | Caminho | Descrição |
|--------|---------|-----------|
| POST | `/auth/register` | Cadastro (pendente). |
| POST | `/auth/login` | Login (aprovado + ativo) → JWT. |

### Users — prefixo `/users`

| Método | Caminho | Auth / nota |
|--------|---------|---------------|
| GET | `/users/me` | Aprovado ativo. |
| GET | `/users/pending` | Aprovador. |
| GET | `/users/efetivo` | Aprovado ativo. |
| PUT | `/users/efetivo/reorder` | Staff (`ADMIN`/`N90`/`TAT_CMD`). |
| POST | `/users/approve/{user_id}` | Aprovador. |
| GET | `/users/{user_id}` | Perfil aprovado. |
| PATCH | `/users/{user_id}` | Regras em `user_service.update_user_profile`. |

### Vehicles — prefixo `/vehicles`

| Método | Caminho | Auth / nota |
|--------|---------|---------------|
| GET | `/vehicles/recent-logs` | Aprovado ativo. |
| GET | `/vehicles/` | Lista. |
| POST | `/vehicles/` | Editor de frota. |
| GET | `/vehicles/{vehicle_id}` | Detalhe. |
| PATCH | `/vehicles/{vehicle_id}` | Editor de frota. |
| PATCH | `/vehicles/{vehicle_id}/status` | Editor de frota (+ log). |
| GET | `/vehicles/{vehicle_id}/logs` | Histórico. |

### Folgas — prefixo `/leaves`

| Método | Caminho | Auth / nota |
|--------|---------|---------------|
| GET | `/leaves/calendar` | Aprovado ativo (`year`, `month` query). |
| GET | `/leaves/pending` | Aprovador. |
| POST | `/leaves/request` | Aprovado ativo. |
| PATCH | `/leaves/{leave_id}/approve` | Aprovador. |
| PATCH | `/leaves/{leave_id}/reject` | Aprovador. |
| PATCH | `/leaves/{leave_id}/cancel` | Dono (pendente/review). |

### Compensações — prefixo `/compensations`

| Método | Caminho | Auth / nota |
|--------|---------|---------------|
| GET | `/compensations/pending` | Aprovador. |
| GET | `/compensations/available` | Aprovado ativo (créditos próprios). |
| POST | `/compensations/` | Criador de compensação (não `ESTAGIO`). |
| PATCH | `/compensations/{event_id}/approve` | Aprovador. |
| PATCH | `/compensations/{event_id}/reject` | Aprovador. |

### Outros

| Método | Caminho |
|--------|---------|
| GET | `/health` |

---

## Como rodar localmente

### Pré-requisitos

- Python **3.12+**, **Node.js** 20+ (ou 22 para alinhar ao Dockerfile do front), **PostgreSQL** 16 (ou só Docker).

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
# Crie backend/.env a partir do exemplo na raiz (o Settings usa env_file=".env" relativo ao CWD do backend)
cp ../.env.example .env
# Edite backend/.env com SECRET_KEY, DATABASE_URL local, CORS_ORIGINS, etc.
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

> O `Settings` (`core/config.py`) referencia `env_file=".env"`: ao rodar `uvicorn` a partir de **`backend/`**, o arquivo esperado é **`backend/.env`**. O **Docker Compose** continua usando o **`.env` na raiz** via `env_file` — mantenha os dois alinhados ou use apenas variáveis de ambiente exportadas no shell.

### Frontend

```bash
cd frontend
npm install
# defina a URL da API (dev)
set VITE_API_URL=http://localhost:8000   # Windows CMD
# export VITE_API_URL=http://localhost:8000  # Linux/macOS
npm run dev
```

Abra **`http://localhost:5173`**. Garanta que `CORS_ORIGINS` no backend inclua essa origem.

---

## Configuração `.env`

Veja **[`.env.example`](.env.example)** na raiz. Variáveis usadas pelo backend (`pydantic-settings`):

| Variável | Função |
|----------|--------|
| `SECRET_KEY` | Segredo JWT (campo `secret_key` no código). |
| `DATABASE_URL` | DSN PostgreSQL + psycopg3. |
| `CORS_ORIGINS` | Lista separada por vírgula. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Bootstrap opcional do admin. |
| `ADMIN_PATENTE` / `ADMIN_NOME_GUERRA` | Patente e nome de guerra do admin bootstrap. |

Opcionais com default em `core/config.py`: `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

---

## Docker

Na pasta **`docker/`**:

```bash
cd docker
docker compose up --build
```

Serviços:

| Serviço | Porta | Observação |
|---------|-------|------------|
| `db` | 5432 | Usuário/senha/db fixos no compose: `pelotao` / `pelotao` / `pelotao`. |
| `backend` | 8000 | `DATABASE_URL` injetada para o host `db`. Roda migrations no entrypoint. |
| `frontend` | 80 | Build com `VITE_API_URL` definido no compose (`http://localhost:8000`). |

`.env` na raiz é referenciado pelo `env_file` do Compose (variáveis como `SECRET_KEY`, `CORS_ORIGINS`, bootstrap admin).

---

## Comandos principais

| Onde | Comando |
|------|---------|
| Backend | `alembic revision --autogenerate -m "msg"` / `alembic upgrade head` |
| Backend | `uvicorn main:app --reload` |
| Frontend | `npm run dev` / `npm run build` |
| Docker | `docker compose up --build` (pasta `docker/`) |

---

## Roadmap futuro (sugestões)

- Testes automatizados (pytest + Vitest/Playwright).  
- Paginação e filtros em efetivo, logs de frota e calendário de folgas.  
- Auditoria exportável (CSV/PDF) — logs de aprovação de folgas já persistidos no banco.  
- Notificações em tempo real (WebSocket) para filas de frota, folgas e compensações.  
- Política de senha e 2FA para contas sensíveis.

---

## Melhorias planejadas (técnicas)

- `package-lock.json` versionado de forma consistente com o Dockerfile do frontend.  
- CI (lint + test + build) em GitHub Actions ou similar.  
- `VITE_API_URL` documentada também para ambientes staging/produção por domínio.

---

## Segurança

- Senhas com **bcrypt**; JWT assinado com **HS256**; validação de token em cada rota protegida.  
- Contas **inativas** ou **não aprovadas** não acessam rotas sob `get_current_approved_user`.  
- CORS restrito às origens configuradas.  
- **Não** commite `.env` com segredos reais (use `.env.example`).  
- Em produção: HTTPS reverso, rotação de `SECRET_KEY`, backups do Postgres e princípio do menor privilégio para roles.

---

## Licença

Este projeto está licenciado sob a **MIT License** — veja o arquivo [`LICENSE`](LICENSE).

---

## Autor
Vinícius Pires
[E-mail](viinycampos19@hotmail.com)
[LinkedIN](https://www.linkedin.com/in/vin%C3%ADcius-pires-544a88241/)
**Pelotão System** — código e documentação mantidos no repositório.  

---

<div align="center">

<sub>Documentação em português (pt-BR), alinhada ao estado atual do repositório (FastAPI + React + PostgreSQL + Docker). Versão em inglês: [README.md](README.md).</sub>

</div>
