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
    format_team_mission_notes,
    member_line,
    mission_sort_key,
    resolve_dejem_display,
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


def test_member_line_pm_format():
    assert (
        member_line({"patente": "1° TEN", "re": "144958-3", "nome_guerra": "Carvalho"})
        == "1º TEN PM 144958-3 CARVALHO"
    )
    assert (
        member_line({"patente": "CB", "re": "110071-8", "nome_guerra": "Ângelo"})
        == "CB PM 110071-8 ÂNGELO"
    )
    assert (
        member_line({"patente": "SD", "re": "155129-9", "nome_guerra": "Zanello"})
        == "SD PM 155129-9 ZANELLO"
    )
    assert (
        member_line({"patente": "SUBTEN", "re": "110170-6", "nome_guerra": "Gesiel"})
        == "SUBTEN PM 110170-6 GESIEL"
    )
    # Sem RE no snapshot: ainda usa PM, sem a palavra "RE"
    assert member_line({"patente": "CB", "nome_guerra": "Angelo"}) == "CB PM ANGELO"
    assert " RE " not in member_line(
        {"patente": "CB", "re": "110071-8", "nome_guerra": "Angelo"}
    )


def test_message_sorts_members_by_role_not_list_order():
    """Ordem da mensagem segue a função, mesmo se a lista do snapshot estiver embaralhada."""
    snapshot = {
        "teams": [
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Tático Comando",
                "vehicle_prefixo": "I-03027",
                "start_time": "13:00",
                "end_time": "00:00",
                "members": [
                    {
                        "patente": "SD",
                        "re": "161173-9",
                        "nome_guerra": "Moretto",
                        "role_label": "4º Homem",
                        "display_order": 1,
                    },
                    {
                        "patente": "1° TEN",
                        "re": "144958-3",
                        "nome_guerra": "Carvalho",
                        "role_label": "Comandante da Equipe",
                        "display_order": 99,
                    },
                    {
                        "patente": "CB",
                        "re": "110071-8",
                        "nome_guerra": "Angelo",
                        "role_label": "Motorista",
                        "display_order": 2,
                    },
                    {
                        "patente": "SD",
                        "re": "153055-A",
                        "nome_guerra": "Martins",
                        "role_label": "3º Homem",
                        "display_order": 3,
                    },
                ],
            }
        ],
        "dejem_blocks": [],
    }
    block = build_equipes_from_snapshot(snapshot)
    carvalho = block.index("1º TEN PM 144958-3 CARVALHO")
    angelo = block.index("CB PM 110071-8 ANGELO")
    martins = block.index("SD PM 153055-A MARTINS")
    moretto = block.index("SD PM 161173-9 MORETTO")
    assert carvalho < angelo < martins < moretto


def test_message_sorts_rocam_by_role():
    snapshot = {
        "teams": [
            {
                "id": 1,
                "modality": "ROCAM",
                "mission_name": "ROCAM 1",
                "start_time": "06:00",
                "end_time": "18:00",
                "members": [
                    {
                        "patente": "SD",
                        "re": "1",
                        "nome_guerra": "C",
                        "role_label": "Moto 3",
                        "assigned_vehicle_prefixo": "I-3",
                        "display_order": 1,
                    },
                    {
                        "patente": "CB",
                        "re": "2",
                        "nome_guerra": "A",
                        "role_label": "Comandante da Equipe",
                        "assigned_vehicle_prefixo": "I-1",
                        "display_order": 9,
                    },
                    {
                        "patente": "SD",
                        "re": "3",
                        "nome_guerra": "B",
                        "role_label": "Moto 2",
                        "assigned_vehicle_prefixo": "I-2",
                        "display_order": 2,
                    },
                ],
            }
        ],
        "dejem_blocks": [],
    }
    block = build_equipes_from_snapshot(snapshot)
    assert block.index("CB PM 2 A") < block.index("SD PM 3 B") < block.index("SD PM 1 C")


