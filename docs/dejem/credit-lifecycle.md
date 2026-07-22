# DEJEM — Credit Lifecycle (C7)

## Objetivo

Ciclo de vida completo dos créditos via **máquina de estados explícita**.  
Prepara o crédito para a Sprint C8 (escolha de datas/turnos), **sem** implementar datas, escalas ou publicação.

## Máquina de estados

Componente único: `CreditStateMachine` (`models/credit_state_machine.py`).

Toda alteração de status passa por `CreditService._apply_transition` → `CreditStateMachine.transition`.

### Fluxo principal

```
AVAILABLE → DATE_SELECTED → PENDING_APPROVAL → APPROVED → EXECUTED
```

### Desistência / cancelamentos

```
AVAILABLE → CANCELLED
DATE_SELECTED → AVAILABLE          (release antes da aprovação)
PENDING_APPROVAL → CANCELLED
APPROVED → CANCELLED               (somente administrador)
```

### Terminais

- `EXECUTED` — não volta a nenhum estado
- `CANCELLED` — terminal

## Transições válidas

| De | Para |
|----|------|
| AVAILABLE | DATE_SELECTED, CANCELLED |
| DATE_SELECTED | AVAILABLE, PENDING_APPROVAL |
| PENDING_APPROVAL | APPROVED, CANCELLED |
| APPROVED | EXECUTED, CANCELLED |
| EXECUTED | — |
| CANCELLED | — |

Qualquer outra transição → `CreditError` / HTTP 400.

### Regras extras

- `AVAILABLE` nunca vai direto a `EXECUTED` (já bloqueado pela tabela)
- `APPROVED → CANCELLED` exige origem `ADMIN` ou `MANUAL`
- `EXECUTED` é imutável

## CreditService

| Método | Transição | Quem |
|--------|-----------|------|
| `select_date()` | AVAILABLE → DATE_SELECTED | titular |
| `release()` | DATE_SELECTED → AVAILABLE | titular |
| `request_approval()` | DATE_SELECTED → PENDING_APPROVAL | titular |
| `approve()` | PENDING_APPROVAL → APPROVED | admin |
| `cancel()` | * → CANCELLED (se permitido) | admin (ou INCREMENTAL em AVAILABLE) |
| `execute()` | APPROVED → EXECUTED | admin |

`select_date` **não** persiste data/turno — apenas o estado.

## Reserva de turno (C8)

Após `APPROVED`, o policial reserva um `ShiftSlot` via `Credit.shift_slot_id`.  
A state machine **não** muda: crédito permanece `APPROVED`.

Ver [date-selection.md](./date-selection.md).

## Auditoria

Tabela `dejem_credit_status_audits` (C4 + C7):

| Campo | Uso |
|-------|-----|
| `credit_id` | crédito |
| `actor_id` | usuário responsável |
| `created_at` | data/hora |
| `from_status` / `to_status` | estados |
| `reason` | motivo opcional (C7) |
| `origin` | POLICE / ADMIN / SYSTEM / INCREMENTAL / MANUAL (C7) |

Nenhuma transição sem auditoria.

## APIs

Base: `/operations/dejem/credits`

| Método | Path | RBAC |
|--------|------|------|
| GET | `/{id}` | titular ou admin |
| GET | `/{id}/history` | titular ou admin |
| POST | `/{id}/select-date` | titular |
| POST | `/{id}/release` | titular |
| POST | `/{id}/request-approval` | titular |
| POST | `/{id}/approve` | admin |
| POST | `/{id}/cancel` | admin |
| POST | `/{id}/execute` | admin |

CRUD admin C4 preservado (`GET /`, `POST /`, `PUT /{id}`, `DELETE /{id}`, `GET /{id}/audits`).

Body opcional nas ações: `{ "reason": "..." }`.

## Integração C6

`IncrementalAllocationService.release_available_credits` cancela `AVAILABLE` via `CreditService.cancel(..., origin=INCREMENTAL, commit=False)` — mesma state machine, um commit no final.

## Limitações (C7)

- Sem escolha real de datas/turnos → implementado em C8 (`ShiftSlot`)
- Sem escalas / publicação / mensagens
- Sem montagem de equipes
- C5 (`POST /allocate`) e C6 (incremental) inalterados em comportamento de distribuição

## Próximo (C9)

Montagem operacional sobre créditos já reservados em ShiftSlots.
