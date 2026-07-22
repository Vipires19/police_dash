# DEJEM — Allocation Domain + Engine

## Status

| Sprint | Conteúdo |
|--------|----------|
| C4 | Infra Offer / Allocation / Credit |
| **C5** | **Allocation Engine (igualitário)** |
| C6 | Incremental Allocation Engine |
| C7 | Credit Lifecycle (estados; sem datas) |

> Escolha de datas e escalas **não** fazem parte desta sprint (ver C7/C8).

## Algoritmo C5

```
available = Σ OfferEvents  (fallback: total_available_slots legado)
n = |interessados|
per = available // n
remaining = available % n   → campaign.undistributed_slots

Para cada interessado:
  Allocation(allocated=per)
  per × Credit(AVAILABLE)
```

Exemplo: 100 / 20 → 5 cada, remaining=0, 20 Allocations, 100 Credits.  
Exemplo: 103 / 20 → 5 cada, remaining=3 (não distribuídas).

## Idempotência

Se a campanha já tiver Allocations ou Credits → erro 400.  
Sem recriação nesta sprint.

## Consistência

`Σ Credits = Σ Allocation.allocated_slots = distributed`  
`distributed + remaining = available`

## APIs Engine

Base: `/operations/dejem/allocations`

| Método | Path |
|--------|------|
| POST | `/allocate` body `{campaign_id}` |
| GET | `/allocation-summary?campaign_id=` |
| GET | `/remaining?campaign_id=` |
| GET | `/credits?campaign_id=` |

Admin: `require_dejem_admin`.

## Limitações C5

- Sem redistribuição por antiguidade (diferente do legado `/dejem/.../distribute`)
- Sobras ficam em `undistributed_slots` para C6
- Sem vínculo crédito ↔ data/escala (lifecycle de estado em C7; datas em C8)

## Equivalência legado

| Legado | Nova |
|-------|------|
| `POST /dejem/months/{id}/distribute` | `POST /operations/dejem/allocations/allocate` |
| Algoritmo legado (base + sobras por antiguidade) | Igualitário puro (sobras preservadas) |

## Incremental (C6)

Ver [incremental-allocation.md](./incremental-allocation.md).

O C5 **não** é alterado. C6 processa apenas deltas (`POST /incremental`, `/redistribute-remaining`).
