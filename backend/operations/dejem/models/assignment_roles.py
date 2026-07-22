"""Funções operacionais por tipo de equipe DEJEM (paridade com Escala Operacional)."""

from __future__ import annotations

from operations.dejem.models.enums import AssignmentRole, TeamType

# Labels idênticos à Escala Operacional (`schemas.service_scale.FT_TEAM_ROLES`).
ASSIGNMENT_ROLE_LABELS: dict[AssignmentRole, str] = {
    AssignmentRole.COMMANDER: "Comandante da Equipe",
    AssignmentRole.DRIVER: "Motorista",
    AssignmentRole.THIRD_MAN: "3º Homem",
    AssignmentRole.FOURTH_MAN: "4º Homem",
    AssignmentRole.MOTO_2: "Moto 2",
    AssignmentRole.MOTO_3: "Moto 3",
    AssignmentRole.MEMBER: "Membro",
}

FT_ASSIGNMENT_ROLES: tuple[AssignmentRole, ...] = (
    AssignmentRole.COMMANDER,
    AssignmentRole.DRIVER,
    AssignmentRole.THIRD_MAN,
    AssignmentRole.FOURTH_MAN,
)

ROCAM_ASSIGNMENT_ROLES: tuple[AssignmentRole, ...] = (
    AssignmentRole.COMMANDER,
    AssignmentRole.MOTO_2,
    AssignmentRole.MOTO_3,
)

# Funções exclusivas (no máximo 1 por equipe). MEMBER pode repetir.
EXCLUSIVE_ASSIGNMENT_ROLES: frozenset[AssignmentRole] = frozenset(
    {
        AssignmentRole.COMMANDER,
        AssignmentRole.DRIVER,
        AssignmentRole.THIRD_MAN,
        AssignmentRole.FOURTH_MAN,
        AssignmentRole.MOTO_2,
        AssignmentRole.MOTO_3,
    }
)


def assignment_roles_for(team_type: TeamType | str) -> tuple[AssignmentRole, ...]:
    key = team_type.value if isinstance(team_type, TeamType) else str(team_type).upper()
    if key == TeamType.ROCAM.value:
        return ROCAM_ASSIGNMENT_ROLES
    if key == TeamType.FT.value:
        return FT_ASSIGNMENT_ROLES
    return ()


def assignment_role_label(role: AssignmentRole | str) -> str:
    if isinstance(role, str):
        try:
            role = AssignmentRole(role)
        except ValueError:
            return role
    return ASSIGNMENT_ROLE_LABELS.get(role, role.value)


def assert_roles_unique(
    roles: list[AssignmentRole],
    *,
    error_cls: type[Exception] = ValueError,
) -> None:
    seen: set[AssignmentRole] = set()
    for role in roles:
        if role not in EXCLUSIVE_ASSIGNMENT_ROLES:
            continue
        if role in seen:
            label = assignment_role_label(role)
            raise error_cls(f"A função '{label}' só pode existir uma vez por equipe.")
        seen.add(role)


def assert_role_allowed_for_team(
    team_type: TeamType | str,
    role: AssignmentRole,
    *,
    error_cls: type[Exception] = ValueError,
) -> None:
    if role == AssignmentRole.MEMBER:
        return
    allowed = assignment_roles_for(team_type)
    if allowed and role not in allowed:
        raise error_cls(
            f"Função '{assignment_role_label(role)}' não é válida para equipe {team_type}."
        )
