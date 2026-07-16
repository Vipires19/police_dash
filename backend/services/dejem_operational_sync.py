"""Sincroniza Snapshot / Publicação / Mensagem após edição DEJEM.

Disparado quando uma escala já no fluxo operacional (fechada / integrada)
é alterada — sem exigir republicação completa da Escala.
"""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy.orm import Session

from models.operational_publication import (
    OperationalPublicationAuditAction,
    OperationalPublicationStatus,
)
from models.service_scale import ServiceScaleVersion
from models.user import User
from repositories.operational_publication_repository import OperationalPublicationRepository
from services.service_scale_service import _load_scale_by_date


def refresh_operational_artifacts_for_day(
    db: Session,
    day: date,
    *,
    actor: User,
) -> bool:
    """Atualiza snapshot, publicação ativa/publicada e mensagem do dia.

    Retorna True se havia escala operacional para sincronizar.
    """
    scale = _load_scale_by_date(db, day)
    if not scale:
        return False

    # Import tardio evita ciclo com operational_publication_service.
    from services.operational_publication_service import (
        _audit,
        _generate_message,
        build_checklist,
        consolidate_snapshot,
    )

    snapshot = consolidate_snapshot(db, scale, actor=actor)
    checklist = build_checklist(db, scale, snapshot)
    message = _generate_message(db, snapshot) if scale.teams else None
    snapshot_raw = json.dumps(snapshot, ensure_ascii=False)
    checklist_raw = checklist.model_dump_json()

    if scale.current_version_id:
        version = db.get(ServiceScaleVersion, scale.current_version_id)
        if version:
            version.snapshot_json = snapshot_raw
            if message is not None:
                version.export_text = message
            version.change_summary = (
                f"{version.change_summary or ''} | DEJEM atualizada (sync automático)."
            ).strip(" |")
            db.add(version)

    repo = OperationalPublicationRepository(db)
    targets: list = []
    active = repo.get_active_workspace(scale.id)
    if active:
        targets.append(active)
    published = repo.latest_published(scale.id)
    if published and (not active or published.id != active.id):
        targets.append(published)

    for row in targets:
        row.snapshot_json = snapshot_raw
        row.checklist_json = checklist_raw
        if message is not None:
            row.generated_message = message
        if row.status in {
            OperationalPublicationStatus.DRAFT,
            OperationalPublicationStatus.READY,
        }:
            row.status = (
                OperationalPublicationStatus.READY
                if checklist.ready
                else OperationalPublicationStatus.DRAFT
            )
        db.add(row)
        _audit(
            repo,
            publication_id=row.id,
            actor_id=actor.id,
            action=OperationalPublicationAuditAction.REFRESHED,
            details="Sync automático após edição de Escala DEJEM.",
        )

    db.commit()
    return True
