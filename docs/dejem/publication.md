# DEJEM — Publication (C10)

## Objetivo

Publicar o planejamento operacional (C9) em versões imutáveis.

Não altera Allocation / Incremental / Lifecycle / ShiftSlot / regras de equipe — apenas congela snapshot e bloqueia mutações enquanto `ACTIVE`.

## PublishedSchedule

| Campo | Uso |
|-------|-----|
| `campaign_id` | campanha |
| `version` | 1, 2, 3… (UNIQUE com campanha) |
| `status` | `ACTIVE` \| `SUPERSEDED` |
| `snapshot_json` | equipes, membros, comandante, viaturas, turnos, créditos |
| `mapa_payload_json` | payload para Mapa Força existente |
| `change_summary` | diff vs versão anterior |
| `previous_publication_id` | encadeamento |

Apenas **uma** `ACTIVE` por campanha.

## Versionamento

```
POST /publish     → v1 ACTIVE
unlock + edits
POST /publish     → v2 ACTIVE, v1 SUPERSEDED
```

ou

```
POST /republish   → SUPERSEDE ACTIVE + nova versão imediatamente
POST /republish {unlock_for_revision:true} → só SUPERSEDE (libera edição)
```

Nunca sobrescreve snapshot.

## Bloqueio

Com `ACTIVE`: bloqueia mutações em equipes, ShiftSlots e reservas de crédito.

Fluxo de revisão: `unlock_for_revision` → editar C8/C9 → `POST /publish`.

## Mapa Força

Adapter `adapters/mapa_force.py` gera blocos compatíveis com o módulo legado (`dejem_map_service` / pipeline).  
Não cria novo Mapa Força. Endpoint: `GET /published/{id}/mapa-force`.

## Exportação

- JSON / CSV via `PublicationExportService`
- PDF: placeholder (`NotImplementedError`)

## WhatsApp

`adapters/whatsapp.py` — `WhatsAppAdapter` + `NoOpWhatsAppAdapter`.  
`prepare_operational_message()` ok; `send()` não envia nesta sprint.

## APIs

Base: `/operations/dejem`

| Método | Path |
|--------|------|
| POST | `/publish` |
| POST | `/republish` |
| GET | `/published?campaign_id=` |
| GET | `/published/{id}` |
| GET | `/published/{id}/snapshot` |
| GET | `/published/{id}/mapa-force` |
| GET | `/published/{id}/export.json` |
| GET | `/published/{id}/export.csv` |
| GET | `/published/{id}/whatsapp-draft` |

Admin para publicar/exportar; consulta de publicados para usuário autenticado.

## Auditoria

`dejem_published_schedule_audits`: actor, version, action (`PUBLISH`/`REPUBLISH`/`UNLOCK_FOR_REVISION`), reason, change_summary.

## MVP

C10 encerra o MVP DEJEM em `/operations/dejem`.
