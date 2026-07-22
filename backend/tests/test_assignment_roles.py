"""Testes das funções operacionais FT/ROCAM."""

from __future__ import annotations

import pytest

from operations.dejem.models.assignment_roles import (
    assert_role_allowed_for_team,
    assert_roles_unique,
    assignment_roles_for,
)
from operations.dejem.models.enums import AssignmentRole, TeamType


def test_ft_and_rocam_roles():
    assert AssignmentRole.DRIVER in assignment_roles_for(TeamType.FT)
    assert AssignmentRole.MOTO_2 in assignment_roles_for(TeamType.ROCAM)
    assert assignment_roles_for(TeamType.APOIO) == ()


def test_unique_roles():
    assert_roles_unique([AssignmentRole.COMMANDER, AssignmentRole.DRIVER])
    with pytest.raises(ValueError, match="Motorista"):
        assert_roles_unique([AssignmentRole.DRIVER, AssignmentRole.DRIVER])


def test_role_allowed():
    assert_role_allowed_for_team(TeamType.FT, AssignmentRole.THIRD_MAN)
    with pytest.raises(ValueError, match="Moto 2"):
        assert_role_allowed_for_team(TeamType.FT, AssignmentRole.MOTO_2)
