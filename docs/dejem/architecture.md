# DEJEM — Arquitetura

```
C5–C10  MVP funcional
        ↓
R1      Hardening (locks, HTTP errors, índices, performance)
        ↓
Frontend / produção
```

Camadas: `api` → `services` → `repositories` → `models` (+ `adapters` C10).

Helpers transversais (R1):

- `api/http_errors.domain_http_error`
- `services/publication_lock.raise_if_campaign_locked`
- `CampaignRepository.get_for_update` em allocate / incremental / publish

Detalhes: [architectural-review.md](./architectural-review.md).

Legado `/dejem/*` intacto.
