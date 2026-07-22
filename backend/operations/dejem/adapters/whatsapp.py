"""Adapter WhatsApp — interface apenas (C10). Não envia mensagens."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WhatsAppMessageDraft:
    """Rascunho preparado para envio futuro."""

    channel: str
    recipient: str | None
    body: str
    metadata: dict[str, Any]


class WhatsAppAdapter(ABC):
    """Contrato de integração WhatsApp (sem implementação de envio nesta sprint)."""

    @abstractmethod
    def prepare_operational_message(
        self,
        *,
        campaign_id: int,
        version: int,
        body: str,
        recipient: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WhatsAppMessageDraft:
        ...

    @abstractmethod
    def send(self, draft: WhatsAppMessageDraft) -> None:
        """Envio real — fora do escopo C10."""
        ...


class NoOpWhatsAppAdapter(WhatsAppAdapter):
    """Adapter padrão: prepara draft; send() é no-op documentado."""

    def prepare_operational_message(
        self,
        *,
        campaign_id: int,
        version: int,
        body: str,
        recipient: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> WhatsAppMessageDraft:
        meta = dict(metadata or {})
        meta.update({"campaign_id": campaign_id, "version": version, "prepared": True})
        return WhatsAppMessageDraft(
            channel="whatsapp",
            recipient=recipient,
            body=body,
            metadata=meta,
        )

    def send(self, draft: WhatsAppMessageDraft) -> None:
        # C10: não envia. C11+ poderá integrar provedor real.
        raise NotImplementedError(
            "Envio WhatsApp não implementado nesta sprint. "
            "Use prepare_operational_message() e integre o provedor depois."
        )


def get_whatsapp_adapter() -> WhatsAppAdapter:
    return NoOpWhatsAppAdapter()
