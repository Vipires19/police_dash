"""Pipeline automático de publicação da Escala de Serviço (fase 4.7).

Etapas:
1. Validar estrutura da escala
2. Buscar DEJEM CLOSED/READY_FOR_MAP
3. Integrar ao mapa
4. Validar policiais duplicados
5. Validar viaturas duplicadas
6. Gerar versão imutável
7. Publicar
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.dejem import DejemShiftStatus
from models.service_scale import (
    ScaleLogAction,
    ScaleModality,
    ServiceScale,
    ServiceScaleVersion,
)
from models.user import User
from schemas.service_scale import ScaleTeamMemberInput
from services import dejem_map_service as dejem_map
from services.service_scale_service import (
    _BR,
    _append_scale_log,
    _load_scale,
    _validate_members,
    _validate_scale_uniqueness,
)

_INTEGRABLE = {DejemShiftStatus.CLOSED, DejemShiftStatus.READY_FOR_MAP}


class PublishPipelineError(ValueError):
    """Erro bloqueante do pipeline de publicação."""


def _next_version_number(db: Session, scale_id: int) -> int:
    current = db.scalar(
        select(func.max(ServiceScaleVersion.version_number)).where(
            ServiceScaleVersion.service_scale_id == scale_id
        )
    )
    return int(current or 0) + 1


def _validate_structure(scale: ServiceScale) -> list[str]:
    errors: list[str] = []
    if not scale.teams:
        errors.append("Adicione ao menos uma equipe antes de publicar.")
        return errors
    for team in scale.teams:
        if team.end_datetime <= team.start_datetime:
            errors.append(
                f"Horário inválido na equipe «{team.mission_name}» "
                "(término deve ser posterior ao início)."
            )
        if not team.members:
            errors.append(f"Equipe «{team.mission_name}» sem policiais.")
        if team.modality == ScaleModality.FT and not team.vehicle_id:
            errors.append(f"Equipe FT «{team.mission_name}» sem viatura.")
        try:
            inputs = [
                ScaleTeamMemberInput(
                    user_id=m.user_id,
                    assigned_vehicle_id=m.assigned_vehicle_id,
                    role_label=m.role_label,
                )
                for m in team.members
            ]
            _validate_members(team.modality, inputs)
        except ValueError as e:
            errors.append(f"Equipe «{team.mission_name}»: {e}")
    return errors


def _validate_duplicate_users(scale: ServiceScale) -> list[str]:
    counts: Counter[int] = Counter()
    labels: dict[int, str] = {}
    for team in scale.teams:
        for m in team.members:
            counts[m.user_id] += 1
            u = m.user
            labels[m.user_id] = (
                f"{u.patente} {u.nome_guerra}" if u else f"user#{m.user_id}"
            )
    return [
        f"Policial duplicado na escala: {labels[uid]}"
        for uid, n in counts.items()
        if n > 1
    ]


def _validate_duplicate_vehicles(scale: ServiceScale) -> list[str]:
    errors: list[str] = []
    ft_seen: dict[int, str] = {}
    moto_seen: dict[int, str] = {}
    for team in scale.teams:
        if team.modality == ScaleModality.FT and team.vehicle_id:
            if team.vehicle_id in ft_seen:
                prefix = team.vehicle.prefixo if team.vehicle else str(team.vehicle_id)
                errors.append(
                    f"Viatura FT duplicada: {prefix} "
                    f"(equipes «{ft_seen[team.vehicle_id]}» e «{team.mission_name}»)."
                )
            else:
                ft_seen[team.vehicle_id] = team.mission_name
        for m in team.members:
            mid = m.assigned_vehicle_id
            if not mid:
                continue
            if mid in moto_seen:
                prefix = (
                    m.assigned_vehicle.prefixo if m.assigned_vehicle else str(mid)
                )
                errors.append(
                    f"Moto ROCAM duplicada: {prefix} "
                    f"(já em «{moto_seen[mid]}», também em «{team.mission_name}»)."
                )
            else:
                moto_seen[mid] = team.mission_name
    return errors


def _validate_uniqueness_via_existing_rules(scale: ServiceScale) -> list[str]:
    """Reaproveita as regras de edição, equipe a equipe."""
    errors: list[str] = []
    for team in scale.teams:
        members = [
            ScaleTeamMemberInput(
                user_id=m.user_id,
                assigned_vehicle_id=m.assigned_vehicle_id,
                role_label=m.role_label,
            )
            for m in team.members
        ]
        try:
            _validate_scale_uniqueness(
                scale,
                exclude_team_id=team.id,
                modality=team.modality,
                vehicle_id=team.vehicle_id,
                members=members,
            )
        except ValueError as e:
            errors.append(f"Equipe «{team.mission_name}»: {e}")
    return errors


def _validate_dejem_officer_conflicts(db: Session, scale: ServiceScale) -> list[str]:
    """Policial na escala operacional e em DEJEM elegível ao mapa → erro."""
    scale_users: dict[int, str] = {}
    for team in scale.teams:
        for m in team.members:
            u = m.user
            scale_users[m.user_id] = (
                f"{u.patente} {u.nome_guerra}" if u else f"user#{m.user_id}"
            )

    candidates = dejem_map.list_shifts_for_date(
        db, scale.scale_date, statuses=_INTEGRABLE
    )
    errors: list[str] = []
    for shift in candidates:
        for p in shift.participants or []:
            from models.dejem import ParticipantStatus

            if p.status == ParticipantStatus.CANCELLED:
                continue
            if p.user_id in scale_users:
                title = dejem_map.map_block_title(shift.shift_type)
                errors.append(
                    f"Conflito DEJEM: {scale_users[p.user_id]} está na escala "
                    f"operacional e em «{title}» "
                    f"({shift.start_time.strftime('%H:%M')}–"
                    f"{shift.end_time.strftime('%H:%M')})."
                )
    return errors


def _hhmm_from_datetime(value: datetime) -> str:
    """Horário operacional local (America/Sao_Paulo) no formato HH:MM."""
    local = value.astimezone(_BR) if value.tzinfo is not None else value
    return f"{local.hour:02d}:{local.minute:02d}"


def _hhmm_from_any(value: Any) -> str | None:
    """Normaliza time / datetime / 'HH:MM[:SS]' para 'HH:MM'."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _hhmm_from_datetime(value)
    if hasattr(value, "hour") and hasattr(value, "minute") and not isinstance(value, str):
        return f"{int(value.hour):02d}:{int(value.minute):02d}"
    text = str(value).strip()
    if "T" in text:
        try:
            return _hhmm_from_datetime(datetime.fromisoformat(text.replace("Z", "+00:00")))
        except ValueError:
            return None
    # "06:00:00" | "06:00"
    parts = text.split(":")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return None