def test_normalize_member_roles_legacy_order():
    from schemas.service_scale import ScaleTeamMemberInput, normalize_member_roles

    members = [
        ScaleTeamMemberInput(user_id=10),
        ScaleTeamMemberInput(user_id=20),
        ScaleTeamMemberInput(user_id=30),
    ]
    out = normalize_member_roles("FT", members)
    assert [m.role_label for m in out] == [
        "Comandante da Equipe",
        "Motorista",
        "3º Homem",
    ]


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
                        "re": "110045-1",
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
                    {
                        "patente": "1° TEN",
                        "re": "144958-3",
                        "nome_guerra": "Carvalho",
                        "display_order": 1,
                    },
                ],
            },
        ],
        "dejem_blocks": [
            {
                "shift_id": 9,
                "title": "APOIO TÁTICO",
                "shift_type": "FT",
                "vehicle_prefixo": "I-03061",
                "start_time": "18:00",
                "end_time": "06:00",
                "members": [
                    {
                        "patente": "CB",
                        "re": "110071-8",
                        "nome_guerra": "Felipe",
                        "display_order": 1,
                    },
                ],
            }
        ],
    }
    block = build_equipes_from_snapshot(snapshot)
    assert block.index("TÁTICO COMANDO") < block.index("ROCAM 1")
    assert block.index("ROCAM 1") < block.index("FORÇA TÁTICA DEJEM")
    assert "*🚔 FORÇA TÁTICA DEJEM*" in block
    assert "*🏍️ ROCAM 1*" in block
    assert "*I-03061*" in block
    assert "*🕘 QTR* Das 06:00 às 18:00" in block
    assert "*🕘 QTR* Das 04:55 às 12:55" in block
    assert "*🕘 QTR* Das 18:00 às 06:00" in block
    assert "22:00" not in block  # não usa horário de publicação
    assert "*I-03027*" in block
    assert "1º TEN PM 144958-3 CARVALHO" in block
    # ROCAM: moto na linha do policial, não como viatura da equipe
    assert "CB PM 110045-1 JOÃO - I-03045" in block
    assert "*I-03045*" not in block
    assert "CB PM 110071-8 FELIPE" in block
    assert " RE " not in block


def test_rocam_renders_motorcycle_per_member():
    snapshot = {
        "teams": [
            {
                "id": 1,
                "modality": "ROCAM",
                "mission_name": "ROCAM 1",
                "vehicle_prefixo": None,
                "start_time": "13:00",
                "end_time": "01:00",
                "members": [
                    {
                        "patente": "CB",
                        "re": "141326-A",
                        "nome_guerra": "Broisler",
                        "assigned_vehicle_prefixo": "I-03065-11",
                        "display_order": 1,
                    },
                    {
                        "patente": "SD",
                        "re": "190443-4",
                        "nome_guerra": "Bispo",
                        "assigned_vehicle_prefixo": "I-03066-11",
                        "display_order": 2,
                    },
                    {
                        "patente": "SD",
                        "re": "180961-0",
                        "nome_guerra": "De Paula",
                        "assigned_vehicle_prefixo": "I-03067-11",
                        "display_order": 3,
                    },
                ],
            },
            {
                "id": 2,
                "modality": "FT",
                "mission_name": "Força Tática",
                "vehicle_prefixo": "I-03024",
                "start_time": "13:00",
                "end_time": "01:00",
                "members": [
                    {
                        "patente": "CB",
                        "re": "110071-8",
                        "nome_guerra": "Felipe",
                        "assigned_vehicle_prefixo": "I-99999",
                        "display_order": 1,
                    },
                    {
                        "patente": "SD",
                        "re": "155129-9",
                        "nome_guerra": "Martins",
                        "display_order": 2,
                    },
                ],
            },
        ],
        "dejem_blocks": [],
    }
    block = build_equipes_from_snapshot(snapshot)

    # ROCAM: sem viatura de equipe; moto por policial; ícone 🏍️
    assert "*🏍️ ROCAM 1*" in block
    assert "CB PM 141326-A BROISLER - I-03065-11" in block
    assert "SD PM 190443-4 BISPO - I-03066-11" in block
    assert "SD PM 180961-0 DE PAULA - I-03067-11" in block
    # Não há linha de viatura da equipe com o prefixo da moto
    assert "*I-03065-11*" not in block
    assert "*I-03066-11*" not in block
    assert "*I-03067-11*" not in block

    # FT: uma viatura da equipe; membros sem moto individual
    assert "*🚔 FORÇA TÁTICA*" in block
    assert "*I-03024*" in block
    assert "CB PM 110071-8 FELIPE" in block
    assert "SD PM 155129-9 MARTINS" in block
    assert "I-99999" not in block
    assert "FELIPE - " not in block
    assert "MARTINS - " not in block

    # QTR presente nas duas equipes
    assert block.count("*🕘 QTR* Das 13:00 às 01:00") == 2
    assert block.index("FORÇA TÁTICA") < block.index("ROCAM 1")


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
                "shift_type": "FT",
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
    team_idx = text.index("*🚔 FORÇA TÁTICA DEJEM*")
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


