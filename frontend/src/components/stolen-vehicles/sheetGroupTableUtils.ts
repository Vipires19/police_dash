import type { StolenVehicleSheetEntry } from "@/types/stolenVehicles";
import { STOLEN_OCCURRENCE_SHORT } from "@/types/stolenVehicles";

const PLATE_CELL_COUNT = 7;

/** Caixas da coluna Placa — na linha vazia, o dígito do grupo aparece na 4ª caixa (como na folha física). */
export function buildPlateCells(plate: string | null | undefined, groupNum: number): string[] {
  const cells = Array<string>(PLATE_CELL_COUNT).fill("");
  if (!plate) {
    cells[3] = String(groupNum);
    return cells;
  }
  const chars = plate
    .replace(/[^A-Za-z0-9]/g, "")
    .toUpperCase()
    .slice(0, PLATE_CELL_COUNT)
    .split("");
  chars.forEach((ch, i) => {
    cells[i] = ch;
  });
  return cells;
}

export function slotFrLabel(slot: StolenVehicleSheetEntry): string {
  return slot.occurrence_type ? STOLEN_OCCURRENCE_SHORT[slot.occurrence_type] : "";
}

export function isGroupOnLeftMargin(groupNum: number): boolean {
  return groupNum % 2 === 0;
}
