"""Serviço do domínio OperationalPublication (fase 4.10).

Consolida informações dos módulos (somente leitura) e gera a publicação oficial.
A geração de mensagem/PDF nasce exclusivamente aqui.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from models.dejem import DejemShiftStatus
from models.operational_publication import (
    OperationalPublication,
    OperationalPublicationAudit,
    OperationalPublicationAuditAction,
    OperationalPublicationStatus,
)
from models.service_scale import ScaleModality, ServiceScale
from models.user import User
from repositories.operational_publication_repository import OperationalPublicationRepository
from schemas.operational_publication import (
    ChecklistItem,
    ChecklistItemLevel,
    OperationalPublicationAuditPublic,
    OperationalPublicationChecklist,
    OperationalPublicationDetail,
    OperationalPublicationHistoryItem,
    OperationalPublicationHistoryResponse,
    OperationalPublicationPublic,
)
from services import dejem_map_service as dejem_map
from services.message_generation_service import MessageGenerationService
from services.scale_message_service import get_default_template
from services.service_scale_service import _load_scale, _load_scale_by_date

_BR = ZoneInfo("America/Sao_Paulo")


class OperationalPublicationError(ValueError):
    pass


def _user_label(user: User | None) -> str | None:
    if not user:
        return None
    return f"{user.patente} {user.nome_guerra}"


def _parse_checklist(raw: str | None) -> OperationalPublicationChecklist | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return OperationalPublicationChecklist.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return None


def to_public(row: OperationalPublication) -> OperationalPublicationPublic:
    return OperationalPublicationPublic(
        id=row.id,
        service_scale_id=row.service_scale_id,
        scale_date=row.scale_date,
        publication_number=row.publication_number,
        version=row.version,
        status=row.status,
        created_by_id=row.created_by_id,
        created_by_label=_user_label(row.created_by),
        published_by_id=row.published_by_id,
        published_by_label=_user_label(row.published_by),
        published_at=row.published_at,
        generated_message=row.generated_message,
        generated_pdf=row.generated_pdf,
        change_summary=row.change_summary,
        publish_reason=row.publish_reason,
        risk_acknowledged=row.risk_acknowledged,
        previous_publication_id=row.previous_publication_id,
        checklist=_parse_checklist(row.checklist_json),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def to_history_item(row: OperationalPublication) -> OperationalPublicationHistoryItem:
    return OperationalPublicationHistoryItem(
        id=row.id,
        service_scale_id=row.service_scale_id,
        scale_date=row.scale_date,
        publication_number=row.publication_number,
        version=row.version,
        status=row.status,
        published_by_label=_user_label(row.published_by) or _user_label(row.created_by),
        published_at=row.published_at,
        publish_reason=row.publish_reason,
        change_summary=row.change_summary,
        risk_acknowledged=row.risk_acknowledged,
    )


def _audit(
    repo: OperationalPublicationRepository,
    *,
    publication_id: int,
    actor_id: int,
    action: OperationalPublicationAuditAction,
    details: str | None = None,
) -> None:
    repo.add_audit(
        OperationalPublicationAudit(
            publication_id=publication_id,
            action=action,
            actor_id=actor_id,
            details=details,
        )
    )


def consolidate_snapshot(
    db: Session,
    scale: ServiceScale,
    *,
    actor: User,
    published_at: datetime | None = None,
) -> dict[str, Any]:
    """Lê Escala / equipes / viaturas / DEJEM CLOSED / observações / fardamento.

    Não altera dados dos módulos origem.
    """
    # DEJEM: consolidação oficial só CLOSED (+ INTEGRATED já incorporadas, se houver)
    dejem_blocks = dejem_map.build_map_blocks(
        db,
        scale.scale_date,
        statuses={DejemShiftStatus.CLOSED, DejemShiftStatus.INTEGRATED},
    )
    open_dejem = dejem_map.list_shifts_for_date(
        db, scale.scale_date, statuses={DejemShiftStatus.OPEN}
    )
    ready_dejem = dejem_map.list_shifts_for_date(
        db, scale.scale_date, statuses={DejemShiftStatus.READY_FOR_MAP}
    )

    from services.scale_publish_pipeline import _build_snapshot

    snapshot = _build_snapshot(
        scale,
        dejem_blocks,
        actor=actor,
        published_at=published_at or datetime.now(tz=_BR),
    )
    snapshot["meta"] = {
        "dejem_open_count": len(open_dejem),
        "dejem_ready_for_map_count": len(ready_dejem),
        "dejem_closed_or_integrated_count": len(dejem_blocks),
        "fardamento": scale.fardamento,
        "description": scale.description,
        "scale_status": scale.status.value if scale.status else None,
        "scale_title": scale.title,
    }
    return snapshot


def build_checklist(db: Session, scale: ServiceScale, snapshot: dict[str, Any]) -> OperationalPublicationChecklist:
    items: list[ChecklistItem] = []

    # Escala
    if not scale.teams:
        items.append(
            ChecklistItem(
                key="scale",
                title="ESCALA OPERACIONAL",
                level=ChecklistItemLevel.ERROR,
                detail="Nenhuma equipe cadastrada.",
                blocking=True,
            )
        )
    else:
        items.append(
            ChecklistItem(
                key="scale",
                title="ESCALA OPERACIONAL",
                level=ChecklistItemLevel.OK,
                detail=f"{len(scale.teams)} equipe(s) · {scale.title}",
            )
        )

    # DEJEM
    meta = snapshot.get("meta") or {}
    closed_n = int(meta.get("dejem_closed_or_integrated_count") or 0)
    open_n = int(meta.get("dejem_open_count") or 0)
    ready_n = int(meta.get("dejem_ready_for_map_count") or 0)
    if open_n > 0:
        items.append(
            ChecklistItem(
                key="dejem",
                title="DEJEM",
                level=ChecklistItemLevel.WARN,
                detail=f"{closed_n} pronta(s) · {open_n} ainda ABERTA(s) · {ready_n} READY_FOR_MAP",
                blocking=False,
            )
        )
    elif closed_n or ready_n:
        items.append(
            ChecklistItem(
                key="dejem",
                title="DEJEM",
                level=ChecklistItemLevel.OK,
                detail=f"{closed_n} escala(s) CLOSED/INTEGRATED"
                + (f" · {ready_n} READY_FOR_MAP" if ready_n else ""),
            )
        )
    else:
        items.append(
            ChecklistItem(
                key="dejem",
                title="DEJEM",
                level=ChecklistItemLevel.OK,
                detail="Nenhuma DEJEM para o dia (ok).",
            )
        )

    # Viaturas
    missing_vehicle = 0
    for team in scale.teams:
        if team.modality == ScaleModality.FT and not team.vehicle_id:
            missing_vehicle += 1
        if team.modality == ScaleModality.ROCAM:
            for m in team.members:
                if not m.assigned_vehicle_id:
                    missing_vehicle += 1
    if missing_vehicle:
        items.append(
            ChecklistItem(
                key="vehicles",
                title="VIATURAS",
                level=ChecklistItemLevel.ERROR,
                detail=f"{missing_vehicle} vínculo(s) de viatura ausente(s).",
                blocking=True,
            )
        )
    else:
        items.append(
            ChecklistItem(
                key="vehicles",
                title="VIATURAS",
                level=ChecklistItemLevel.OK,
                detail="Todas vinculadas.",
            )
        )

    # Conflitos (reusa validações do pipeline, sem persistir)
    from services.scale_publish_pipeline import _collect_pipeline_errors

    conflicts = _collect_pipeline_errors(db, scale)
    # Filtrar só conflitos/duplicados (estrutura de equipe sem viatura já coberta)
    conflict_msgs = [
        e
        for e in conflicts
        if "duplicad" in e.lower() or "conflito" in e.lower() or "horário" in e.lower()
    ]
    if conflict_msgs:
        items.append(
            ChecklistItem(
                key="conflicts",
                title="CONFLITOS",
                level=ChecklistItemLevel.WARN,
                detail=" · ".join(conflict_msgs[:4])
                + (f" (+{len(conflict_msgs) - 4})" if len(conflict_msgs) > 4 else ""),
                blocking=False,
            )
        )
    else:
        items.append(
            ChecklistItem(
                key="conflicts",
                title="CONFLITOS",
                level=ChecklistItemLevel.OK,
                detail="Nenhum encontrado.",
            )
        )

    # Mensagem
    items.append(
        ChecklistItem(
            key="message",
            title="MENSAGEM",
            level=ChecklistItemLevel.OK if snapshot.get("teams") else ChecklistItemLevel.PENDING,
            detail="Pronta para geração no publish."
            if snapshot.get("teams")
            else "Aguardando equipes.",
        )
    )

    # PDF (preparado)
    items.append(
        ChecklistItem(
            key="pdf",
            title="PDF",
            level=ChecklistItemLevel.PENDING,
            detail="Ainda não gerado (arquitetura preparada).",
        )
    )

    has_errors = any(i.level == ChecklistItemLevel.ERROR for i in items)
    has_warnings = any(i.level == ChecklistItemLevel.WARN for i in items)
    blocking = any(i.blocking and i.level == ChecklistItemLevel.ERROR for i in items)
    ready = not blocking and bool(scale.teams)

    items.append(
        ChecklistItem(
            key="publication",
            title="PUBLICAÇÃO",
            level=ChecklistItemLevel.OK if ready else ChecklistItemLevel.WARN,
            detail="PRONTA" if ready and not has_warnings else (
                "PRONTA (com avisos — N90 pode publicar assumindo risco)"
                if ready
                else "BLOQUEADA — corrija pendências"
            ),
        )
    )

    return OperationalPublicationChecklist(
        items=items,
        ready=ready,
        has_errors=has_errors,
        has_warnings=has_warnings,
        can_publish_with_risk=ready,
    )


def _generate_message(db: Session, snapshot: dict[str, Any]) -> str:
    tpl = get_default_template(db)
    body = tpl.body_text if tpl else None
    return MessageGenerationService(body).render_from_snapshot(snapshot)


def _generate_pdf_stub(snapshot: dict[str, Any], message: str) -> str | None:
    """Placeholder: futura geração PDF do Mapa Força. Retorna None por enquanto."""
    _ = snapshot, message
    return None


def create_or_refresh_draft(
    db: Session,
    actor: User,
    *,
    service_scale_id: int | None = None,
    scale_date: date | None = None,
) -> OperationalPublication:
    repo = OperationalPublicationRepository(db)
    scale: ServiceScale | None = None
    if service_scale_id is not None:
        scale = _load_scale(db, service_scale_id)
    elif scale_date is not None:
        scale = _load_scale_by_date(db, scale_date)
    if not scale:
        raise OperationalPublicationError("Escala operacional não encontrada")

    snapshot = consolidate_snapshot(db, scale, actor=actor)
    checklist = build_checklist(db, scale, snapshot)
    message_preview = _generate_message(db, snapshot) if scale.teams else None

    existing = repo.get_active_workspace(scale.id)
    if existing:
        existing.snapshot_json = json.dumps(snapshot, ensure_ascii=False)
        existing.checklist_json = checklist.model_dump_json()
        existing.generated_message = message_preview
        existing.generated_pdf = None
        existing.status = (
            OperationalPublicationStatus.READY
            if checklist.ready
            else OperationalPublicationStatus.DRAFT
        )
        existing.scale_date = scale.scale_date
        db.add(existing)
        _audit(
            repo,
            publication_id=existing.id,
            actor_id=actor.id,
            action=OperationalPublicationAuditAction.REFRESHED,
            details="Consolidação atualizada a partir dos módulos operacionais.",
        )
        db.commit()
        return repo.get(existing.id) or existing

    row = OperationalPublication(
        service_scale_id=scale.id,
        scale_date=scale.scale_date,
        publication_number=repo.next_publication_number(),
        version=repo.next_version(scale.id),
        status=(
            OperationalPublicationStatus.READY
            if checklist.ready
            else OperationalPublicationStatus.DRAFT
        ),
        created_by_id=actor.id,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        checklist_json=checklist.model_dump_json(),
        generated_message=message_preview,
        generated_pdf=None,
        previous_publication_id=(
            prev.id if (prev := repo.latest_published(scale.id)) else None
        ),
    )
    repo.add(row)
    _audit(
        repo,
        publication_id=row.id,
        actor_id=actor.id,
        action=OperationalPublicationAuditAction.CREATED,
        details="Draft criado por consolidação automática.",
    )
    db.commit()
    return repo.get(row.id) or row


def validate_publication(db: Session, publication_id: int, actor: User) -> OperationalPublication:
    repo = OperationalPublicationRepository(db)
    row = repo.get(publication_id)
    if not row:
        raise OperationalPublicationError("Publicação não encontrada")
    if row.status not in {
        OperationalPublicationStatus.DRAFT,
        OperationalPublicationStatus.READY,
    }:
        raise OperationalPublicationError("Somente DRAFT/READY podem ser validados")

    scale = _load_scale(db, row.service_scale_id)
    if not scale:
        raise OperationalPublicationError("Escala vinculada não encontrada")

    snapshot = consolidate_snapshot(db, scale, actor=actor)
    checklist = build_checklist(db, scale, snapshot)
    row.snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    row.checklist_json = checklist.model_dump_json()
    row.generated_message = _generate_message(db, snapshot) if scale.teams else None
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
        action=OperationalPublicationAuditAction.VALIDATED,
        details=f"ready={checklist.ready}; warnings={checklist.has_warnings}",
    )
    db.commit()
    return repo.get(row.id) or row


def publish_publication(
    db: Session,
    publication_id: int,
    actor: User,
    *,
    acknowledge_risks: bool = False,
    reason: str | None = None,
) -> OperationalPublication:
    """Publica criando versão imutável oficial (mensagem + PDF stub).

    Orquestra o pipeline de Escala (DEJEM/Mapa Força) sem alterar contratos
    dos módulos — apenas consome/dispara o fluxo já existente.
    """
    repo = OperationalPublicationRepository(db)
    row = repo.get(publication_id)
    if not row:
        raise OperationalPublicationError("Publicação não encontrada")
    if row.status not in {
        OperationalPublicationStatus.DRAFT,
        OperationalPublicationStatus.READY,
    }:
        raise OperationalPublicationError("Publicação já finalizada — crie um novo draft")

    scale = _load_scale(db, row.service_scale_id)
    if not scale:
        raise OperationalPublicationError("Escala vinculada não encontrada")

    snapshot = consolidate_snapshot(db, scale, actor=actor)
    checklist = build_checklist(db, scale, snapshot)

    if not checklist.ready:
        raise OperationalPublicationError(
            "Publicação bloqueada: " + "; ".join(
                i.detail for i in checklist.items if i.blocking
            )
        )

    if checklist.has_warnings and not acknowledge_risks:
        raise OperationalPublicationError(
            "Há avisos na consolidação. Confirme acknowledge_risks=true para "
            "publicar assumindo o risco."
        )

    # Orquestra publicação da Escala (integra DEJEM). Com risco assumido,
    # permite salvar a publicação oficial mesmo se o pipeline bloquear.
    from services.scale_publish_pipeline import PublishPipelineError, run_publish_pipeline

    pipeline_note: str | None = None
    try:
        scale = run_publish_pipeline(db, scale.id, actor)
    except PublishPipelineError as e:
        if not acknowledge_risks:
            raise OperationalPublicationError(str(e)) from e
        pipeline_note = str(e)

    row = repo.get(publication_id)
    if not row:
        raise OperationalPublicationError("Publicação não encontrada após pipeline")
    scale = _load_scale(db, row.service_scale_id) or scale
    now = datetime.now(tz=_BR)
    snapshot = consolidate_snapshot(db, scale, actor=actor, published_at=now)
    message = _generate_message(db, snapshot)
    pdf = _generate_pdf_stub(snapshot, message)

    prev = repo.latest_published(scale.id)
    # Se o draft atual ainda não é "published previous", prev pode ser última PUBLISHED
    was_republish = prev is not None and prev.id != row.id
    row.status = OperationalPublicationStatus.PUBLISHED
    row.published_by_id = actor.id
    row.published_at = now
    row.generated_message = message
    row.generated_pdf = pdf
    row.snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    row.checklist_json = checklist.model_dump_json()
    row.publish_reason = (reason or "").strip() or None
    row.risk_acknowledged = bool(
        acknowledge_risks and (checklist.has_warnings or pipeline_note)
    )
    row.previous_publication_id = prev.id if was_republish else row.previous_publication_id
    row.change_summary = (
        f"Republicação v{row.version}" if was_republish else f"Primeira publicação v{row.version}"
    )
    if reason:
        row.change_summary = f"{row.change_summary}: {reason.strip()}"
    if pipeline_note:
        row.change_summary = (
            f"{row.change_summary} | Publicado com risco (pipeline: {pipeline_note})"
        )
    db.add(row)
    _audit(
        repo,
        publication_id=row.id,
        actor_id=actor.id,
        action=(
            OperationalPublicationAuditAction.REPUBLISHED
            if was_republish
            else OperationalPublicationAuditAction.PUBLISHED
        ),
        details=row.change_summary,
    )
    if row.risk_acknowledged:
        _audit(
            repo,
            publication_id=row.id,
            actor_id=actor.id,
            action=OperationalPublicationAuditAction.RISK_ACK,
            details=pipeline_note or "Publicação com avisos — risco assumido pelo editor.",
        )
    db.commit()
    return repo.get(row.id) or row


def archive_publication(db: Session, publication_id: int, actor: User) -> OperationalPublication:
    repo = OperationalPublicationRepository(db)
    row = repo.get(publication_id)
    if not row:
        raise OperationalPublicationError("Publicação não encontrada")
    if row.status != OperationalPublicationStatus.PUBLISHED:
        raise OperationalPublicationError("Somente publicações PUBLISHED podem ser arquivadas")
    row.status = OperationalPublicationStatus.ARCHIVED
    db.add(row)
    _audit(
        repo,
        publication_id=row.id,
        actor_id=actor.id,
        action=OperationalPublicationAuditAction.ARCHIVED,
        details="Arquivada pelo editor.",
    )
    db.commit()
    return repo.get(row.id) or row


def get_detail(db: Session, publication_id: int) -> OperationalPublicationDetail:
    repo = OperationalPublicationRepository(db)
    row = repo.get(publication_id)
    if not row:
        raise OperationalPublicationError("Publicação não encontrada")
    snapshot = None
    try:
        snapshot = json.loads(row.snapshot_json) if row.snapshot_json else None
    except json.JSONDecodeError:
        snapshot = None
    base = to_public(row)
    audits = [
        OperationalPublicationAuditPublic(
            id=a.id,
            action=a.action,
            actor_id=a.actor_id,
            actor_label=_user_label(a.actor),
            details=a.details,
            created_at=a.created_at,
        )
        for a in (row.audits or [])
    ]
    return OperationalPublicationDetail(
        **base.model_dump(),
        snapshot=snapshot,
        audits=audits,
    )


def list_history(
    db: Session,
    *,
    scale_date: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> OperationalPublicationHistoryResponse:
    repo = OperationalPublicationRepository(db)
    rows, total = repo.list_history(scale_date=scale_date, limit=limit, offset=offset)
    return OperationalPublicationHistoryResponse(
        items=[to_history_item(r) for r in rows],
        total=total,
    )


def get_center_for_date(db: Session, actor: User, day: date) -> dict[str, Any]:
    """Painel do Centro de Publicação para um dia."""
    scale = _load_scale_by_date(db, day)
    repo = OperationalPublicationRepository(db)
    active = None
    checklist = None
    latest = None
    if scale:
        active = repo.get_active_workspace(scale.id)
        if active:
            checklist = _parse_checklist(active.checklist_json)
        else:
            # Preview de consolidação sem persistir
            snap = consolidate_snapshot(db, scale, actor=actor)
            checklist = build_checklist(db, scale, snap)
        pub = repo.latest_published(scale.id)
        if pub:
            latest = to_history_item(pub)
    return {
        "scale_date": day,
        "service_scale_id": scale.id if scale else None,
        "scale_title": scale.title if scale else None,
        "scale_status": scale.status.value if scale else None,
        "active_publication": to_public(active) if active else None,
        "checklist": checklist,
        "latest_published": latest,
    }
