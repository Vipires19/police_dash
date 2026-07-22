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
| `vehicle_id` | FK `vehicles` |
| `commander_id` | FK `users` (derivado do assignment `COMMANDER`) |
| `mission_name` | missão/empenho — **mesmo padrão da Escala Operacional** |
| `max_members` | capacidade da equipe |
| `status` | `DRAFT` \| `READY` |
| `notes` | observações |

### OperationalAssignment

| Campo | Uso |
|-------|-----|
| `credit_id` | crédito reservado (opcional — God Mode) |
| `user_id` | policial |
| `role` | função operacional |

A função **pertence ao assignment**, nunca ao `User` nem ao `OperationalTeam`.

A missão **pertence à equipe** (`mission_name`), nunca ao assignment.

## Missão operacional

Reutiliza integralmente a Escala Operacional:

- Presets: `FT_MISSION_PRESETS` / `ROCAM_MISSION_PRESETS` (`schemas/service_scale.py` e `frontend/src/types/serviceScale.ts`)
- Endpoint de presets: `GET /service-scales/presets/missions`
- UI compartilhada: `MissionPresetSelect` (`frontend/src/components/service-scales/missionPresets.tsx`)
- Texto livre via opção “Personalizado…”

Exemplos de empenho (presets atuais): Tático Comando, Supervisor Tático, Força Tática, ROCAM 1–3 — além de missão customizada.

Na Escala DEJEM (produção), `DejemShift.mission_name` espelha o mesmo campo.

## Funções por tipo de equipe

### FT

| Enum | Label UI |
|------|----------|
| `COMMANDER` | Comandante da Equipe |
| `DRIVER` | Motorista |
| `THIRD_MAN` | 3º Homem |
| `FOURTH_MAN` | 4º Homem |

### ROCAM

| Enum | Label UI |
|------|----------|
| `COMMANDER` | Comandante da Equipe |
| `MOTO_2` | Moto 2 |
| `MOTO_3` | Moto 3 |

### Validações

- Cada função exclusiva no máximo **uma vez** por equipe
- Listas só com integrantes da própria equipe
- God Mode e distribuição automática são equivalentes nas listas

## God Mode

Admin inclui policial com `user_id` **sem** `credit_id`.

Após inclusão:

- integra a equipe normalmente;
- aparece em Comandante / Motorista / 3º / 4º / Moto 2 / Moto 3;
- crédito **não** é exigido.

## Escala DEJEM (produção) — UI

`DejemShiftDayDrawer` monta a equipe no padrão Escala Operacional:

```
Equipe FT — {missão}
Missão [Selecionar]
Comandante / Motorista / 3º Homem / 4º Homem

Equipe ROCAM — {missão}
Missão [Selecionar]
Comandante / Moto 2 / Moto 3
```

Reutiliza:

- `teamRolesFor` / `setRoleUser` / `emptyRoleAssignments`
- `MissionPresetSelect` / `missionToPreset`

## APIs

`/operations/dejem/teams` — `mission_name` em create/update/response; roles via `PUT .../roles`.

Escala DEJEM: `mission_name` em create/update de shift; `PUT /dejem/shifts/{id}/roles`.

## Compatibilidade

Não altera Campaign, Credits, ShiftSlot, Publication nem Allocation Engine.
