"""Testes unitários do domínio OperationalPublication (fase 4.10)."""

from __future__ import annotations

from types import SimpleNamespace

from models.service_scale import ScaleModality
from schemas.operational_publication import ChecklistItemLevel
from services.operational_publication_service import build_checklist


def test_checklist_ok_with_teams(monkeypatch):
    team = SimpleNamespace(
        modality=ScaleModality.FT,
        vehicle_id=1,
        members=[],
        mission_name="FT",
    )
    scale = SimpleNamespace(teams=[team], title="Escala Teste")
    snapshot = {
        "teams": [{"id": 1}],
        "meta": {
            "dejem_closed_or_integrated_count": 2,
            "dejem_open_count": 0,
            "dejem_ready_for_map_count": 0,
        },
    }

    monkeypatch.setattr(
        "services.operational_publication_service._collect_pipeline_errors",
        lambda *_a, **_k: [],
        raising=False,
    )
    # Patch where it's imported inside the function — inject via module path used at call
    import services.scale_publish_pipeline as pipe

    monkeypatch.setattr(pipe, "_collect_pipeline_errors", lambda *_a, **_k: [])

    checklist = build_checklist(SimpleNamespace(), scale, snapshot)  # type: ignore[arg-type]
    by_key = {i.key: i for i in checklist.items}
    assert by_key["scale"].level == ChecklistItemLevel.OK
    assert by_key["dejem"].level == ChecklistItemLevel.OK
    assert by_key["vehicles"].level == ChecklistItemLevel.OK
    assert by_key["pdf"].level == ChecklistItemLevel.PENDING
    assert checklist.ready is True


def test_checklist_warns_open_dejem(monkeypatch):
    team = SimpleNamespace(
        modality=ScaleModality.FT,
        vehicle_id=10,
        members=[],
        mission_name="CMD",
    )
    scale = SimpleNamespace(teams=[team], title="X")
    snapshot = {
        "teams": [{"id": 1}],
        "meta": {
            "dejem_closed_or_integrated_count": 1,
            "dejem_open_count": 2,
            "dejem_ready_for_map_count": 0,
        },
    }
    import services.scale_publish_pipeline as pipe

    monkeypatch.setattr(pipe, "_collect_pipeline_errors", lambda *_a, **_k: [])
    checklist = build_checklist(SimpleNamespace(), scale, snapshot)  # type: ignore[arg-type]
    dejem = next(i for i in checklist.items if i.key == "dejem")
    assert dejem.level == ChecklistItemLevel.WARN
    assert checklist.can_publish_with_risk is True
