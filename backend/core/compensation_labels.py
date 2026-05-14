from models.compensations import CompensationType

COMPENSATION_DISPLAY_LABELS: dict[CompensationType, str] = {
    CompensationType.CPJ_SUPPORT: "Horas CPJ",
    CompensationType.WEAPON_OCCURRENCE: "Ocorrência com arma",
    CompensationType.RELEVANT_OCCURRENCE: "Ocorrência de relevância",
    CompensationType.TWO_WANTED: "02 Procurados",
    CompensationType.FIVE_FLAGRANTS: "05 Flagrantes",
}


def compensation_display_label(event_type: CompensationType) -> str:
    return COMPENSATION_DISPLAY_LABELS.get(event_type, event_type.value)
