# DEJEM — Incremental Allocation Engine (C6)

## Princípio

O Allocation Engine **C5** permanece a distribuição inicial oficial.

C6 **nunca** recalcula a campanha. Apenas:

- concede créditos novos;
- atualiza Allocations existentes;
- cria Allocation só para **novos** interessados;
- registra inconsistências de redução de oferta.

## Cenários

| Cenário | Comportamento |
|---------|---------------|
| +N vagas (OfferEvent) | `unaccounted = offer - distributed - undistributed` → distribui por antiguidade |
| −N vagas | Não remove créditos; grava `offer_excess_slots` + auditoria `OFFER_EXCESS` |
| Novos interessados (pré-RUNNING) | Entram no pool via `POST /incremental` ou `/redistribute-remaining` |
| Cancelamento de interesse (ALLOCATED) | Cancela só créditos `AVAILABLE` via Credit Lifecycle (`origin=INCREMENTAL`); devolve à sobra |
| Sobras | `POST /redistribute-remaining` consome só `undistributed_slots` |

## Prioridade

Ordem do efetivo: `patente` → `display_order` → `nome_guerra` → `user_id`  
(`core.ranks.patente_sort_key`, mesma base do legado).

Distribuição incremental: rodadas **1 a 1** nessa ordem.

## Idempotência

Estado já consistente (`unaccounted=0` e sem pool) → `noop=true`, sem novos créditos.

## APIs

Base: `/operations/dejem/allocations`

| Método | Path |
|--------|------|
| POST | `/incremental` |
| POST | `/redistribute-remaining` |
| GET | `/preview` |
| GET | `/audit` |

## Limitações

- Sem remoção automática de créditos em redução de oferta
- Sem fila administrativa avançada
- C5 (`POST /allocate`) inalterado
- Evolução de status do crédito: [credit-lifecycle.md](./credit-lifecycle.md) (C7)
