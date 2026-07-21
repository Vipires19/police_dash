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
from schemas.service_scale import sort_members_by_role

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

DEFAULT_TEMPLATE_BODY = """*💀 ESCALA DE SERVIÇO 💀*

*{{titulo}}*

*📅 {{data}}*

*👕 Fardamento*

{{fardamento}}

━━━━━━━━━━━━━━━━━━━━━━
{{equipes}}
━━━━━━━━━━━━━━━━━━━━━━
*📢 MISSÕES*
*{{observacoes}}*
"""

_ICON_FT = "🚔"
_ICON_ROCAM = "🏍️"

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

    # Templates persistidos ainda podem trazer o rótulo legado.
    normalized_body = body.replace("*📢 OBSERVAÇÕES*", "*📢 MISSÕES*")
    text = _PLACEHOLDER_RE.sub(repl, normalized_body)
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
    # Remove separador final se missões vazias deixaram bloco órfão
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


def _normalize_hhmm(value: Any) -> str | None:
    """Normaliza '06:00', '06:00:00', time ou datetime ISO → 'HH:MM'."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        from zoneinfo import ZoneInfo

        local = value
        if local.tzinfo is not None:
            local = local.astimezone(ZoneInfo("America/Sao_Paulo"))
        return f"{local.hour:02d}:{local.minute:02d}"
    if hasattr(value, "hour") and hasattr(value, "minute") and not isinstance(value, str):
        return f"{int(value.hour):02d}:{int(value.minute):02d}"
    text = str(value).strip()
    if "T" in text:
        try:
            return _normalize_hhmm(datetime.fromisoformat(text.replace("Z", "+00:00")))
        except ValueError:
            return None
    parts = text.split(":")
    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return None


def resolve_team_qtr(entity: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extrai horário operacional da equipe/DEJEM a partir do snapshot.

    Preferência: start_time/end_time → start_datetime/end_datetime.
    Nunca usa published_at da escala.
    """
    start = _normalize_hhmm(entity.get("start_time"))
    end = _normalize_hhmm(entity.get("end_time"))
    if start and end:
        return start, end
    start = start or _normalize_hhmm(entity.get("start_datetime") or entity.get("start_at"))
    end = end or _normalize_hhmm(entity.get("end_datetime") or entity.get("end_at"))
    if start and end:
        return start, end
    return None, None


def format_qtr_var(published_at: datetime | str | None) -> str:
    """Legado: não usar para QTR de equipe. Preferir resolve_team_qtr."""
    _ = published_at
    return "—"


def format_patente(patente: str) -> str:
    """Normaliza patente para o padrão PM (mantém ordinal e espaços: 1º TEN)."""
    raw = (patente or "").strip().upper()
    raw = raw.replace("°", "º")
    return re.sub(r"\s+", " ", raw)


def member_line(member: dict[str, Any], *, with_assigned_vehicle: bool = False) -> str:
    """Linha do policial no padrão PM: <PATENTE> PM <RE> <NOME_GUERRA>.

    Consome exclusivamente campos do snapshot (nunca consulta users).
    Com `with_assigned_vehicle=True` (ROCAM): anexa a moto do membro.
    """
    patente = format_patente(str(member.get("patente") or ""))
    re_num = str(member.get("re") or "").strip()
    nome = (member.get("nome_guerra") or "").strip().upper()

    parts: list[str] = []
    if patente:
        parts.append(patente)
    parts.append("PM")
    if re_num:
        parts.append(re_num)
    if nome:
        parts.append(nome)
    base = " ".join(parts)
    if not with_assigned_vehicle:
        return base
    prefix = str(member.get("assigned_vehicle_prefixo") or "").strip()
    if prefix:
        return f"{base} - {prefix}"
    return f"{base} - {_VEHICLE_MISSING}"


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


def format_team_mission_notes(notes: str | None) -> list[str]:
    """Bloco 📌 Missão da equipe. Vazio → nada (sem linhas em branco)."""
    bullets = format_observacoes(notes)
    if not bullets:
        return []
    return ["*📌 Missão*", "", *bullets.splitlines()]


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
    """Viatura da equipe (FT / Supervisor / DEJEM). Não usa moto por membro."""
    prefix = team.get("vehicle_prefixo")
    return str(prefix).strip() if prefix else None


def _modality_icon(modality: str) -> str:
    if (modality or "").upper() == "ROCAM":
        return _ICON_ROCAM
    return _ICON_FT


def _strip_dejem_origin_noise(label: str) -> str:
    """Remove ruído de origem/legado do título do snapshot (DEJEM, EXTRA)."""
    text = (label or "").strip().upper()
    text = re.sub(r"\s+", " ", text)
    changed = True
    while changed and text:
        changed = False
        for suffix in (" DEJEM", " EXTRA", " FT EXTRA"):
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                changed = True
    if text in {"DEJEM", "EXTRA", "FT EXTRA", "FT"}:
        return ""
    return text


