from models.compensations import CompensationType

COMPENSATION_DISPLAY_LABELS: dict[CompensationType, str] = {
    CompensationType.CPJ_SUPPORT: "Apoio CPJ / operacional (≥4h)",
    CompensationType.WEAPON_OCCURRENCE: "Ocorrência com armas",
    CompensationType.RELEVANT_OCCURRENCE: "Ocorrência de grande relevância (N90/TAT)",
    CompensationType.TWO_WANTED: "02 procurados",
    CompensationType.FIVE_FLAGRANTS: "05 flagrantes",
    CompensationType.FOLGA_MENSAL: "Folga mensal",
    CompensationType.COMPENSACAO: "Compensação",
    CompensationType.DS: "Dispensa de serviço (DS)",
}

# Tipos válidos no cadastro de eventos de compensação (méritos operacionais).
MERIT_COMPENSATION_TYPES: frozenset[CompensationType] = frozenset(
    {
        CompensationType.CPJ_SUPPORT,
        CompensationType.WEAPON_OCCURRENCE,
        CompensationType.RELEVANT_OCCURRENCE,
        CompensationType.TWO_WANTED,
        CompensationType.FIVE_FLAGRANTS,
    }
)


def compensation_display_label(event_type: CompensationType) -> str:
    return COMPENSATION_DISPLAY_LABELS.get(event_type, event_type.value)
