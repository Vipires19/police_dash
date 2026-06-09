<div align="center">

# Pelotão System

**Sistema operacional web para gestão interna de pelotão policial**  
Força Tática / ROCAM · efetivo · perfis · viaturas · folgas e compensações · férias e LP · escalas de serviço · logs

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

O **Pelotão System** é uma aplicação **full-stack** pensada para uso interno: autenticação **JWT**, cadastro com **aprovação por perfil de comando**, **RBAC** granular, painel operacional, **efetivo** com agrupamento visual e **drag-and-drop** de antiguidade (persistido), **edição de role** pelo staff, **perfis policiais** detalhados, módulo de **viaturas** (FT e ROCAM) com **histórico e logs operacionais** automáticos, **folgas e compensações**, **férias e LP (Licença Prêmio)** com calendário operacional e regras de review, **escalas de serviço** (equipes FT/ROCAM, publicação, auditoria, exportação operacional para WhatsApp) e **dashboard** com feed de frota, atividade de escalas e indicadores de afastamento — inclusive **dias críticos** para o comando.

Interface em **tema escuro** (operacional), **sidebar responsiva** (menu hamburger no mobile) e empacotamento via **Docker**.

### Motivação

O projeto busca **aliviar rotinas exaustivas** do pelotão, tornando-as **mais dinâmicas** e devolvendo tempo ao efetivo. A modelagem reflete a **realidade operacional** vivida durante os turnos e a dinâmica do pelotão.

Não é produto comercial: houve **desenvolvimento assistido por IA** (*vibe coding*) para acelerar entregas e revisar código gerado, sempre com supervisão humana. Os prompts seguem um **modelo fixo**, alterando apenas o objetivo de cada tarefa. **MCPs do Cursor** apoiaram o fluxo — em especial o **Context7** para documentação atualizada; o MCP **Playwright** auxiliou testes de interface quando coube.

---

## Objetivos operacionais

Centralizar, com rastreabilidade:

- quem compõe o efetivo, em que ordem hierárquica e com quais dados cadastrais;
- estado das viaturas (operando, fora de operação, manutenção, reserva) e **quem** alterou **o quê** e **por quê**;
- solicitações mensais de folga, créditos de compensação, férias e LP, com aprovação do comando e trilha auditável;
- **escalas de serviço** diárias (equipes FT e ROCAM, empenhos, viaturas/motos, publicação);
- acesso conforme **role** do policial no sistema (não confundir **patente** institucional com **role** de aplicação).

---

## Capturas de tela

[Login](docs/screenshots/login.png)  
[Dashboard](docs/screenshots/dashboard.png)  
[Efetivo](docs/screenshots/efetivo.png)  
[Viaturas](docs/screenshots/viaturas.png)  
[Perfil](docs/screenshots/perfil.png)  
[Férias e LP](docs/screenshots/ferias.png)  
[Escala de serviço](docs/screenshots/escala-servico.png)  
[Exportação da escala (WhatsApp)](docs/screenshots/escala-export.png)

> Caminhos placeholder para novas capturas — adicione PNGs em `docs/screenshots/` quando disponíveis.

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| API | **FastAPI** 0.115, **Uvicorn**, **Pydantic** v2 |
| ORM / BD | **SQLAlchemy** 2.0, **Alembic**, **PostgreSQL** 16, **psycopg** 3 |
| Auth | **JWT** (`python-jose`), senhas **bcrypt** |
| Frontend | **React** 19, **TypeScript**, **Vite** 6, **react-router-dom** 7 |
| UI | **Tailwind CSS** 4 (`@tailwindcss/vite`), ícones **Lucide** |
| DnD | **@dnd-kit** (core, sortable, utilities) |
| Deploy local | **Docker Compose** (Postgres + API + Nginx estático) |

---

## Arquitetura

