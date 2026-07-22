"""PublicationService — publicar planejamento DEJEM (Sprint C10).

Não altera engines C5–C9. Congela snapshot imutável versionado.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User
from models.vehicle import Vehicle
from operations.dejem.adapters.mapa_force import build_mapa_force_payload
from operations.dejem.adapters.whatsapp import get_whatsapp_adapter
from operations.dejem.models.enums import PublishedScheduleStatus
from operations.dejem.models.published_schedule import (
    PublishedSchedule,
    PublishedScheduleAudit,
)
from operations.dejem.repositories.campaign_repository import CampaignRepository
from operations.dejem.repositories.credit_repository import CreditRepository
from operations.dejem.repositories.operational_team_repository import (
    OperationalTeamRepository,
)
from operations.dejem.repositories.published_schedule_repository import (
    PublishedScheduleRepository,
)
from operations.dejem.repositories.shift_slot_repository import ShiftSlotRepository
from operations.dejem.schemas.publication import (
    PublishRequest,
    PublishedScheduleResponse,
    RepublishRequest,
)
from operations.dejem.services.publication_export_service import PublicationExportService


class PublicationError(ValueError):
    pass


class PublicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PublishedScheduleRepository(db)
        self.campaigns = CampaignRepository(db)
        self.teams = OperationalTeamRepository(db)
        self.slots = ShiftSlotRepository(db)
        self.credits = CreditRepository(db)
        self.exports = PublicationExportService()

    def list_published(self, campaign_id: int) -> list[PublishedScheduleResponse]:
        self._require_campaign(campaign_id)
        return [self._to_response(r) for r in self.repo.list_by_campaign(campaign_id)]

    def get(self, publication_id: int) -> PublishedScheduleResponse:
        return self._to_response(self._get_or_raise(publication_id))

    def get_snapshot(self, publication_id: int) -> dict[str, Any]:
        row = self._get_or_raise(publication_id)
        return json.loads(row.snapshot_json)

    def get_mapa_payload(self, publication_id: int) -> list[dict[str, Any]]:
        row = self._get_or_raise(publication_id)
        return json.loads(row.mapa_payload_json)

    def export_json(self, publication_id: int) -> str:
        return self.exports.to_json(self.get_snapshot(publication_id))

    def export_csv(self, publication_id: int) -> str:
        return self.exports.to_csv(self.get_snapshot(publication_id))

    def prepare_whatsapp_draft(
        self,
        publication_id: int,
        *,
        body: str | None = None,
        recipient: str | None = None,
    ) -> dict[str, Any]:
        row = self._get_or_raise(publication_id)
        text = body or (
            f"DEJEM campanha {row.campaign_id} — escala publicada v{row.version}."
        )
        draft = get_whatsapp_adapter().prepare_operational_message(
            campaign_id=row.campaign_id,
            version=row.version,
            body=text,
            recipient=recipient,
            metadata={"publication_id": row.id},
        )
        return {
            "channel": draft.channel,
            "recipient": draft.recipient,
            "body": draft.body,
            "metadata": draft.metadata,
            "send_implemented": False,
        }

    def publish(self, actor: User, body: PublishRequest) -> PublishedScheduleResponse:
        campaign = self.campaigns.get_for_update(body.campaign_id)
        if not campaign:
            raise PublicationError("Campanha DEJEM não encontrada.")
        active = self.repo.get_active_for_update(body.campaign_id)
        if active:
            raise PublicationError(
                f"Já existe publicação ACTIVE (v{active.version}). Use POST /republish."
            )
        return self._create_version(
            actor,
            campaign_id=body.campaign_id,
            notes=body.notes,
            reason=body.reason or "publish",
            action="PUBLISH",
            previous=None,
        )

    def republish(self, actor: User, body: RepublishRequest) -> PublishedScheduleResponse | dict[str, Any]:
        campaign = self.campaigns.get_for_update(body.campaign_id)
        if not campaign:
            raise PublicationError("Campanha DEJEM não encontrada.")
        active = self.repo.get_active_for_update(body.campaign_id)

        if body.unlock_for_revision:
            if not active:
                raise PublicationError("Não há publicação ACTIVE para desbloquear.")
            active.status = PublishedScheduleStatus.SUPERSEDED
            self.repo.save(active)
            self._audit(
                publication=active,
                actor=actor,
                action="UNLOCK_FOR_REVISION",
                reason=body.reason or "unlock_for_revision",
                change_summary="Planejamento liberado para revisão; sem nova versão.",
            )
            self.db.commit()
            return {
                "campaign_id": body.campaign_id,
                "unlocked": True,
                "superseded_version": active.version,
                "message": "Publicação SUPERSEDED. Edite o planejamento e use POST /publish.",
            }

        if not active:
            return self._create_version(
                actor,
                campaign_id=body.campaign_id,
                notes=body.notes,
                reason=body.reason or "republish",
                action="REPUBLISH",
                previous=None,
            )

        previous = active
        previous.status = PublishedScheduleStatus.SUPERSEDED
        self.repo.save(previous)
        return self._create_version(
            actor,
            campaign_id=body.campaign_id,
            notes=body.notes,
            reason=body.reason or "republish",
            action="REPUBLISH",
            previous=previous,
        )

    def _create_version(
        self,
        actor: User,
        *,
        campaign_id: int,
        notes: str | None,
        reason: str,
        action: str,
        previous: PublishedSchedule | None,
    ) -> PublishedScheduleResponse:
        snapshot = self._build_snapshot(campaign_id)
        if not snapshot.get("teams"):
            raise PublicationError(
                "Nenhuma equipe operacional para publicar. Monte o planejamento (C9) antes."
            )

        prev_snap = json.loads(previous.snapshot_json) if previous else None
        change_summary = self._diff_summary(prev_snap, snapshot)
        mapa = build_mapa_force_payload(snapshot)
        version = self.repo.max_version(campaign_id) + 1

        row = PublishedSchedule(
            campaign_id=campaign_id,
            published_by=actor.id,
            published_at=datetime.now(timezone.utc),
            version=version,
            status=PublishedScheduleStatus.ACTIVE,
            notes=notes,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False, default=str),
            mapa_payload_json=json.dumps(mapa, ensure_ascii=False, default=str),
            change_summary=change_summary,
            previous_publication_id=previous.id if previous else None,
        )
        self.repo.add(row)
        self._audit(
            publication=row,
            actor=actor,
            action=action,
            reason=reason,
            change_summary=change_summary,
        )
        # Prepara draft WhatsApp (sem enviar)
        get_whatsapp_adapter().prepare_operational_message(
            campaign_id=campaign_id,
            version=version,
            body=f"DEJEM v{version} publicada (campanha {campaign_id}).",
            metadata={"publication_id": row.id, "action": action},
        )
        self.db.commit()
        self.db.refresh(row)
        return self._to_response(row)

    def _build_snapshot(self, campaign_id: int) -> dict[str, Any]:
        teams = self.teams.list_by_campaign(campaign_id)
        slots = {s.id: s for s in self.slots.list_by_campaign(campaign_id)}

        user_ids: set[int] = set()
        vehicle_ids: set[int] = set()
        credit_ids: set[int] = set()
        for team in teams:
            if team.vehicle_id:
                vehicle_ids.add(team.vehicle_id)
            if team.commander_id:
                user_ids.add(team.commander_id)
            for a in team.assignments:
                user_ids.add(a.user_id)
                credit_ids.add(a.credit_id)

        users: dict[int, User] = {}
        if user_ids:
            users = {
                u.id: u
                for u in self.db.scalars(select(User).where(User.id.in_(user_ids))).all()
            }
        vehicles: dict[int, Vehicle] = {}
        if vehicle_ids:
            vehicles = {
                v.id: v
                for v in self.db.scalars(
                    select(Vehicle).where(Vehicle.id.in_(vehicle_ids))
                ).all()
            }
        credits_map = {
            c.id: c
            for c in self.credits.list_by_campaign(campaign_id)
            if c.id in credit_ids
        }

        team_payloads: list[dict[str, Any]] = []
        for team in teams:
            slot = slots.get(team.shift_slot_id)
            vehicle = vehicles.get(team.vehicle_id) if team.vehicle_id else None
            commander = users.get(team.commander_id) if team.commander_id else None
            members: list[dict[str, Any]] = []
            for a in team.assignments:
                user = users.get(a.user_id)
                credit = credits_map.get(a.credit_id)
                members.append(
                    {
                        "assignment_id": a.id,
                        "credit_id": a.credit_id,
                        "user_id": a.user_id,
                        "role": a.role.value if hasattr(a.role, "value") else a.role,
                        "patente": getattr(user, "patente", None) if user else None,
                        "nome_guerra": getattr(user, "nome_guerra", None) if user else None,
                        "re": getattr(user, "re", None) if user else None,
                        "display_order": getattr(user, "display_order", 0) if user else 0,
                        "credit_status": (
                            credit.status.value
                            if credit and hasattr(credit.status, "value")
                            else (credit.status if credit else None)
                        ),
                    }
                )
            team_payloads.append(
                {
                    "id": team.id,
                    "team_type": team.team_type.value
                    if hasattr(team.team_type, "value")
                    else team.team_type,
                    "status": team.status.value if hasattr(team.status, "value") else team.status,
                    "shift_slot_id": team.shift_slot_id,
                    "shift_slot": {
                        "id": slot.id if slot else None,
                        "date": slot.date.isoformat() if slot else None,
                        "start_time": slot.start_time.isoformat() if slot else None,
                        "end_time": slot.end_time.isoformat() if slot else None,
                    },
                    "vehicle_id": team.vehicle_id,
                    "vehicle_prefixo": getattr(vehicle, "prefixo", None) if vehicle else None,
                    "vehicle_placa": getattr(vehicle, "placa", None) if vehicle else None,
                    "commander_id": team.commander_id,
                    "commander_nome": (
                        f"{getattr(commander, 'patente', '')} "
                        f"{getattr(commander, 'nome_guerra', '')}".strip()
                        if commander
                        else None
                    ),
                    "notes": team.notes,
                    "max_members": team.max_members,
                    "members": members,
                }
            )

        return {
            "campaign_id": campaign_id,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "teams": team_payloads,
            "team_count": len(team_payloads),
            "member_count": sum(len(t["members"]) for t in team_payloads),
        }

    def _diff_summary(
        self,
        previous: dict[str, Any] | None,
        current: dict[str, Any],
    ) -> str:
        if previous is None:
            return (
                f"Primeira publicação: {current.get('team_count', 0)} equipe(s), "
                f"{current.get('member_count', 0)} membro(s)."
            )
        prev_teams = {t["id"]: t for t in previous.get("teams", [])}
        curr_teams = {t["id"]: t for t in current.get("teams", [])}
        added = sorted(set(curr_teams) - set(prev_teams))
        removed = sorted(set(prev_teams) - set(curr_teams))
        changed: list[int] = []
        for tid in set(prev_teams) & set(curr_teams):
            if json.dumps(prev_teams[tid], sort_keys=True, default=str) != json.dumps(
                curr_teams[tid], sort_keys=True, default=str
            ):
                changed.append(tid)
        parts = [
            f"equipes {previous.get('team_count', 0)}→{current.get('team_count', 0)}",
            f"membros {previous.get('member_count', 0)}→{current.get('member_count', 0)}",
        ]
        if added:
            parts.append(f"novas={added}")
        if removed:
            parts.append(f"removidas={removed}")
        if changed:
            parts.append(f"alteradas={sorted(changed)}")
        return "; ".join(parts)

    def _audit(
        self,
        *,
        publication: PublishedSchedule,
        actor: User,
        action: str,
        reason: str | None,
        change_summary: str | None,
    ) -> None:
        self.repo.add_audit(
            PublishedScheduleAudit(
                publication_id=publication.id,
                campaign_id=publication.campaign_id,
                actor_id=actor.id,
                action=action,
                version=publication.version,
                reason=reason,
                change_summary=change_summary,
            )
        )

    def _get_or_raise(self, publication_id: int) -> PublishedSchedule:
        row = self.repo.get(publication_id)
        if not row:
            raise PublicationError("Publicação não encontrada.")
        return row

    def _require_campaign(self, campaign_id: int) -> None:
        if not self.campaigns.get(campaign_id):
            raise PublicationError("Campanha DEJEM não encontrada.")

    def _to_response(self, row: PublishedSchedule) -> PublishedScheduleResponse:
        snap = json.loads(row.snapshot_json) if row.snapshot_json else {}
        return PublishedScheduleResponse(
            id=row.id,
            campaign_id=row.campaign_id,
            published_by=row.published_by,
            published_at=row.published_at,
            version=row.version,
            status=row.status,
            notes=row.notes,
            change_summary=row.change_summary,
            previous_publication_id=row.previous_publication_id,
            team_count=int(snap.get("team_count", 0) or 0),
            member_count=int(snap.get("member_count", 0) or 0),
        )