def _normalize_dejem_block(block: Any) -> dict[str, Any]:
    data = block.model_dump(mode="json") if hasattr(block, "model_dump") else dict(block)
    start = _hhmm_from_any(data.get("start_time"))
    end = _hhmm_from_any(data.get("end_time"))
    if start:
        data["start_time"] = start
    if end:
        data["end_time"] = end
    # Garante chave explícita para a mensagem (mesmo quando None).
    if "vehicle_prefixo" not in data:
        data["vehicle_prefixo"] = None
    prefix = data.get("vehicle_prefixo")
    if prefix is not None:
        data["vehicle_prefixo"] = str(prefix).strip() or None
    return data


def _build_snapshot(
    scale: ServiceScale,
    dejem_blocks: list[Any],
    *,
    actor: User | None = None,
    published_at: datetime | None = None,
) -> dict[str, Any]:
    teams_payload = []
    for team in scale.teams:
        start_time = _hhmm_from_datetime(team.start_datetime)
        end_time = _hhmm_from_datetime(team.end_datetime)
        teams_payload.append(
            {
                "id": team.id,
                "modality": team.modality.value,
                "mission_name": team.mission_name,
                "notes": team.notes,
                "vehicle_id": team.vehicle_id,
                "vehicle_prefixo": team.vehicle.prefixo if team.vehicle else None,
                "start_datetime": team.start_datetime.isoformat(),
                "end_datetime": team.end_datetime.isoformat(),
                # Horário operacional da equipe (fonte da verdade para QTR na mensagem)
                "start_time": start_time,
                "end_time": end_time,
                "members": [
                    {
                        "user_id": m.user_id,
                        "patente": m.user.patente if m.user else "",
                        "nome_guerra": m.user.nome_guerra if m.user else "",
                        "re": (m.user.re if m.user else None) or None,
                        "display_order": m.user.display_order if m.user else 0,
                        "assigned_vehicle_id": m.assigned_vehicle_id,
                        "assigned_vehicle_prefixo": (
                            m.assigned_vehicle.prefixo if m.assigned_vehicle else None
                        ),
                        "role_label": m.role_label,
                    }
                    for m in team.members
                ],
            }
        )
    unit = None
    if actor is not None:
        unit = getattr(actor, "organizational_unit", None)
        unit = unit.value if unit is not None else None
    elif scale.created_by is not None:
        u = scale.created_by.organizational_unit
        unit = u.value if u is not None else None
    return {
        "scale_id": scale.id,
        "scale_date": scale.scale_date.isoformat(),
        "title": scale.title,
        "description": scale.description,
        "fardamento": scale.fardamento,
        "organizational_unit": unit,
        "published_at": published_at.isoformat() if published_at else None,
        "teams": teams_payload,
        "dejem_blocks": [_normalize_dejem_block(b) for b in dejem_blocks],
    }


