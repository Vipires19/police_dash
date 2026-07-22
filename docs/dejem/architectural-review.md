# DEJEM — Architectural Review (R1)

## Objetivo

Revisão e hardening do MVP C1–C10 **sem** novas funcionalidades, entidades ou endpoints.
Contratos públicos e regras de negócio preservados.

## Problemas encontrados

| Área | Problema |
|------|----------|
| APIs | `_http_error` duplicado em 8 routers |
| Lock C10 | `_guard_lock` duplicado em 3 services |
| Concorrência | `allocate` / `incremental` / `publish` sem lock de campanha |
| Publicação | possível corrida com duas ACTIVE na mesma campanha |
| Performance | `max_version` carregava todas as versões; snapshot N+1 em User/Vehicle |
| Performance | `_to_response` fazia `json.loads` duas vezes |
| Código morto | import `CreditStatusAudit` não usado no incremental; `Integer` órfão em `credit.py` |

## Melhorias realizadas

1. **`api/http_errors.domain_http_error`** — mapeamento HTTP único (400/403/404)
2. **`raise_if_campaign_locked`** — lock C10 centralizado
3. **`CampaignRepository.get_for_update`** — usado em allocate, incremental e publish
4. **`get_active_for_update` + índice parcial único** — uma ACTIVE por campanha
5. **Snapshot** — batch load de users/vehicles/credits
6. **`max_version`** — `func.max` em SQL
7. Limpeza de imports mortos

## Decisões

- Não mover pastas nem renomear endpoints
- Índice parcial `WHERE status = 'ACTIVE'` em vez de trigger
- State machine C7 mantida (defesa em profundidade intacta)
- Sem mudança de assinatura de API / schemas públicos

## Recomendações futuras

- Testes de integração automatizados do fluxo completo Campaign→Publication
- Observabilidade (métricas de allocate/publish)
- PDF / WhatsApp send (já previstos pós-MVP)
- Avaliar partial unique em `(shift_slot_id, vehicle_id)` com `NULLS NOT DISTINCT` (PG 15+)
- Cache read-only de availability de ShiftSlots sob carga
