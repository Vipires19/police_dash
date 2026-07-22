"""Mapeamento padronizado DomainError → HTTPException (R1).

Não altera contratos públicos; apenas unifica status/mensagens.
"""

from __future__ import annotations

from fastapi import HTTPException, status


def domain_http_error(exc: Exception) -> HTTPException:
    """Traduz erros de domínio DEJEM para HTTP sem mudar `detail` textual."""
    msg = str(exc)
    lower = msg.lower()
    code = status.HTTP_400_BAD_REQUEST
    if "não encontrad" in lower:
        code = status.HTTP_404_NOT_FOUND
    elif (
        "sem permissão" in lower
        or "somente o policial" in lower
        or "somente o titular" in lower
    ):
        code = status.HTTP_403_FORBIDDEN
    return HTTPException(status_code=code, detail=msg)
