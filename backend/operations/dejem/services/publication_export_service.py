"""Exportação de snapshots publicados (JSON / CSV). PDF futuro."""

from __future__ import annotations

import csv
import io
import json
from typing import Any


class PublicationExportService:
    """Gera artefatos a partir do snapshot imutável."""

    def to_json(self, snapshot: dict[str, Any], *, indent: int = 2) -> str:
        return json.dumps(snapshot, ensure_ascii=False, indent=indent, default=str)

    def to_csv(self, snapshot: dict[str, Any]) -> str:
        """Uma linha por membro de equipe."""
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(
            [
                "team_id",
                "team_type",
                "shift_slot_id",
                "date",
                "start_time",
                "end_time",
                "vehicle_id",
                "vehicle_prefixo",
                "commander_id",
                "credit_id",
                "user_id",
                "patente",
                "nome_guerra",
                "role",
            ]
        )
        for team in snapshot.get("teams", []):
            slot = team.get("shift_slot") or {}
            members = team.get("members") or []
            if not members:
                writer.writerow(
                    [
                        team.get("id"),
                        team.get("team_type"),
                        team.get("shift_slot_id"),
                        slot.get("date"),
                        slot.get("start_time"),
                        slot.get("end_time"),
                        team.get("vehicle_id"),
                        team.get("vehicle_prefixo"),
                        team.get("commander_id"),
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]
                )
                continue
            for m in members:
                writer.writerow(
                    [
                        team.get("id"),
                        team.get("team_type"),
                        team.get("shift_slot_id"),
                        slot.get("date"),
                        slot.get("start_time"),
                        slot.get("end_time"),
                        team.get("vehicle_id"),
                        team.get("vehicle_prefixo"),
                        team.get("commander_id"),
                        m.get("credit_id"),
                        m.get("user_id"),
                        m.get("patente"),
                        m.get("nome_guerra"),
                        m.get("role"),
                    ]
                )
        return buf.getvalue()

    def to_pdf_placeholder(self, snapshot: dict[str, Any]) -> None:
        """Arquitetura reservada — PDF fora do escopo C10."""
        raise NotImplementedError("Exportação PDF será implementada em sprint futura.")
