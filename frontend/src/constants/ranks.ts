/** Ordem hierárquica (índice menor = mais alto na escala). */
export const PATENTE_ORDER: Record<string, number> = {
  "1° TEN": 0,
  "1º TEN": 0,
  "2° TEN": 1,
  "2º TEN": 1,
  SUBTEN: 2,
  "1° SGT": 3,
  "1º SGT": 3,
  "2° SGT": 4,
  "2º SGT": 4,
  "3° SGT": 5,
  "3º SGT": 5,
  CB: 6,
  SD: 7,
};

export function patenteRank(patente: string): number {
  const t = patente.trim();
  const hit = Object.keys(PATENTE_ORDER).find((k) => k.toUpperCase() === t.toUpperCase());
  return hit !== undefined ? PATENTE_ORDER[hit]! : 99;
}
