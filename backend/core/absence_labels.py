from models.vacation import VacationType

RESTRICTED_ABSENCE_TYPES: frozenset[VacationType] = frozenset(
    {VacationType.FERIAS, VacationType.LP},
)

FLEXIBLE_ABSENCE_TYPES: frozenset[VacationType] = frozenset(
    {
        VacationType.LTS,
        VacationType.CURSO,
        VacationType.ESTAGIO_OPERACIONAL,
        VacationType.OUTROS,
    },
)

ABSENCE_TYPE_LABELS: dict[VacationType, str] = {
    VacationType.FERIAS: "Férias",
    VacationType.LP: "LP",
    VacationType.LTS: "LTS",
    VacationType.CURSO: "Curso",
    VacationType.ESTAGIO_OPERACIONAL: "Estágio operacional",
    VacationType.OUTROS: "Outros",
}

OPERATIONAL_RANK: dict[VacationType, int] = {
    VacationType.FERIAS: 1,
    VacationType.LP: 2,
    VacationType.LTS: 3,
    VacationType.CURSO: 4,
    VacationType.ESTAGIO_OPERACIONAL: 5,
    VacationType.OUTROS: 6,
}


def absence_display_label(vt: VacationType) -> str:
    return ABSENCE_TYPE_LABELS.get(vt, vt.value)


def is_restricted_absence(vt: VacationType) -> bool:
    return vt in RESTRICTED_ABSENCE_TYPES
