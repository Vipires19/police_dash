# DEJEM — Operational Planning (C9)

## Objetivo

Transformar reservas (`ShiftSlot` + `Credit`) em **equipes operacionais** planejadas.

Não publica. Não gera Mapa Força. Não envia WhatsApp/PDF.

## Entidades

### OperationalTeam

| Campo | Uso |
|-------|-----|
| `campaign_id` / `shift_slot_id` | escopo do turno |
| `team_type` | `FT` \| `ROCAM` \| `APOIO` \| `ADMINISTRATIVO` |
| `vehicle_id` | FK `vehicles` (módulo existente) |
| `commander_id` | FK `users` |
| `max_members` | capacidade da equipe |
| `status` | `DRAFT` \| `READY` (sem PUBLISHED) |
| `notes` | observações |

### OperationalAssignment

| Campo | Uso |
|-------|-----|
| `credit_id` | crédito reservado (único — 1 equipe) |
| `user_id` | policial do crédito |
| `role` | `MEMBER` \| `COMMANDER` |

## Fluxo

```
ShiftSlot (reservas)
    ↓ Credits APPROVED com shift_slot_id
OperationalTeam(s) no mesmo slot
    ↓ OperationalAssignment(credit_id)
Equipe com viatura + comandante (planejamento)
```

## Regras

1. Só Credits com `shift_slot_id` no mesmo turno da equipe
2. Credit em no máximo 1 equipe (`UNIQUE credit_id`)
3. Capacidade: `len(members) ≤ max_members`
4. Mesma viatura não pode estar em 2 equipes do mesmo `shift_slot`
5. Viatura `BAIXADA` rejeitada
6. Policial consulta só equipes em que é membro

## APIs

Base: `/operations/dejem/teams`

| Método | Path | RBAC |
|--------|------|------|
| GET | `/` | admin: todos; policial: suas |
| GET | `/{id}` | admin ou membro |
| POST | `/` | admin |
| PUT | `/{id}` | admin |
| DELETE | `/{id}` | admin |
| POST | `/{id}/members` | admin |
| DELETE | `/{id}/members/{member_id}` | admin |
| PUT | `/{id}/vehicle` | admin |
| PUT | `/{id}/commander` | admin |

## Auditoria

`dejem_operational_team_audits`: actor, action, team, user, credit, vehicle, commander, details.

Ações: `CREATE` | `UPDATE` | `DELETE` | `ADD_MEMBER` | `REMOVE_MEMBER` | `SET_VEHICLE` | `SET_COMMANDER`.

## Decisões

- Reusa `vehicles` e `users` — sem novo módulo
- Planejamento ortogonal a C7/C8 (não muda status do crédito)
- Publicação / Mapa Força / mensagens → **C10**

## Limitações

- Sem publicação → **C10** ([publication.md](./publication.md))
- Sem composição automática FT/ROCAM
- Sem documentos finais