```
┌─────────────┐     HTTPS/HTTP      ┌──────────────┐
│  Navegador  │ ◄──────────────────► │  Nginx :80   │  (build estático Vite)
└──────┬──────┘                      └──────┬───────┘
       │                                    │
       │  VITE_API_URL (build)              │  browser → API (configurar CORS)
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

- A **SPA** consome a API REST; o JWT fica em `localStorage` (`Authorization: Bearer`).
- O **backend** valida JWT, aplica dependências RBAC por rota e persiste com SQLAlchemy.
- **Migrations Alembic** versionam o schema (incluindo ENUMs nativos do PostgreSQL sem duplicar `CREATE TYPE` em migrations existentes).
- **Subida do container backend** executa `alembic upgrade head` no entrypoint antes do Uvicorn.

---

## Estrutura do repositório (resumo)

```text
pelotao-system/
├── backend/
│   ├── alembic/              # env.py + versions (001…013)
│   ├── auth/                 # JWT, deps (approver, scale editor, vehicle editor, …)
│   ├── core/                 # config, patentes, política de folgas, labels de compensação
│   ├── database/             # Base, session
│   ├── models/               # User, Vehicle, Leave, Vacation, ServiceScale, StolenVehicle, …
│   │   └── stolen_vehicle.py
│   ├── routes/               # auth, users, vehicles, leaves, compensations, vacations, service_scales, stolen_vehicles
│   │   └── stolen_vehicles.py
│   ├── schemas/              # DTOs Pydantic por domínio
│   │   └── stolen_vehicle.py
│   ├── services/             # serviços de domínio + scale_export_service.py
│   │   └── stolen_vehicle_service.py
│   ├── main.py
│   ├── requirements.txt
│   └── docker-entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── components/       # efetivo, vehicle/, folgas/, vacations/, service-scales/, stolen-vehicles/
│   │   ├── constants/        # ranks.ts (grupos visuais)
│   │   ├── hooks/            # AuthContext
│   │   ├── layouts/          # OperationalLayout (sidebar)
│   │   ├── pages/            # Dashboard, Efetivo, Viaturas, StolenVehicles, Folgas, Férias, Escala, Perfil, Aprovações
│   │   │   └── StolenVehiclesPage.tsx
│   │   ├── services/         # clientes API por módulo
│   │   │   └── stolenVehiclesApi.ts
│   │   └── types.ts + types/*.ts
│   │       └── stolenVehicles.ts
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

## Funcionalidades implementadas

| Módulo | O que existe hoje |
|--------|-------------------|
| Autenticação | Cadastro (`PENDING`); login só para `APPROVED` + `is_active`; JWT HS256; expiração configurável. |
| Aprovações | Lista pendente; aprovar com **role** obrigatória ou rejeitar (`ADMIN`, `N90`, `TAT_CMD`). |
| Bootstrap admin | Admin opcional na subida via `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`, …). |
| Dashboard | Boas-vindas; **3 últimos logs** de viaturas; **3 últimos eventos** de escala; **afastados hoje** (folgas / férias / LP separados); alertas de dias críticos. |
| Layout | Sidebar: Dashboard, Efetivo, **Escala de serviço**, Viaturas, Folgas, **Férias**, Perfil, **Aprovações**. |
| Efetivo | Grupos visuais (Oficiais, SubTen/Sargentos, Cabos/Soldados, **Estágio**); DnD de antiguidade por patente; edição de **role** pelo staff; reorder otimista. |
| Perfil | Campos operacionais; edições conforme RBAC. |
| Viaturas | Listagem FT / ROCAM; criar / editar status (com motivo); timeline por viatura; feed global. |
| Folgas e compensações | Calendário mensal; solicitações mensais ou com crédito; **REVIEW** automático ao exceder limites; hub de aprovação. |
| Férias e LP | Calendário mensal; períodos de **15 ou 30 dias**; máx. **2** policiais simultâneos (Férias/LP); status + review do comando; flags de disponibilidade no efetivo. |
| Escalas de serviço | Calendário mensal; múltiplas equipes/dia; FT (viatura + até 4 policiais) e ROCAM (até 3 policiais, **motos individuais**); rascunho/publicação; logs de auditoria; histórico; **exportação operacional**. |
| **Veículos Produtos de Crime** | Cadastro de furto/roubo; grupo **0 a 9** automático pela placa; histórico permanente; consulta por placa/modelo/cor; localização; folha operacional **0 a 9** (carros/motos); impressão A4 inspirada na folha física. |
| Health | `GET /health` |

---

## RBAC (`UserRole`)

| Role | Efeito principal no código atual |
|------|----------------------------------|
| **ADMIN** | Acesso total a aprovações, efetivo (reorder + perfis + `is_active` + **role** de terceiros), viaturas, **escalas** (nível N90). |
| **N90** | Aprovador; staff do efetivo; viaturas; **editor de escala** (`SCALE_EDITOR_ROLES`). |
| **TAT_CMD** | Aprovador; staff do efetivo; viaturas; **visualiza** escalas publicadas (sem editar escala). |
| **BRACAL** | Próprio perfil; CRUD viaturas; compensações; solicita folgas/férias; **sem** edição de escala. |
| **ESTAGIO** | Próprio perfil; viaturas somente leitura; solicita folgas/férias; grupo **Estágio** no efetivo; **sem** edição de escala. |

> **Patente** (campo texto) ≠ **role** (enum da aplicação).

Dependências no backend:

- `require_approver` / `STAFF_EDITOR_ROLES` → cadastros pendentes, folgas/compensações/férias pendentes, `PUT /users/efetivo/reorder`, edições amplas de perfil (incluindo **role** de terceiros, não a própria).
- `require_scale_editor` (`SCALE_EDITOR_ROLES`: **ADMIN**, **N90**) → criar/publicar/editar/excluir escalas e equipes.
- `require_vehicle_editor` → `POST/PATCH` em `/vehicles`.
- `require_compensation_creator` (exceto `ESTAGIO`) → `POST /compensations`.

---

## Fluxo de autenticação

1. `POST /auth/register` → usuário `PENDING`.  
2. Aprovador chama `POST /users/approve/{id}` com `decision` + `role` (ao aprovar).  
3. `POST /auth/login` → JWT `access_token` (`sub` = id do usuário; claim `role`).  
4. Rotas protegidas: header `Authorization: Bearer <token>`.  
5. `get_current_approved_user` exige `APPROVED` + `is_active`.  
6. Logout no cliente limpa `localStorage`.

Documentação interativa: **`http://localhost:8000/docs`** (Swagger UI).

---

## Modelo de dados principal

### `users`

`email`, `patente`, `nome_guerra`, campos de perfil, `display_order`, `is_active`, `role` (`userrole`), `status` (`userstatus`), timestamps.

### `vehicles` / `vehicle_logs`

Unidades de frota (FT/ROCAM) e logs operacionais por alteração.

### Folgas / compensações

`leave_requests`, `leave_approval_logs`, `compensation_events`, `user_compensations` — migrations `004`, `005`.

### Férias / LP

- **`vacation_requests`**: `vacation_type` (`FERIAS` \| `LP`), `start_date`, `end_date`, `total_days` (**15** ou **30**), `status` (`PENDING` \| `REVIEW` \| `APPROVED` \| `REJECTED` \| `CANCELLED`), campos de review/decisão, `vacation_approval_logs` para auditoria.

### Escalas de serviço

- **`service_scales`**: uma linha por dia (`scale_date` único), `title`, `status` (`DRAFT` \| `PUBLISHED`), `published_at`, `created_by_id`.
- **`scale_teams`**: `modality` (`FT` \| `ROCAM`), `vehicle_id` opcional (**somente FT**; **NULL na ROCAM**), `start_datetime`, `end_datetime`, `mission_name`, `notes`.
- **`scale_team_members`**: `user_id`, `assigned_vehicle_id` opcional (**moto ROCAM** por policial).
- **`scale_logs`**: trilha de auditoria (`TEAM_ADDED`, `PUBLISHED`, `MEMBERS_CHANGED`, …).

Alembic: `006_vacations.py`, `007_service_scales.py` (após `001`–`005`).

### Veículos produtos de crime

- **`stolen_vehicles`**: `vehicle_type` (`CARRO` \| `MOTO`), `plate`, `vehicle_model`, `color`, `year`, `occurrence_type` (`FURTO` \| `ROUBO`), `plate_group` (0 a 9), `observation`, `is_recovered`, `recovered_at`, `recovered_by_id`, `recovered_notes`, `created_by_id`, timestamps.
- Registros **não são excluídos**; veículos localizados saem da folha operacional, mas permanecem no histórico e na consulta.
- Alembic: `012_stolen_vehicles.py`, `013_stolen_vehicles_recover_audit.py`.

---

## Módulo de efetivo

- Rota: `GET /users/efetivo` (usuários aprovados).
- Ordenação no servidor: hierarquia de patente + `display_order` + nome.
- **Agrupamento visual** (somente frontend): Oficiais · SubTen/Sargentos · Cabos/Soldados · **Estágio** (`role === ESTAGIO`).
- **Reorder**: `PUT /users/efetivo/reorder` com `{ patente, ordered_user_ids }` (staff); UI otimista sem recarregar a página inteira.
- **Edição de role**: `PATCH /users/{id}` com `role` (staff; não no próprio usuário).
- Frontend: `/efetivo`, **@dnd-kit**, drawer operacional.

---

## Módulo de férias e LP

- **Calendário** (`GET /vacations/calendar`): visão mensal; entradas de **Férias** e **LP**; resumo para comando (pendentes, **afastados hoje**, dias críticos quando **≥2** Férias/LP simultâneas no dia).
- **Solicitação** (`POST /vacations/request`): períodos de **15 ou 30** dias consecutivos; regra operacional: máx. **2** policiais em Férias/LP no mesmo dia → pode entrar em **`REVIEW`** com `review_reason`.
- **Status**: `PENDING`, `REVIEW`, `APPROVED`, `REJECTED`, `CANCELLED`.
- **Comando**: `PATCH /vacations/{id}/approve|reject`; policial `PATCH /vacations/{id}/cancel` na própria solicitação pendente/review.
- **Integração com efetivo**: calendário/efetivo sinalizam policiais com folga ou férias/LP ativas na data.
- Frontend: `/ferias` (calendário + modal de solicitação); aba de aprovações para férias pendentes.

---

## Módulo de escalas de serviço

### Calendário operacional

- Rota: `/escala-servico` — calendário mensal (`GET /service-scales/calendar`).
- Drawer do dia: criar escala (rascunho), adicionar/editar/remover equipes, publicar, excluir escala, **exportar** (quando publicada).

### Estrutura das equipes

| Modalidade | Viatura | Efetivo | Observações |
|------------|---------|---------|-------------|
| **FT (Força Tática)** | **Uma viatura principal** (obrigatória, `OPERANDO`, FT) | Até **4** policiais | Empenhos pré-definidos (Tático Comando, Supervisor Tático, Força Tática) ou missão customizada |
| **ROCAM** | **Sem viatura de equipe** (`vehicle_id = NULL`) | Até **3** policiais | Cada policial com **moto ROCAM individual** (`assigned_vehicle_id`, obrigatório) |

> **ROCAM não possui mais viatura principal da equipe.** Cada policial ROCAM tem sua própria moto vinculada.

### Regras operacionais (frontend + backend)

- **Viatura FT única** por escala publicada (sem viatura duplicada entre equipes).
- **Moto ROCAM única** por escala (sem moto duplicada entre membros).
- **Policial único** por escala (não pode constar em duas equipes no mesmo dia).
- Filtragem em tempo real de viaturas, motos e efetivo disponíveis ao montar equipes.
- **Editar equipe** in-place: patch de metadados e membros sem remover/recriar.

### Publicação e auditoria

- Rascunhos visíveis apenas para **editores de escala** (`ADMIN` / `N90`).
- `POST /service-scales/{id}/publish` — exige ao menos uma equipe; define `PUBLISHED` + `published_at`.
- Cada alteração gera entrada em **`scale_logs`** (ator, ação, descrição).

### Integração automática com folgas, férias e LP

Se um policial for **escalado** em uma data **D** com folga ou férias/LP ativas cobrindo **D**, o sistema **cancela automaticamente** o afastamento (com motivo auditável), garantindo flexibilidade operacional.

### Exportação operacional (WhatsApp)

- Disponível apenas para escalas **`PUBLISHED`**.
- `GET /service-scales/{id}/export` → `{ "text": "…" }` (texto puro, quebras de linha preservadas).
- Formatador em **`services/scale_export_service.py`** (desacoplado para futura integração WhatsApp/IA).
- Frontend: botão **Exportar** → modal com preview + **Copiar** + feedback “Copiado”.

Exemplo de texto exportado (resumido):

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

Horários fora do padrão 06:00–18:00 no dia da escala exibem empenho + faixa horária antes do bloco da equipe.

---

## Módulo de viaturas

- Página `/viaturas`: seções FT e ROCAM, fluxo de status, logs, feed.

---

## Módulo Veículos Produtos de Crime

Substituição digital da folha física **“0 a 9”** para acompanhamento de veículos produtos de furto e roubo.

### Funcionalidades

- **Cadastro** de veículos (`CARRO` / `MOTO`, placa, veículo, cor, ano, `FURTO` / `ROUBO`, observação opcional).
- **Classificação automática por grupo (0 a 9)** usando o **primeiro número** encontrado na placa (ex.: `FWB0F63` → grupo `0`).
- **Histórico permanente** — nenhum registro é excluído automaticamente.
- **Consulta** por placa, modelo ou cor (`GET /stolen-vehicles/search`).
- **Marcação de veículo localizado** — exclusão lógica via `is_recovered` e `recovered_at` (com `recovered_by_id` e `recovered_notes` quando informados).
- **Folha operacional 0 a 9**: até **10 registros mais recentes não localizados** por grupo; preenchimento **de baixo para cima** (mais recente na linha inferior).
- **Separação carros / motos** na folha e na impressão A4 (duas páginas).
- Layout de tabela contínua por grupo, inspirado na folha física do pelotão (colunas: Placa, Veículo, Cor, Ano, F/R).
- Frontend: `/veiculos-produtos-crime` — abas **Cadastro**, **Folha 0 a 9**, **Consulta**; menu **Veículos Produtos de Crime**.

---

## Logs operacionais

| Domínio | Mecanismo |
|---------|-----------|
| Viaturas | `vehicle_logs` + `GET /vehicles/recent-logs` |
| Folgas | `leave_approval_logs` |
| Férias | `vacation_approval_logs` |
| Escalas | `scale_logs` + `GET /service-scales/recent-events` |

---

## Módulo de folgas e compensações

- **Calendário** (`GET /leaves/calendar`): visão mensal; **≥4** policiais de folga no dia → **crítico** (dashboard).
- **Solicitações**, **compensações**, **aprovações** — comportamento central mantido; ver seções anteriores do README.
- Frontend: `/folgas`, `/admin/pending-users`.

---

## Dashboard operacional

- Rota: `/dashboard`.
- **Escalas de serviço**: últimos **3** eventos operacionais; ícone rápido de **exportação** por evento (abre modal quando a escala está publicada).
- **Viaturas**: últimas **3** entradas do feed de frota.
- **Comando — afastados hoje**: listas separadas de **Folgas**, **Férias** e **LP** (aprovados, data atual).
- Banners de dias críticos para folgas (≥4) e férias/LP (≥2).

---

## API REST (atual)

### Auth — `/auth`

| Método | Caminho | Descrição |
|--------|---------|-----------|
| POST | `/auth/register` | Cadastro (pendente). |
| POST | `/auth/login` | Login → JWT. |

### Users — `/users`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| GET | `/users/me` | Aprovado, ativo. |
| GET | `/users/pending` | Aprovador. |
| GET | `/users/efetivo` | Efetivo aprovado. |
| PUT | `/users/efetivo/reorder` | Staff. |
| POST | `/users/approve/{user_id}` | Aprovador. |
| GET | `/users/{user_id}` | Perfil. |
| PATCH | `/users/{user_id}` | Perfil + **role** (regras staff). |

### Vehicles — `/vehicles`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| GET | `/vehicles/recent-logs` | Feed (`limit`). |
| GET/POST/PATCH | `/vehicles/…` | Editores de frota. |
| GET | `/vehicles/{id}/logs` | Timeline. |

### Leaves — `/leaves`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| GET | `/leaves/calendar` | Visão mensal. |
| GET | `/leaves/pending` | Aprovador. |
| POST | `/leaves/request` | Criar solicitação. |
| PATCH | `/leaves/{id}/approve\|reject\|cancel` | Fluxo. |

### Compensations — `/compensations`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| GET | `/compensations/pending` | Aprovador. |
| GET | `/compensations/available` | Créditos próprios. |
| POST | `/compensations/` | Criador (não `ESTAGIO`). |
| PATCH | `/compensations/{id}/approve\|reject` | Aprovador. |

### Vacations — `/vacations`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| GET | `/vacations/calendar` | Visão mensal (`year`, `month`). |
| GET | `/vacations/pending` | Aprovador. |
| POST | `/vacations/request` | Período 15 ou 30 dias. |
| PATCH | `/vacations/{id}/approve` | Aprovador. |
| PATCH | `/vacations/{id}/reject` | Aprovador. |
| PATCH | `/vacations/{id}/cancel` | Titular (pendente/review). |

### Service scales — `/service-scales`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| GET | `/service-scales/calendar` | Calendário mensal. |
| GET | `/service-scales/{date}` | Detalhe do dia (escala, efetivo, viaturas). |
| GET | `/service-scales/history` | Histórico paginado. |
| GET | `/service-scales/recent-events` | Feed de auditoria. |
| GET | `/service-scales/presets/missions` | Empenhos FT / ROCAM. |
| POST | `/service-scales/` | Editor de escala — criar escala. |
| PATCH | `/service-scales/{id}` | Editor de escala — metadados. |
| POST | `/service-scales/{id}/publish` | Editor de escala. |
| POST | `/service-scales/{id}/teams` | Editor de escala — adicionar equipe. |
| PATCH | `/service-scales/team/{id}` | Editor de escala — editar equipe (+ `members` opcional). |
| PATCH | `/service-scales/team/{id}/members` | Editor de escala — substituir membros. |
| PATCH | `/service-scales/team/{id}/remove` | Editor de escala — remover equipe. |
| DELETE | `/service-scales/{id}` | Editor de escala — excluir escala. |
| GET | `/service-scales/{id}/export` | **Somente publicada** → `{ "text": "…" }`. |

### Veículos Produtos de Crime — `/stolen-vehicles`

| Método | Caminho | Auth / notas |
|--------|---------|----------------|
| POST | `/stolen-vehicles/` | Usuário aprovado — cadastro (`plate_group` calculado no servidor). |
| GET | `/stolen-vehicles/` | Listagem com filtros opcionais (`is_recovered`, `vehicle_type`, `plate_group`). |
| GET | `/stolen-vehicles/search` | Busca por placa, modelo ou cor (`q`). |
| GET | `/stolen-vehicles/sheet` | Folha operacional 0 a 9 (carros + motos, somente não localizados). |
| PATCH | `/stolen-vehicles/{id}/recover` | Marcar veículo como localizado. |

### Outros

| Método | Caminho |
|--------|---------|
| GET | `/health` |

---

## Execução local

### Pré-requisitos

- Python **3.12+**, **Node.js** 20+ (ou 22), **PostgreSQL** 16 (ou apenas Docker).

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

> Execute `uvicorn` a partir de **`backend/`** com **`backend/.env`**. O Docker Compose usa **`.env`** na raiz — mantenha alinhados.

### Frontend

```bash
cd frontend
npm install
export VITE_API_URL=http://localhost:8000
npm run dev
```

Abra **`http://localhost:5173`**. Garanta que `CORS_ORIGINS` inclua essa origem.

---

## Configuração `.env`

Veja **[`.env.example`](.env.example)**. Principais: `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_PATENTE`, `ADMIN_NOME_GUERRA`.

---

## Docker

```bash
cd docker
docker compose up --build
```

| Serviço | Porta |
|---------|-------|
| `db` | 5432 |
| `backend` | 8000 |
| `frontend` | 80 |

---

## Comandos úteis

| Local | Comando |
|-------|---------|
| Backend | `alembic upgrade head` / `uvicorn main:app --reload` |
| Frontend | `npm run dev` / `npm run build` |
| Docker | `docker compose up --build` |

---

## Roadmap (ideias)

- Testes automatizados (pytest + Vitest/Playwright).  
- **WhatsApp / IA**: enviar texto de exportação via bot usando `scale_export_service`.  
- Exportação PDF de escalas publicadas.  
- Notificações em tempo real (WebSocket) para filas de aprovação.  
- Política de senha e 2FA.

### Veículos Produtos de Crime — evoluções futuras

- Auditoria completa de localização (logs dedicados).  
- Expansão de `recovered_by_id` e `recovered_notes` em painéis operacionais.  
- Dashboard operacional do módulo.  
- Estatísticas por tipo (`CARRO` / `MOTO`) e natureza (`FURTO` / `ROUBO`).  
- Integração futura com **Heimdall**.  
- Exportação PDF da folha 0 a 9 (além da impressão HTML).

---

## Melhorias técnicas previstas

- Versionar **`package-lock.json`** de forma consistente.  
- CI (lint + test + build).  
- Documentar **`VITE_API_URL`** para staging/produção.

---

## Segurança

- **bcrypt** + **JWT**; RBAC por rota.  
- Exportação e rascunhos de escala respeitam role e estado de publicação.  
- **Não** commitar segredos em `.env`.  
- Produção: HTTPS, rotacionar `SECRET_KEY`, backups do Postgres.

---

## Licença

**MIT License** — veja [`LICENSE`](LICENSE).

---

## Autor

Vinícius Pires · [E-mail](viinycampos19@hotmail.com) · [LinkedIn](https://www.linkedin.com/in/vin%C3%ADcius-pires-544a88241/)

---

<div align="center">

<sub>Documentação em português (pt-BR) alinhada ao repositório atual. English: [README.md](README.md).</sub>

</div>