def resolve_dejem_modality(block: dict[str, Any]) -> str:
    """Modalidade operacional da equipe DEJEM (sem sufixo de origem).

    DEJEM é origem, não modalidade. Fonte: `shift_type` e `title` do snapshot.
    `shift_type` FT/ROCAM prevalece sobre títulos legados (ex.: APOIO TÁTICO / ROCAM EXTRA).
    """
    shift_type = str(block.get("shift_type") or "").strip().upper()
    title = str(block.get("title") or "").strip()
    core = _fold(_strip_dejem_origin_noise(title))

    if shift_type == "ROCAM" or core.startswith("rocam") or core == "rocam":
        return "ROCAM"
    if shift_type == "FT":
        return "FORÇA TÁTICA"
    if "supervisor" in core:
        return "SUPERVISOR TÁTICO"
    if "tatico comando" in core:
        return "TÁTICO COMANDO"
    if "apoio tatico" in core:
        return "APOIO TÁTICO"
    if "forca tatica" in core:
        return "FORÇA TÁTICA"

    cleaned = _strip_dejem_origin_noise(title)
    if cleaned:
        return cleaned
    # OUTROS / título legado «DEJEM»: modalidade padrão da companhia.
    return "FORÇA TÁTICA"


def resolve_dejem_display(block: dict[str, Any]) -> tuple[str, str]:
    """Ícone + rótulo `<MODALIDADE> DEJEM` só na renderização.

    Blocos em `dejem_blocks` têm origem DEJEM no snapshot; o sufixo é sempre
    acrescentado. Não altera o snapshot.
    """
    modality = resolve_dejem_modality(block)
    icon = _modality_icon(modality)
    return icon, f"{modality} DEJEM"


def _append_qtr_and_members(
    lines: list[str],
    *,
    start: str | None,
    end: str | None,
    members: list[dict[str, Any]],
    with_assigned_vehicle: bool,
    notes: str | None = None,
) -> None:
    if start and end:
        lines.append(f"*🕘 QTR* Das {start} às {end}")
    lines.append("")
    for m in members:
        line = member_line(m, with_assigned_vehicle=with_assigned_vehicle)
        if line:
            lines.append(line)
    mission_block = format_team_mission_notes(notes)
    if mission_block:
        lines.append("")
        lines.extend(mission_block)
        lines.append("")
    lines.append(_TEAM_SEPARATOR)
    lines.append("")


class StandardTeamBlockStrategy:
    """Renderização padrão: uma viatura da equipe + linhas sem moto individual."""

    def render(
        self,
        *,
        label: str,
        start: str | None,
        end: str | None,
        members: list[dict[str, Any]],
        team: dict[str, Any],
        icon: str = _ICON_FT,
    ) -> list[str]:
        vehicle = _team_vehicle_prefixo(team)
        lines = [
            f"*{icon} {label}*",
            f"*{vehicle if vehicle else _VEHICLE_MISSING}*",
        ]
        _append_qtr_and_members(
            lines,
            start=start,
            end=end,
            members=members,
            with_assigned_vehicle=False,
            notes=team.get("notes"),
        )
        return lines


class RocamTeamBlockStrategy:
    """ROCAM: sem viatura da equipe; cada policial exibe a própria moto."""

    def render(
        self,
        *,
        label: str,
        start: str | None,
        end: str | None,
        members: list[dict[str, Any]],
        team: dict[str, Any],
        icon: str = _ICON_ROCAM,
    ) -> list[str]:
        lines = [f"*{icon} {label}*"]
        _append_qtr_and_members(
            lines,
            start=start,
            end=end,
            members=members,
            with_assigned_vehicle=True,
            notes=team.get("notes"),
        )
        return lines


def get_team_block_strategy(modality: str) -> StandardTeamBlockStrategy | RocamTeamBlockStrategy:
    if (modality or "").upper() == "ROCAM":
        return RocamTeamBlockStrategy()
    return StandardTeamBlockStrategy()


def _format_team_block(
    *,
    label: str,
    vehicle: str | None,
    start: str | None,
    end: str | None,
    members: list[dict[str, Any]],
    icon: str = _ICON_FT,
    notes: str | None = None,
) -> list[str]:
    """Compat: blocos DEJEM e chamadas legadas (estratégia padrão)."""
    return StandardTeamBlockStrategy().render(
        label=label,
        start=start,
        end=end,
        members=members,
        team={"vehicle_prefixo": vehicle, "notes": notes},
        icon=icon,
    )


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
        if modality == "ROCAM" and not mission.startswith("ROCAM"):
            mission = f"ROCAM {mission}"
        members = list(team.get("members") or [])
        members = sort_members_by_role(modality, members)
        start, end = resolve_team_qtr(team)
        strategy = get_team_block_strategy(modality)
        lines.extend(
            strategy.render(
                label=mission,
                start=start,
                end=end,
                members=members,
                team=team,
                icon=_modality_icon(modality),
            )
        )

    for block in snapshot.get("dejem_blocks") or []:
        icon, label = resolve_dejem_display(block)
        members = list(block.get("members") or [])
        members.sort(
            key=lambda m: (
                int(m.get("display_order") or 0),
                str(m.get("nome_guerra") or "").lower(),
            )
        )
        vehicle = block.get("vehicle_prefixo")
        start, end = resolve_team_qtr(block)
        notes = block.get("notes")
        lines.extend(
            _format_team_block(
                label=label,
                vehicle=str(vehicle).strip() if vehicle else None,
                start=start,
                end=end,
                members=members,
                icon=icon,
                notes=str(notes) if notes else None,
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
        # QTR global removido: cada equipe/DEJEM exibe o próprio horário no bloco {{equipes}}.
        "qtr": "",
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
