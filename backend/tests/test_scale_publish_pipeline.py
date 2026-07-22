"""Testes do pipeline de publicação inteligente (fase 4.7)."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from models.dejem import DejemShiftStatus, DejemShiftType, ParticipantStatus
from models.service_scale import ScaleModality
from services.scale_publish_pipeline import (
    _diff_summaries,
    _inject_version_line,
    _validate_dejem_officer_conflicts,
    _validate_duplicate_users,
    _validate_duplicate_vehicles,
    _validate_structure,
)

_BR = ZoneInfo("America/Sao_Paulo")


def _member(uid: int, moto=None, name="X"):
    return SimpleNamespace(
        user_id=uid,
        assigned_vehicle_id=moto,
        role_label=None,
        user=SimpleNamespace(patente="CB", nome_guerra=name, display_order=1),
        assigned_vehicle=SimpleNamespace(prefixo=f"I-{moto}") if moto else None,
    )


def _team(*, tid, modality, mission, vehicle_id=None, members, start=None, end=None):
    now = datetime.now(tz=_BR)
    return SimpleNamespace(
        id=tid,
        modality=modality,
        mission_name=mission,
        vehicle_id=vehicle_id,
        vehicle=SimpleNamespace(prefixo=f"I-{vehicle_id}") if vehicle_id else None,
        members=members,
        start_datetime=start or now,
        end_datetime=end or (now + timedelta(hours=8)),
        notes=None,
    )


def test_validate_structure_requires_teams():
    scale = SimpleNamespace(teams=[])
    errs = _validate_structure(scale)
    assert any("equipe" in e.lower() for e in errs)


def test_duplicate_users_detected():
    scale = SimpleNamespace(
        teams=[
            _team(
                tid=1,
                modality=ScaleModality.FT,
                mission="A",
                vehicle_id=10,
                members=[_member(1, name="JOAO"), _member(2, name="PEDRO")],
            ),
            _team(
                tid=2,
                modality=ScaleModality.FT,
                mission="B",
                vehicle_id=11,
                members=[_member(1, name="JOAO")],
            ),
        ]
    )
    errs = _validate_duplicate_users(scale)
    assert len(errs) == 1
    assert "JOAO" in errs[0]


def test_duplicate_ft_vehicles_detected():
    scale = SimpleNamespace(
        teams=[
            _team(
                tid=1,
                modality=ScaleModality.FT,
                mission="A",
                vehicle_id=10,
                members=[_member(1)],
            ),
            _team(
                tid=2,
                modality=ScaleModality.FT,
                mission="B",
                vehicle_id=10,
                members=[_member(2)],
            ),
        ]
    )
    errs = _validate_duplicate_vehicles(scale)
    assert any("Viatura FT duplicada" in e for e in errs)


def test_duplicate_motos_detected():
    scale = SimpleNamespace(
        teams=[
            _team(
                tid=1,
                modality=ScaleModality.ROCAM,
                mission="RO1",
                members=[_member(1, moto=50, name="A"), _member(2, moto=51, name="B")],
            ),
            _team(
                tid=2,
                modality=ScaleModality.ROCAM,
                mission="RO2",
                members=[_member(3, moto=50, name="C")],
            ),
        ]
    )
    errs = _validate_duplicate_vehicles(scale)
    assert any("Moto ROCAM duplicada" in e for e in errs)


def test_inject_version_after_qtr():
    text = "💀\nQtr: 10:00hs\nRest"
    out = _inject_version_line(text, 2, datetime(2026, 7, 14, 10, 0, tzinfo=_BR))
    assert "Versão 2" in out
    assert out.index("Qtr:") < out.index("Versão 2")


def test_diff_first_publish():
    assert "Primeira publicação" in _diff_summaries(None, {"title": "X", "teams": [], "dejem_blocks": []})


def test_diff_title_change():
    prev = '{"title": "A", "teams": [], "dejem_blocks": []}'
    summary = _diff_summaries(prev, {"title": "B", "teams": [], "dejem_blocks": []})
    assert "Título" in summary


def test_dejem_conflict_only_when_times_overlap():
    day = date(2026, 8, 19)
    op_start = datetime(2026, 8, 19, 18, 0, tzinfo=_BR)
    op_end = datetime(2026, 8, 20, 2, 0, tzinfo=_BR)
    scale = SimpleNamespace(
        scale_date=day,
        teams=[
            _team(
                tid=1,
                modality=ScaleModality.FT,
                mission="PATRULHA",
                vehicle_id=10,
                members=[_member(1, name="SILVA")],
                start=op_start,
                end=op_end,
            )
        ],
    )
    # DEJEM manhã — mesmo policial, sem overlap
    morning = SimpleNamespace(
        date=day,
        start_time=time(6, 0),
        end_time=time(14, 0),
        shift_type=DejemShiftType.FT,
        status=DejemShiftStatus.CLOSED,
        participants=[
            SimpleNamespace(user_id=1, status=ParticipantStatus.CONFIRMED),
        ],
    )
    with patch(
        "services.scale_publish_pipeline.dejem_map.list_shifts_for_date",
        return_value=[morning],
    ):
        assert _validate_dejem_officer_conflicts(None, scale) == []

    # DEJEM overnight — overlap real
    overnight = SimpleNamespace(
        date=day,
        start_time=time(18, 30),
        end_time=time(2, 30),
        shift_type=DejemShiftType.FT,
        status=DejemShiftStatus.CLOSED,
        participants=[
            SimpleNamespace(user_id=1, status=ParticipantStatus.CONFIRMED),
        ],
    )
    with patch(
        "services.scale_publish_pipeline.dejem_map.list_shifts_for_date",
        return_value=[overnight],
    ):
        errs = _validate_dejem_officer_conflicts(None, scale)
    assert len(errs) == 1
    assert "SILVA" in errs[0]
    assert "sobreposição" in errs[0].lower()
    assert "PATRULHA" in errs[0]
    assert "18:30" in errs[0]
