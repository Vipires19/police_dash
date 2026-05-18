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

/** Agrupamento visual do efetivo (não altera ordenação no backend). */
export type VisualRankGroup = "OFFICERS" | "NCOS" | "ENLISTED";

/** Seção visual separada para policiais com role ESTAGIO. */
export type EstagioVisualGroup = "ESTAGIO";

export const ESTAGIO_SECTION_LABEL = "Estágio";

export const VISUAL_GROUP_LABELS: Record<VisualRankGroup, string> = {
  OFFICERS: "Oficiais",
  NCOS: "SubTen / Sargentos",
  ENLISTED: "Cabos / Soldados",
};

const VISUAL_GROUP_ORDER: VisualRankGroup[] = ["OFFICERS", "NCOS", "ENLISTED"];

export function visualRankGroup(patente: string): VisualRankGroup {
  const rank = patenteRank(patente);
  if (rank <= 1) return "OFFICERS";
  if (rank <= 5) return "NCOS";
  return "ENLISTED";
}

export function visualGroupSortIndex(group: VisualRankGroup): number {
  return VISUAL_GROUP_ORDER.indexOf(group);
}
