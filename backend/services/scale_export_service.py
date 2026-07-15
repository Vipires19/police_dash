"""Formatação / exportação — consome apenas texto congelado da publicação."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from models.service_scale import ServiceScale
from models.user import User
from services.message_generation_service import MessageGenerationService
from services.scale_message_service import get_default_template
from services.service_scale_service import _load_scale


def format_published_scale(
    db: Session,
    scale: ServiceScale,
    *,
    actor: User | None = None,
) -> str:
    """Compat: preferir texto da versão; senão renderizar do snapshot da versão."""
    _ = actor
    version = scale.current_version
    if version is not None and version.export_text:
        return version.export_text
    if version is not None and version.snapshot_json:
        try:
            snapshot = json.loads(version.snapshot_json)
        except json.JSONDecodeError as e:
            raise ValueError("Snapshot da publicação ilegível") from e
        tpl = get_default_template(db)
        body = tpl.body_text if tpl else None
        return MessageGenerationService(body).render_from_snapshot(snapshot)
    msg = "Publicação sem histórico de mensagem"
    raise ValueError(msg)


def build_export_text(db: Session, scale_id: int) -> str:
    scale = _load_scale(db, scale_id)
    if not scale:
        msg = "Escala não encontrada"
        raise ValueError(msg)
    if scale.current_version is not None and scale.current_version.export_text:
        return scale.current_version.export_text
    return format_published_scale(db, scale)