def _diff_summaries(prev_json: str | None, new_snapshot: dict[str, Any]) -> str:
    if not prev_json:
        return "Primeira publicação (versão 1)."
    try:
        prev = json.loads(prev_json)
    except json.JSONDecodeError:
        return "Nova publicação (snapshot anterior ilegível)."

    changes: list[str] = []
    if prev.get("title") != new_snapshot.get("title"):
        changes.append(f"Título: «{prev.get('title')}» → «{new_snapshot.get('title')}»")

    prev_teams = {t["id"]: t for t in prev.get("teams", [])}
    new_teams = {t["id"]: t for t in new_snapshot.get("teams", [])}
    for tid in sorted(set(prev_teams) - set(new_teams)):
        changes.append(f"Equipe removida: «{prev_teams[tid].get('mission_name')}»")
    for tid in sorted(set(new_teams) - set(prev_teams)):
        changes.append(f"Equipe adicionada: «{new_teams[tid].get('mission_name')}»")
    for tid in sorted(set(prev_teams) & set(new_teams)):
        a, b = prev_teams[tid], new_teams[tid]
        if a.get("members") != b.get("members"):
            changes.append(f"Membros alterados em «{b.get('mission_name')}»")
        if a.get("vehicle_id") != b.get("vehicle_id"):
            changes.append(f"Viatura alterada em «{b.get('mission_name')}»")

    prev_dejem = {b.get("shift_id") for b in prev.get("dejem_blocks", [])}
    new_dejem = {b.get("shift_id") for b in new_snapshot.get("dejem_blocks", [])}
    if prev_dejem != new_dejem:
        changes.append(
            f"DEJEM no mapa: {len(prev_dejem)} → {len(new_dejem)} bloco(s)."
        )

    return "; ".join(changes) if changes else "Republicação sem alterações estruturais detectadas."


def _collect_pipeline_errors(db: Session, scale: ServiceScale) -> list[str]:
    errors = _validate_structure(scale)
    errors.extend(_validate_duplicate_users(scale))
    errors.extend(_validate_duplicate_vehicles(scale))
    errors.extend(_validate_uniqueness_via_existing_rules(scale))
    errors.extend(_validate_dejem_officer_conflicts(db, scale))
    return list(dict.fromkeys(errors))


def preview_publish_message(
    db: Session,
    scale_id: int,
    actor: User,
    *,
    description_override: str | None = None,
) -> dict[str, Any]:
    """Monta preview da mensagem sem persistir integração/publicação.

    DEJEM candidatas (CLOSED/READY_FOR_MAP) entram no snapshot provisório
    junto das já INTEGRATED — espelha o que a publicação incorporará.
    """
    scale = _load_scale(db, scale_id)
    if not scale:
        raise PublishPipelineError("Escala não encontrada")

    errors = _collect_pipeline_errors(db, scale)
    if errors:
        raise PublishPipelineError(" | ".join(errors))

    dejem_blocks = dejem_map.build_map_blocks(
        db,
        scale.scale_date,
        statuses={
            DejemShiftStatus.CLOSED,
            DejemShiftStatus.READY_FOR_MAP,
            DejemShiftStatus.INTEGRATED,
        },
    )
    now = datetime.now(tz=_BR)
    snapshot = _build_snapshot(scale, dejem_blocks, actor=actor, published_at=now)
    if description_override is not None:
        snapshot["description"] = description_override

    from services.scale_message_service import get_default_template
    from services.message_generation_service import MessageGenerationService

    tpl = get_default_template(db)
    body = tpl.body_text if tpl else None
    text = MessageGenerationService(body).render_from_snapshot(snapshot)
    return {
        "text": text,
        "fardamento": snapshot.get("fardamento"),
        "description": snapshot.get("description"),
        "team_count": len(snapshot.get("teams") or []),
        "dejem_count": len(snapshot.get("dejem_blocks") or []),
        "titulo": snapshot.get("organizational_unit"),
    }


