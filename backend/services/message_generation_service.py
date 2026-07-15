"""Geração inteligente da mensagem operacional (fase 4.9).

Fonte única de verdade: o snapshot da publicação.
Nunca consulta folgas, férias, efetivo ou outras tabelas operacionais.
"""

from __future__ import annotations

import enum
import re
import unicodedata
from datetime import date, datetime
from typing import Any

from models.user import OrganizationalUnit

_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")

_MONTHS_PT = (
    "",
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)

DEFAULT_TEMPLATE_BODY = """💀 ESCALA DE SERVIÇO 💀

{{titulo}}

📅 {{data}}

👕 Fardamento

{{fardamento}}

🕘 QTR

{{qtr}}

━━━━━━━━━━━━━━━━━━━━━━
{{equipes}}
━━━━━━━━━━━━━━━━━━━━━━
{{observacoes}}
"""

_UNIT_TITLES: dict[str, str] = {
    OrganizationalUnit.FIRST_PLATOON.value: "1º PELOTÃO DE FORÇA TÁTICA",
    OrganizationalUnit.SECOND_PLATOON.value: "2º PELOTÃO DE FORÇA TÁTICA",
    OrganizationalUnit.COMPANY_ADMIN.value: "COMPANHIA DE FORÇA TÁTICA",
}

_ORDER_TATICO = 0
_ORDER_SUPERVISOR = 1
_ORDER_FT = 2
_ORDER_ROCAM = 3
_ORDER_DEJEM = 4
_ORDER_OUTRAS = 5

_TEAM_SEPARATOR = "----------------------------"
_VEHICLE_MISSING = "⚠ Viatura não definida"


class MessageChannel(str, enum.Enum):
    """Canais de saída futuros (mesmo template / snapshot)."""

    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    PDF = "pdf"
    PRINT = "print"
    EMAIL = "email"


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def resolve_operational_title(unit: OrganizationalUnit | str | None) -> str:
    if unit is None:
        return _UNIT_TITLES[OrganizationalUnit.FIRST_PLATOON.value]
    key = unit.value if isinstance(unit, OrganizationalUnit) else str(unit)
    return _UNIT_TITLES.get(key, _UNIT_TITLES[OrganizationalUnit.FIRST_PLATOON.value])