def test_format_team_mission_notes_empty():
    assert format_team_mission_notes(None) == []
    assert format_team_mission_notes("") == []
    assert format_team_mission_notes("   ") == []


def test_team_notes_render_after_members():
    snapshot = {
        "teams": [
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Força Tática",
                "vehicle_prefixo": "I-03024",
                "start_time": "13:00",
                "end_time": "01:00",
                "notes": "Permanecer em apoio ao Tático Comando.",
                "members": [
                    {
                        "patente": "CB",
                        "re": "110071-8",
                        "nome_guerra": "Ângelo",
                        "display_order": 1,
                    },
                    {
                        "patente": "SD",
                        "re": "162951-4",
                        "nome_guerra": "S.Lima",
                        "display_order": 2,
                    },
                ],
            },
            {
                "id": 2,
                "modality": "ROCAM",
                "mission_name": "ROCAM 1",
                "vehicle_prefixo": None,
                "start_time": "04:55",
                "end_time": "12:55",
                "notes": None,
                "members": [
                    {
                        "patente": "CB",
                        "re": "109840-3",
                        "nome_guerra": "Cardozo",
                        "assigned_vehicle_prefixo": "I-03069-11",
                        "display_order": 1,
                    },
                ],
            },
        ],
        "dejem_blocks": [
            {
                "shift_id": 9,
                "title": "ROCAM EXTRA",
                "shift_type": "ROCAM",
                "start_time": "04:55",
                "end_time": "12:55",
                "notes": "Apoiar evento na Praça Central.",
                "members": [
                    {
                        "patente": "CB",
                        "re": "147498-2",
                        "nome_guerra": "M. Carlos",
                        "display_order": 1,
                    },
                ],
            }
        ],
    }
    block = build_equipes_from_snapshot(snapshot)

    ft = block.index("*🚔 FORÇA TÁTICA*")
    ft_sep = block.index("----------------------------", ft)
    ft_chunk = block[ft:ft_sep]
    assert "CB PM 110071-8 ÂNGELO" in ft_chunk
    assert "*📌 Missão*" in ft_chunk
    assert "• Permanecer em apoio ao Tático Comando." in ft_chunk
    assert ft_chunk.index("S.LIMA") < ft_chunk.index("*📌 Missão*")

    # Equipe sem notes: bloco Missão ausente
    rocam = block.index("*🏍️ ROCAM 1*")
    rocam_sep = block.index("----------------------------", rocam)
    rocam_chunk = block[rocam:rocam_sep]
    assert "*📌 Missão*" not in rocam_chunk
    assert "CB PM 109840-3 CARDOZO - I-03069-11" in rocam_chunk

    dejem = block.index("*🏍️ ROCAM DEJEM*")
    assert "*📌 Missão*" in block[dejem:]
    assert "• Apoiar evento na Praça Central." in block[dejem:]


def test_team_notes_and_general_missoes_coexist():
    snapshot = {
        "scale_id": 1,
        "scale_date": "2026-07-14",
        "organizational_unit": OrganizationalUnit.FIRST_PLATOON.value,
        "fardamento": "5º Uniforme",
        "description": "QRV às 09:00 em frente à sala de choque.\nReunião com o comando às 08:30.",
        "teams": [
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Força Tática",
                "vehicle_prefixo": "I-03024",
                "start_time": "13:00",
                "end_time": "01:00",
                "notes": "Permanecer em apoio ao Tático Comando.",
                "members": [
                    {"patente": "CB", "re": "110071-8", "nome_guerra": "Angelo", "display_order": 1},
                ],
            }
        ],
        "dejem_blocks": [],
    }
    text = MessageGenerationService(DEFAULT_TEMPLATE_BODY).render_from_snapshot(snapshot)
    assert "*📌 Missão*" in text
    assert "• Permanecer em apoio ao Tático Comando." in text
    assert "*📢 MISSÕES*" in text
    assert "• QRV às 09:00 em frente à sala de choque." in text
    assert text.index("*📌 Missão*") < text.index("*📢 MISSÕES*")


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
    assert "*📢 MISSÕES*" in text
    assert "OBSERVAÇÕES" not in text
    assert "• Reforço ROCAM." in text
    assert "{{" not in text
    assert "Folga" not in text


