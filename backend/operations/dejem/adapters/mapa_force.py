"""Adapter — estrutura consumível pelo Mapa Força existente (C10).

Não altera `dejem_map_service` / pipeline legado.
Gera payload compatível com blocos DEJEM do mapa.
"""

from __future__ import annotations

from typing import Any


_MAP_TITLE: dict[str, str] = {
    "FT": "APOIO TÁTICO",
    "ROCAM": "ROCAM EXTRA",
    "APOIO": "DEJEM APOIO",
    "ADMINISTRATIVO": "DEJEM ADMINISTRATIVO",
}


def build_mapa_force_payload(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    """Converte snapshot DEJEM C9/C10 em lista de blocos estilo Mapa Força."""
    blocks: list[dict[str, Any]] = []
    for team in snapshot.get("teams", []):
        slot = team.get("shift_slot") or {}
        members = []
        for m in team.get("members", []):
            members.append(
                {
                    "user_id": m.get("user_id"),
                    "patente": m.get("patente") or "",
                    "nome_guerra": m.get("nome_guerra") or "",
                    "re": m.get("re"),
                    "display_order": m.get("display_order") or 0,
                    "role": m.get("role"),
                    "credit_id": m.get("credit_id"),
                }
            )
        members.sort(key=lambda x: (x.get("display_order") or 0, (x.get("nome_guerra") or "").lower()))
        team_type = team.get("team_type") or "APOIO"
        blocks.append(
            {
                "source": "operations_dejem",
                "team_id": team.get("id"),
                "title": _MAP_TITLE.get(team_type, "DEJEM"),
                "team_type": team_type,
                "date": slot.get("date"),
                "start_time": slot.get("start_time"),
                "end_time": slot.get("end_time"),
                "vehicle_id": team.get("vehicle_id"),
                "vehicle_prefixo": team.get("vehicle_prefixo"),
                "commander_id": team.get("commander_id"),
                "commander_nome": team.get("commander_nome"),
                "members": members,
                "shift_slot_id": team.get("shift_slot_id"),
            }
        )
    blocks.sort(key=lambda b: (b.get("date") or "", b.get("start_time") or "", b.get("team_id") or 0))
    return blocks
