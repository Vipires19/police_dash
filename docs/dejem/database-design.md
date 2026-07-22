# DEJEM — Database design

## R1 — `038_dejem_hardening_indexes`

```sql
UNIQUE INDEX uq_dejem_published_one_active_per_campaign
  ON dejem_published_schedules (campaign_id)
  WHERE status = 'ACTIVE'
```

## C10 — `037_dejem_publication`

`dejem_published_schedules` + audits.

## C9 — `036_dejem_operational_planning`

Teams / assignments.

## C8 — `035_dejem_date_selection`

ShiftSlots + `credit.shift_slot_id`.