def test_resolve_dejem_display_labels():
    assert resolve_dejem_display({"shift_type": "FT", "title": "APOIO TÁTICO"}) == (
        "🚔",
        "FORÇA TÁTICA DEJEM",
    )
    assert resolve_dejem_display({"shift_type": "ROCAM", "title": "ROCAM EXTRA"}) == (
        "🏍️",
        "ROCAM DEJEM",
    )
    assert resolve_dejem_display({"shift_type": "OUTROS", "title": "APOIO TÁTICO"}) == (
        "🚔",
        "APOIO TÁTICO DEJEM",
    )
    assert resolve_dejem_display({"title": "Supervisor Tático"}) == (
        "🚔",
        "SUPERVISOR TÁTICO DEJEM",
    )
    assert resolve_dejem_display({"title": "Tático Comando"}) == (
        "🚔",
        "TÁTICO COMANDO DEJEM",
    )
    # Título legado genérico: origem DEJEM + modalidade padrão (nunca «DEJEM» sozinho)
    assert resolve_dejem_display({"shift_type": "OUTROS", "title": "DEJEM"}) == (
        "🚔",
        "FORÇA TÁTICA DEJEM",
    )
    assert resolve_dejem_display({"title": "FT EXTRA"}) == (
        "🚔",
        "FORÇA TÁTICA DEJEM",
    )


def test_dejem_rocam_and_apoio_titles_in_message():
    snapshot = {
        "teams": [
            {
                "id": 1,
                "modality": "FT",
                "mission_name": "Força Tática",
                "vehicle_prefixo": "I-03024",
                "start_time": "06:00",
                "end_time": "18:00",
                "members": [{"patente": "CB", "nome_guerra": "Z", "display_order": 0}],
            }
        ],
        "dejem_blocks": [
            {
                "shift_id": 1,
                "title": "ROCAM EXTRA",
                "shift_type": "ROCAM",
                "vehicle_prefixo": "I-03070",
                "start_time": "06:00",
                "end_time": "18:00",
                "members": [{"patente": "SD", "nome_guerra": "X", "display_order": 0}],
            },
            {
                "shift_id": 2,
                "title": "APOIO TÁTICO",
                "shift_type": "OUTROS",
                "vehicle_prefixo": "I-03071",
                "start_time": "18:00",
                "end_time": "06:00",
                "members": [{"patente": "CB", "nome_guerra": "Y", "display_order": 0}],
            },
            {
                "shift_id": 3,
                "title": "DEJEM",
                "shift_type": "OUTROS",
                "vehicle_prefixo": "I-03072",
                "start_time": "12:00",
                "end_time": "00:00",
                "members": [{"patente": "SD", "nome_guerra": "W", "display_order": 0}],
            },
        ],
    }
    block = build_equipes_from_snapshot(snapshot)
    # Operacional sem origem DEJEM: sem sufixo
    assert "*🚔 FORÇA TÁTICA*" in block
    assert block.count("FORÇA TÁTICA DEJEM") == 1  # só o bloco OUTROS/DEJEM
    assert "*🏍️ ROCAM DEJEM*" in block
    assert "*🚔 APOIO TÁTICO DEJEM*" in block
    assert "*🚔 FORÇA TÁTICA DEJEM*" in block
    assert "*🚔 DEJEM*" not in block
    assert "ROCAM EXTRA" not in block
    assert "FT EXTRA" not in block


def test_legacy_observacoes_label_normalized_to_missoes():
    legacy = DEFAULT_TEMPLATE_BODY.replace("*📢 MISSÕES*", "*📢 OBSERVAÇÕES*")
    text = apply_template(
        legacy,
        {
            "titulo": "COMPANHIA DE FORÇA TÁTICA",
            "data": format_date_var(date(2026, 7, 14)),
            "fardamento": "—",
            "qtr": "",
            "equipes": "🚔 FT",
            "observacoes": "• Apoio",
        },
    )
    assert "*📢 MISSÕES*" in text
    assert "OBSERVAÇÕES" not in text


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
