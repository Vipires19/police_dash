"""Testes do MessageGenerationService — horários por equipe a partir do snapshot."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from models.user import OrganizationalUnit
from services.message_generation_service import (
    DEFAULT_TEMPLATE_BODY,
    MessageChannel,
    MessageGenerationService,
    apply_template,
    build_equipes_from_snapshot,
    format_date_var,
    format_observacoes,
    format_qtr_var,
    member_line,
    mission_sort_key,
    resolve_operational_title,
    resolve_team_qtr,
)
from services.scale_publish_pipeline import _hhmm_from_datetime, _normalize_dejem_block

_BR = ZoneInfo("America/Sao_Paulo")


def test_titles_by_organizational_unit():
    assert resolve_operational_title(OrganizationalUnit.FIRST_PLATOON) == (
        "1º PELOTÃO DE FORÇA TÁTICA"
    )
    assert resolve_operational_title(OrganizationalUnit.SECOND_PLATOON) == (
        "2º PELOTÃO DE FORÇA TÁTICA"
    )
    assert resolve_operational_title(OrganizationalUnit.COMPANY_ADMIN) == (
        "COMPANHIA DE FORÇA TÁTICA"
    )


def test_mission_sort_order():
    keys = [
        mission_sort_key("ROCAM 1", "ROCAM"),
        mission_sort_key("Força Tática", "FT"),
        mission_sort_key("Tático Comando", "FT"),
        mission_sort_key("Escolta especial", "FT"),
        mission_sort_key("Supervisor Tático", "FT"),
    ]
    ordered = sorted(keys)
    assert ordered[0][0] == 0
    assert ordered[1][0] == 1
    assert ordered[2][0] == 2
    assert ordered[3][0] == 2
    assert ordered[4][0] == 3


def test_member_line_compact_patente():
    assert member_line({"patente": "1° TEN", "nome_guerra": "Carvalho"}) == "1TEN CARVALHO"
    assert member_line({"patente": "CB", "nome_guerra": "Angelo"}) == "CB ANGELO"
    assert (
        member_line({"patente": "CB", "re": "123456", "nome_guerra": "Angelo"})
        == "CB RE 123456 ANGELO"
    )


def test_resolve_team_qtr_prefers_start_end_time():
    start, end = resolve_team_qtr(
        {
            "start_time": "04:55",
            "end_time": "12:55",
            "start_datetime": "2026-07-14T06:00:00-03:00",
            "end_datetime": "2026-07-14T18:00:00-03:00",
            "published_at": "2026-07-14T22:00:00-03:00",
        }
    )
    assert start == "04:55"
    assert end == "12:55"


def test_resolve_team_qtr_falls_back_to_datetime():
    start, end = resolve_team_qtr(
        {
            "start_datetime": "2026-07-14T06:00:00-03:00",
            "end_datetime": "2026-07-14T18:00:00-03:00",
        }
    )
    assert start == "06:00"
    assert end == "18:00"


def test_resolve_team_qtr_never_uses_published_at():
    start, end = resolve_team_qtr({"published_at": "2026-07-14T22:00:00-03:00"})
    assert start is None
    assert end is None


def test_equipes_format_independent_qtr_per_team():
    snapshot = {
        "teams": [
            {
                "id": 2,
                "modality": "ROCAM",
                "mission_name": "ROCAM 1",
                "vehicle_prefixo": None,
                "start_time": "04:55",
                "end_time": "12:55",
                "start_datetime": "2026-07-14T04:55:00-03:00",
                "members": [
                    {
                        "patente": "CB",
                        "nome_guerra": "João",
                        "assigned_vehicle_prefixo": "I-03045",
                        "display_order": 1,
                    },
                ],
            },
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Tático Comando",
                "vehicle_prefixo": "I-03027",
                "start_time": "06:00",
                "end_time": "18:00",
                "start_datetime": "2026-07-14T06:00:00-03:00",
                "members": [
                    {"patente": "1° TEN", "nome_guerra": "Carvalho", "display_order": 1},
                ],
            },
        ],
        "dejem_blocks": [
            {
                "shift_id": 9,
                "title": "APOIO TÁTICO",
                "vehicle_prefixo": "I-03061",
                "start_time": "18:00",
                "end_time": "06:00",
                "members": [
                    {"patente": "CB", "nome_guerra": "Felipe", "display_order": 1},
                ],
            }
        ],
    }
    block = build_equipes_from_snapshot(snapshot)
    assert block.index("TÁTICO COMANDO") < block.index("ROCAM 1")
    assert block.index("ROCAM 1") < block.index("APOIO TÁTICO")
    assert "*🚔 APOIO TÁTICO*" in block
    assert "*I-03061*" in block
    assert "*🕘 QTR* Das 06:00 às 18:00" in block
    assert "*🕘 QTR* Das 04:55 às 12:55" in block
    assert "*🕘 QTR* Das 18:00 às 06:00" in block
    assert "22:00" not in block  # não usa horário de publicação
    assert "I-03027" in block
    assert "1TEN CARVALHO" in block


def test_render_has_no_global_qtr_block():
    snapshot = {
        "scale_id": 1,
        "scale_date": "2026-07-16",
        "organizational_unit": OrganizationalUnit.FIRST_PLATOON.value,
        "fardamento": "5º Uniforme",
        "published_at": datetime(2026, 7, 16, 22, 0, tzinfo=_BR).isoformat(),
        "description": None,
        "teams": [],
        "dejem_blocks": [
            {
                "shift_id": 1,
                "title": "APOIO TÁTICO",
                "vehicle_prefixo": "I-03024",
                "start_time": "04:55",
                "end_time": "12:55",
                "members": [
                    {"patente": "CB", "nome_guerra": "Silva", "display_order": 1},
                ],
            }
        ],
    }
    text = MessageGenerationService(DEFAULT_TEMPLATE_BODY).render_from_snapshot(snapshot)
    fard_idx = text.index("5º Uniforme")
    team_idx = text.index("*🚔 APOIO TÁTICO*")
    between = text[fard_idx:team_idx]
    assert "QTR" not in between
    assert text.count("*🕘 QTR*") == 1
    assert "*I-03024*" in text
    assert "*🕘 QTR* Das 04:55 às 12:55" in text


def test_missing_vehicle_warning():
    snapshot = {
        "teams": [
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Supervisor Tático",
                "vehicle_prefixo": None,
                "start_time": "06:00",
                "end_time": "18:00",
                "members": [{"patente": "SGT", "nome_guerra": "X", "display_order": 0}],
            }
        ],
        "dejem_blocks": [],
    }
    text = build_equipes_from_snapshot(snapshot)
    assert "⚠ Viatura não definida" in text
    assert "*🕘 QTR* Das 06:00 às 18:00" in text


def test_observacoes_bullets():
    assert format_observacoes("Apoio\nQAP às 08:30") == "• Apoio\n• QAP às 08:30"
    assert format_observacoes(None) == ""


def test_render_from_snapshot_full_message():
    snapshot = {
        "scale_id": 1,
        "scale_date": "2026-07-14",
        "organizational_unit": OrganizationalUnit.FIRST_PLATOON.value,
        "fardamento": "5º Uniforme",
        "published_at": datetime(2026, 7, 14, 22, 0, tzinfo=_BR).isoformat(),
        "description": "Reforço ROCAM.",
        "teams": [
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Tático Comando",
                "vehicle_prefixo": "I-03027",
                "start_time": "06:00",
                "end_time": "18:00",
                "members": [
                    {"patente": "CB", "nome_guerra": "Angelo", "display_order": 1},
                ],
            }
        ],
        "dejem_blocks": [],
    }
    text = MessageGenerationService(DEFAULT_TEMPLATE_BODY).render_from_snapshot(snapshot)
    assert "💀 ESCALA DE SERVIÇO 💀" in text
    assert "1º PELOTÃO DE FORÇA TÁTICA" in text
    assert "📅 Dia 14 de Julho de 2026" in text
    assert "👕 Fardamento" in text
    assert "5º Uniforme" in text
    assert "*🕘 QTR* Das 06:00 às 18:00" in text
    assert "22:00" not in text
    assert "🚔 TÁTICO COMANDO" in text
    assert "• Reforço ROCAM." in text
    assert "{{" not in text
    assert "Folga" not in text


def test_channel_payload_envelope():
    snapshot = {
        "scale_id": 7,
        "scale_date": "2026-07-14",
        "organizational_unit": "FIRST_PLATOON",
        "teams": [],
        "dejem_blocks": [],
        "published_at": None,
        "fardamento": None,
        "description": None,
    }
    payload = MessageGenerationService().render_channel_payload(
        snapshot, channel=MessageChannel.TELEGRAM
    )
    assert payload["channel"] == "telegram"
    assert payload["format"] == "text/plain"
    assert "💀 ESCALA DE SERVIÇO 💀" in payload["text"]


def test_apply_template_basic():
    text = apply_template(
        DEFAULT_TEMPLATE_BODY,
        {
            "titulo": "COMPANHIA DE FORÇA TÁTICA",
            "data": format_date_var(date(2026, 7, 14)),
            "fardamento": "—",
            "qtr": format_qtr_var(None),
            "equipes": "🚔 FT",
            "observacoes": "",
        },
    )
    assert "COMPANHIA DE FORÇA TÁTICA" in text
    assert "🚔 FT" in text


def test_snapshot_hhmm_helpers():
    assert _hhmm_from_datetime(datetime(2026, 7, 14, 4, 55, tzinfo=_BR)) == "04:55"
    block = _normalize_dejem_block(
        {"title": "APOIO", "start_time": "18:00:00", "end_time": "06:00:00"}
    )
    assert block["start_time"] == "18:00"
    assert block["end_time"] == "06:00"
