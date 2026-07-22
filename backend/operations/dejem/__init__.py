"""
Fundação do domínio DEJEM (operations/dejem).

Camada de evolução DDD-lite sobre o módulo DEJEM já em produção.
Não substitui a API `/dejem`.
"""

from operations.dejem.models.enums import CampaignStatus, CreditStatus, OfferEventType

__all__ = [
    "CampaignStatus",
    "CreditStatus",
    "OfferEventType",
]
