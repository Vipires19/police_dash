"""Adapters do domínio DEJEM (Mapa Força, WhatsApp, …)."""

from operations.dejem.adapters.mapa_force import build_mapa_force_payload
from operations.dejem.adapters.whatsapp import (
    NoOpWhatsAppAdapter,
    WhatsAppAdapter,
    WhatsAppMessageDraft,
    get_whatsapp_adapter,
)

__all__ = [
    "NoOpWhatsAppAdapter",
    "WhatsAppAdapter",
    "WhatsAppMessageDraft",
    "build_mapa_force_payload",
    "get_whatsapp_adapter",
]
