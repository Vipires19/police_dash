"""Compat layer — geração via MessageGenerationService (fase 4.9)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from models.service_scale import ScaleMessageTemplate, ScaleStatus, ServiceScale
from models.user import User
from services.message_generation_service import (
    DEFAULT_TEMPLATE_BODY,
    MessageChannel,
    MessageGenerationService,
    apply_template,
    format_date_var,
    format_qtr_var,
    mission_sort_key,
    resolve_operational_title,
)
from sqlalchemy import select

# Re-exports para testes / imports legados
__all__ = [
    "DEFAULT_TEMPLATE_BODY",
    "MessageChannel",
    "MessageGenerationService",
    "apply_template",
    "format_date_var",
    "format_qtr_var",
    "get_default_template",
    "mission_sort_key",
    "render_operational_message",
    "resolve_operational_title",
    "title_for_scale",
]


def get_default_template(db: Session) -> ScaleMessageTemplate | None:
    row = db.scalars(
        select(ScaleMessageTemplate)
        .where(
            ScaleMessageTemplate.is_active.is_(True),
            ScaleMessageTemplate.is_default.is_(True),
        )
        .limit(1)
    ).first()
    if row:
        return row
    return db.scalars(
        select(ScaleMessageTemplate)
        .where(ScaleMessageTemplate.is_active.is_(True))
        .order_by(ScaleMessageTemplate.id.asc())
        .limit(1)
    ).first()


def title_for_scale(scale: ServiceScale, actor: User | None = None) -> str:
    user = actor
    if user is None and scale.current_version is not None:
        user = scale.current_version.published_by
    if user is None and scale.created_by is not None:
        user = scale.created_by
    unit = getattr(user, "organizational_unit", None) if user else None
    return resolve_operational_title(unit)


def render_operational_message(
    db: Session,
    scale: ServiceScale,
    *,
    actor: User | None = None,
    template: ScaleMessageTemplate | None = None,
) -> str:
    """Somente a partir do snapshot congelado da versão corrente."""
    if scale.status != ScaleStatus.PUBLISHED:
        msg = "Somente escalas publicadas podem ser exportadas"
        raise ValueError(msg)
    version = scale.current_version
    if version is None or not version.export_text:
        msg = "Publicação sem mensagem congelada no histórico"
        raise ValueError(msg)
    # Nunca regenera: histórico imutável
    return version.export_text
