<div align="center">

# Pelotão System

**Sistema operacional web para gestão interna de pelotão policial**  
Força Tática / ROCAM · efetivo · perfis · viaturas · logs

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

O **Pelotão System** é uma aplicação **full-stack** pensada para uso interno: autenticação **JWT**, cadastro com **aprovação por perfil de comando**, **RBAC** granular, painel operacional, **efetivo** com ordenação por patente e **drag-and-drop** de antiguidade (persistido), **perfis policiais** detalhados, módulo de **viaturas** (FT e ROCAM) com **histórico e logs operacionais** automáticos, e **dashboard** com feed dos últimos eventos de frota.

Interface em **tema escuro** (operacional), **sidebar responsiva** (menu hamburger no mobile) e empacotamento via **Docker**.

### Motivação

O projeto busca **aliviar rotinas exaustivas** do pelotão, tornando-as **mais dinâmicas** e devolvendo tempo ao efetivo. A modelagem reflete a **realidade operacional** vivida durante os turnos e a dinâmica do pelotão.

Sem fins comerciais, usei **desenvolvimento assistido por IA** (*vibe coding*) para acelerar entregas e inspecionar a qualidade do código gerado, sempre com revisão humana. Os prompts seguem **uma estrutura fixa**, variando apenas o objetivo de cada tarefa; no Cursor, as **MCPs** apoiaram o fluxo — em especial o **Context7** para documentação atualizada; o **Playwright** (MCP) foi utilizado como apoio a testes de interface quando coube no escopo da tarefa.

---

## Objetivo operacional

Centralizar, com rastreabilidade:

- quem está no efetivo, em que ordem hierárquica e com quais dados cadastrais;
- estado das viaturas (operando, baixada, manutenção, reserva) e **quem** alterou **o quê** e **por quê**;
- acesso condicionado ao **papel** do policial no sistema (não confundir **patente** institucional com **role** de aplicação).

---

## Screenshots

[Login](docs/screenshots/login.png)
[Dashboard](docs/screenshots/dashboard.png)` |
[Efetivo] |(docs/screenshots/efetivo.png) |
[Viaturas](docs/screenshots/viaturas.png) |
[Perfil](docs/screenshots/perfil.png) |

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
│   ├── alembic/              # env.py + versions (001…003)
│   ├── auth/                 # JWT, deps, senha
│   ├── core/                 # config, ranks (ordem de patentes)
│   ├── database/             # Base, session
│   ├── models/               # User, Vehicle, VehicleLog
│   ├── routes/               # auth, users, vehicles
│   ├── schemas/              # Pydantic
│   ├── services/             # regras de negócio
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
| Layout | Sidebar com Dashboard, Efetivo, Viaturas, Perfil + **Aprovações** (só aprovadores). |
| Efetivo | Lista aprovados, agrupados por patente; **DnD** por patente (comando); `display_order` persistido. |
| Perfil | Dados operacionais (nome completo, RE, endereço, etc.); edição conforme RBAC. |
| Viaturas | Listagem **FT** / **ROCAM**; criar/editar status (com motivo); timeline de logs por viatura; feed global. |
| Saúde | `GET /health` |

---

## RBAC (papéis `UserRole`)

| Role | Efeito principal no código atual |
|------|----------------------------------|
| **ADMIN** | Acesso total às operações de aprovação, efetivo (reorder + perfis + `is_active`), viaturas (CRUD + status). |
| **N90** | Idem aprovador / staff de efetivo / viaturas. |
| **TAT_CMD** | Idem. |
| **BRACAL** | Edita **próprio** perfil; **não** altera `is_active`; pode **criar/alterar viaturas** e status; **não** reordena efetivo nem aprova cadastros. |
| **ESTAGIO** | Edita **próprio** perfil; **somente leitura** em viaturas (sem criar/alterar status); **não** reordena efetivo. |

> **Patente** (campo textual do policial) ≠ **role** (enum de aplicação).

Dependências principais no backend:

- `require_approver` / `STAFF_EDITOR_ROLES` → aprovações + `PUT /users/efetivo/reorder` + edição ampla de perfil.
- `require_vehicle_editor` (`VEHICLE_EDITOR_ROLES`) → `POST/PATCH` em `/vehicles`.

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

Migrations Alembic: `001_initial` (users + ENUMs usuário), `002_profile` (campos de perfil + ordem), `003_vehicles` (ENUMs frota + tabelas).

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

- Gerados no **service** ao criar viatura, alterar dados (`UPDATED`) ou status (`STATUS_CHANGED` / `RETURNED` quando retorno operacional a partir de `BAIXADA` ou `MANUTENCAO`).  
- Feed agregado: `GET /vehicles/recent-logs?limit=…` (usado no dashboard).

---

## Dashboard operacional

- Rota front: `/dashboard`.  
- Além do texto institucional, lista **últimos registros** de frota com ícone discreto por tipo de evento.

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
- Paginação e filtros em efetivo e logs.  
- Auditoria exportável (CSV/PDF).  
- Notificações em tempo real (WebSocket) para o feed operacional.  
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
