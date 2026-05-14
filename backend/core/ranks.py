"""Ordem hierárquica de patentes (antiguidade institucional, maior índice = mais baixo na hierarquia)."""

PATENTE_ORDER: dict[str, int] = {
    "1° TEN": 0,
    "1º TEN": 0,
    "2° TEN": 1,
    "2º TEN": 1,
    "SUBTEN": 2,
    "1° SGT": 3,
    "1º SGT": 3,
    "2° SGT": 4,
    "2º SGT": 4,
    "3° SGT": 5,
    "3º SGT": 5,
    "CB": 6,
    "SD": 7,
}


def patente_sort_key(patente: str) -> tuple[int, str]:
    raw = patente.strip()
    upper = raw.upper()
    for key, idx in PATENTE_ORDER.items():
        if upper == key.upper():
            return (idx, raw)
    return (99, raw)