def run_publish_pipeline(db: Session, scale_id: int, actor: User) -> ServiceScale:
    """Executa o pipeline completo e retorna a escala publicada."""
    scale = _load_scale(db, scale_id)
    if not scale:
        raise PublishPipelineError("Escala não encontrada")

    errors = _collect_pipeline_errors(db, scale)
    if errors:
        raise PublishPipelineError(" | ".join(errors))

    # 2–3) Buscar DEJEM CLOSED/READY e integrar ao mapa
    integrated = dejem_map.integrate_closed_shifts_for_scale(
        db,
        scale_id=scale.id,
        scale_date=scale.scale_date,
        actor=actor,
    )

    # Recarrega para snapshot com DEJEM INTEGRATED
    scale = _load_scale(db, scale_id) or scale
    dejem_blocks = dejem_map.build_map_blocks(
        db, scale.scale_date, statuses={DejemShiftStatus.INTEGRATED}
    )

    # 6) Gerar versão final (snapshot + texto)
    now = datetime.now(tz=_BR)
    version_number = _next_version_number(db, scale.id)
    snapshot = _build_snapshot(scale, dejem_blocks, actor=actor, published_at=now)

    prev = db.scalars(
        select(ServiceScaleVersion)
        .where(ServiceScaleVersion.service_scale_id == scale.id)
        .order_by(ServiceScaleVersion.version_number.desc())
        .limit(1)
    ).first()
    change_summary = _diff_summaries(
        prev.snapshot_json if prev else None,
        snapshot,
    )

    from models.service_scale import ScaleStatus
    from services.message_generation_service import MessageGenerationService
    from services.scale_message_service import get_default_template

    scale.status = ScaleStatus.PUBLISHED
    scale.published_at = now
    db.add(scale)
    db.flush()

    tpl = get_default_template(db)
    body = tpl.body_text if tpl else None
    export_text = MessageGenerationService(body).render_from_snapshot(snapshot)

    version = ServiceScaleVersion(
        service_scale_id=scale.id,
        version_number=version_number,
        published_at=now,
        published_by_id=actor.id,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        export_text=export_text,
        change_summary=change_summary,
        dejem_integrated_count=integrated,
    )
    db.add(version)
    db.flush()
    scale.current_version_id = version.id
    db.add(scale)

    # 7) Auditoria
    _append_scale_log(
        db,
        scale_id=scale.id,
        actor_id=actor.id,
        action=ScaleLogAction.PUBLISHED,
        description=(
            f"Escala publicada (versão {version_number}): {scale.title}. "
            f"{change_summary}"
        ),
    )
    _append_scale_log(
        db,
        scale_id=scale.id,
        actor_id=actor.id,
        action=ScaleLogAction.VERSION_CREATED,
        description=(
            f"Versão {version_number} gerada. "
            f"DEJEM integradas: {integrated}. {change_summary}"
        ),
    )
    if integrated:
        _append_scale_log(
            db,
            scale_id=scale.id,
            actor_id=actor.id,
            action=ScaleLogAction.DEJEM_INTEGRATED,
            description=f"{integrated} escala(s) DEJEM incorporada(s) ao Mapa Força",
        )

    db.commit()
    return _load_scale(db, scale_id) or scale


def _inject_version_line(export_text: str, version_number: int, published_at: datetime) -> str:
    local = published_at.astimezone(_BR)
    stamp = (
        f"Versão {version_number} · "
        f"{local.day:02d}/{local.month:02d}/{local.year} "
        f"{local.hour:02d}:{local.minute:02d}"
    )
    lines = export_text.splitlines()
    # Após o bloco de fardamento (QTR global foi removido do template).
    for i, line in enumerate(lines):
        upper = line.upper()
        if "FARDAMENTO" in upper:
            # Insere após a linha do valor do fardamento (próxima não vazia) ou logo abaixo.
            insert_at = i + 1
            while insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            if insert_at < len(lines) and "━" not in lines[insert_at] and "EQUIPE" not in lines[insert_at].upper():
                insert_at += 1
            lines.insert(insert_at, stamp)
            break
    else:
        lines.insert(0, stamp)
    return "\n".join(lines)


def list_versions(db: Session, scale_id: int) -> list[ServiceScaleVersion]:
    from sqlalchemy.orm import joinedload

    return list(
        db.scalars(
            select(ServiceScaleVersion)
            .options(joinedload(ServiceScaleVersion.published_by))
            .where(ServiceScaleVersion.service_scale_id == scale_id)
            .order_by(ServiceScaleVersion.version_number.desc())
        ).unique().all()
    )


def get_version(db: Session, scale_id: int, version_number: int) -> ServiceScaleVersion | None:
    from sqlalchemy.orm import joinedload

    return db.scalars(
        select(ServiceScaleVersion)
        .options(joinedload(ServiceScaleVersion.published_by))
        .where(
            ServiceScaleVersion.service_scale_id == scale_id,
            ServiceScaleVersion.version_number == version_number,
        )
    ).unique().first()