def apply_template(body: str, variables: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        return variables.get(match.group(1), "")

    text = _PLACEHOLDER_RE.sub(repl, body)
    out: list[str] = []
    blank_run = 0
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped == "":
            blank_run += 1
            if blank_run <= 1:
                out.append("")
        else:
            blank_run = 0
            out.append(stripped)
    while out and out[-1] == "":
        out.pop()
    # Remove separador final se observações vazias deixaram bloco órfão
    while out and out[-1].startswith("━"):
        out.pop()
        while out and out[-1] == "":
            out.pop()
    return "\n".join(out)


def format_date_var(scale_date: date | str) -> str:
    if isinstance(scale_date, str):
        scale_date = date.fromisoformat(scale_date[:10])
    month = _MONTHS_PT[scale_date.month]
    return f"Dia {scale_date.day:02d} de {month} de {scale_date.year}"


def format_qtr_var(published_at: datetime | str | None) -> str:
    if published_at is None or published_at == "":
        return "—"
    if isinstance(published_at, str):
        published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    local = published_at
    if local.tzinfo is not None:
        from zoneinfo import ZoneInfo

        local = local.astimezone(ZoneInfo("America/Sao_Paulo"))
    return f"{local.hour:02d}:{local.minute:02d}hs"


def format_patente(patente: str) -> str:
    raw = (patente or "").upper().replace("°", "").replace("º", "").replace(".", "")
    return re.sub(r"\s+", "", raw)


def member_line(patente: str, nome_guerra: str) -> str:
    name = (nome_guerra or "").strip().upper()
    return f"{format_patente(patente)} {name}".strip()


def format_observacoes(description: str | None) -> str:
    raw = (description or "").strip()
    if not raw:
        return ""
    bullets: list[str] = []
    for ln in raw.splitlines():
        item = ln.strip()
        if not item:
            continue
        if item.startswith("•"):
            bullets.append(item)
        elif item.startswith("-"):
            bullets.append(f"• {item.lstrip('-').strip()}")
        else:
            bullets.append(f"• {item}")
    return "\n".join(bullets)


def mission_sort_key(mission_name: str, modality: str) -> tuple[int, str]:
    folded = _fold(mission_name.strip())
    mod = (modality or "").upper()
    if "tatico comando" in folded:
        return (_ORDER_TATICO, folded)
    if "supervisor" in folded:
        return (_ORDER_SUPERVISOR, folded)
    if mod == "ROCAM" or folded.startswith("rocam"):
        return (_ORDER_ROCAM, folded)
    if "forca tatica" in folded:
        return (_ORDER_FT, folded)
    if mod == "FT":
        return (_ORDER_FT, folded)
    return (_ORDER_OUTRAS, folded)


def _team_vehicle_prefixo(team: dict[str, Any]) -> str | None:
    prefix = team.get("vehicle_prefixo")
    if prefix:
        return str(prefix)
    for m in team.get("members") or []:
        p = m.get("assigned_vehicle_prefixo")
        if p:
            return str(p)
    return None


def _format_team_block(*, label: str, vehicle: str | None, members: list[dict[str, Any]]) -> list[str]:
    lines = [
        f"🚔 {label}",
        "Viatura",
        vehicle if vehicle else _VEHICLE_MISSING,
    ]
    for m in members:
        line = member_line(str(m.get("patente") or ""), str(m.get("nome_guerra") or ""))
        if line:
            lines.append(line)
    lines.append(_TEAM_SEPARATOR)
    lines.append("")
    return lines


def build_equipes_from_snapshot(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    teams = list(snapshot.get("teams") or [])
    teams.sort(
        key=lambda t: (
            *mission_sort_key(str(t.get("mission_name") or ""), str(t.get("modality") or "")),
            str(t.get("start_datetime") or ""),
            int(t.get("id") or 0),
        )
    )
    for team in teams:
        mission = str(team.get("mission_name") or "EQUIPE").strip().upper()
        modality = str(team.get("modality") or "").upper()
        # Demais FT e Outras: missão em maiúsculas; ROCAM idem
        if modality == "ROCAM" and not mission.startswith("ROCAM"):
            mission = f"ROCAM {mission}"
        members = list(team.get("members") or [])
        members.sort(
            key=lambda m: (
                int(m.get("display_order") or 0),
                str(m.get("nome_guerra") or "").lower(),
            )
        )
        lines.extend(
            _format_team_block(
                label=mission,
                vehicle=_team_vehicle_prefixo(team),
                members=members,
            )
        )

    for block in snapshot.get("dejem_blocks") or []:
        title = str(block.get("title") or "DEJEM").strip()
        label = title.upper() if title.upper().startswith("DEJEM") else f"DEJEM {title}".upper()
        members = list(block.get("members") or [])
        members.sort(
            key=lambda m: (
                int(m.get("display_order") or 0),
                str(m.get("nome_guerra") or "").lower(),
            )
        )
        vehicle = block.get("vehicle_prefixo")
        lines.extend(
            _format_team_block(
                label=label,
                vehicle=str(vehicle) if vehicle else None,
                members=members,
            )
        )

    while lines and lines[-1] == "":
        lines.pop()
    if lines and lines[-1] == _TEAM_SEPARATOR:
        lines.pop()
    return "\n".join(lines)


def build_variables_from_snapshot(snapshot: dict[str, Any]) -> dict[str, str]:
    unit = snapshot.get("organizational_unit")
    fardamento = (snapshot.get("fardamento") or "").strip() or "—"
    return {
        "titulo": resolve_operational_title(unit),
        "data": format_date_var(snapshot.get("scale_date") or date.today().isoformat()),
        "fardamento": fardamento,
        "qtr": format_qtr_var(snapshot.get("published_at")),
        "equipes": build_equipes_from_snapshot(snapshot),
        "observacoes": format_observacoes(snapshot.get("description")),
    }


class MessageGenerationService:
    """Monta a mensagem operacional exclusivamente a partir do snapshot."""

    def __init__(self, template_body: str | None = None) -> None:
        self.template_body = template_body or DEFAULT_TEMPLATE_BODY

    def render_from_snapshot(
        self,
        snapshot: dict[str, Any],
        *,
        channel: MessageChannel = MessageChannel.WHATSAPP,
        template_body: str | None = None,
    ) -> str:
        # Canais futuros compartilham o mesmo render textual; adapters
        # (PDF/e-mail) consumirão este texto ou o snapshot tipado.
        _ = channel
        body = template_body or self.template_body
        variables = build_variables_from_snapshot(snapshot)
        return apply_template(body, variables)

    def render_channel_payload(
        self,
        snapshot: dict[str, Any],
        *,
        channel: MessageChannel = MessageChannel.WHATSAPP,
        template_body: str | None = None,
    ) -> dict[str, Any]:
        """Envelope multi-canal: mesmo texto + metadados para adapters futuros."""
        text = self.render_from_snapshot(
            snapshot, channel=channel, template_body=template_body
        )
        return {
            "channel": channel.value,
            "format": "text/plain",
            "text": text,
            "snapshot_scale_id": snapshot.get("scale_id"),
            "snapshot_scale_date": snapshot.get("scale_date"),
        }
