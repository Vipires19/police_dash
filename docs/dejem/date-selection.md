# DEJEM — Date & Shift Selection (C8)

## Objetivo

Permitir que um Credit **APPROVED** reserve exatamente um **ShiftSlot** (turno compartilhado).

Não implementa: equipes, viaturas, publicação, mapa força.

## Decisão de modelo

Credit **não** guarda data/hora própria. Vincula-se a `ShiftSlot`:

```
ShiftSlot (19/08 — 04:55–12:55, 4 vagas)
    ↑
Credit A, Credit B, Credit C, Credit D  (até total_slots)
```

C9 monta equipes/viaturas a partir do mesmo slot.

## ShiftSlot

| Campo | Uso |
|-------|-----|
| `campaign_id` | campanha |
| `date` / `start_time` / `end_time` | janela do turno |
| `total_slots` | capacidade |
| `reserved_slots` | ocupadas |
| `remaining_slots` | `total - reserved` |
| `status` | `OPEN` / `FULL` / `CLOSED` |

`sync_capacity()` atualiza `remaining` e `OPEN`↔`FULL`. `CLOSED` é administrativo.

## Reserva

Regras:

- Somente `APPROVED`
- 1 crédito → no máximo 1 `shift_slot_id`
- `AVAILABLE` / `CANCELLED` / `EXECUTED` (alteração) bloqueados
- Status do crédito **não muda** na reserva (permanece `APPROVED`)
- Capacidade: `reserved_slots` nunca excede `total_slots`
- Lock `SELECT … FOR UPDATE` em Credit + ShiftSlot

### Troca (`change-slot`)

Só com crédito `APPROVED` e reserva existente: libera vaga antiga, consome nova, audita.

### Cancelamento de reserva

Libera vaga, `shift_slot_id = null`, crédito **continua APPROVED**.

### Cancelamento do crédito (C7)

Se houver reserva, libera capacidade (`RELEASE_ON_CANCEL`) antes de `CANCELLED`.

## Auditoria

Tabela `dejem_credit_reservation_audits`:

- actor, created_at
- from_shift_slot_id / to_shift_slot_id
- action: `RESERVE` | `CHANGE` | `CANCEL` | `RELEASE_ON_CANCEL`
- reason, origin

## APIs

### ShiftSlots — `/operations/dejem/shift-slots`

| Método | Path | RBAC |
|--------|------|------|
| GET | `/` | policial+ |
| GET | `/availability` | policial+ |
| GET | `/{id}` | policial+ |
| POST | `/` | admin |
| PUT | `/{id}` | admin |
| DELETE | `/{id}` | admin (só se `reserved=0`) |

### Credits — reserva

| Método | Path | RBAC |
|--------|------|------|
| POST | `/credits/{id}/reserve` | titular |
| POST | `/credits/{id}/change-slot` | titular |
| POST | `/credits/{id}/cancel-reservation` | titular |

## Limitações

- Sem montagem de equipes / FT / ROCAM → **C9** ([operational-planning.md](./operational-planning.md))
- Sem viaturas / publicação
- State machine C7 inalterada
