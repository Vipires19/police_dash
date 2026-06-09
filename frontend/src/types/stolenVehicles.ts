export type StolenVehicleType = "CARRO" | "MOTO";
export type StolenOccurrenceType = "FURTO" | "ROUBO";

export const STOLEN_VEHICLE_TYPE_LABELS: Record<StolenVehicleType, string> = {
  CARRO: "Carro",
  MOTO: "Moto",
};

export const STOLEN_OCCURRENCE_TYPE_LABELS: Record<StolenOccurrenceType, string> = {
  FURTO: "Furto",
  ROUBO: "Roubo",
};

export const STOLEN_OCCURRENCE_SHORT: Record<StolenOccurrenceType, string> = {
  FURTO: "F",
  ROUBO: "R",
};

export interface StolenVehiclePublic {
  id: number;
  vehicle_type: StolenVehicleType;
  plate: string;
  vehicle_model: string;
  color: string;
  year: number;
  occurrence_type: StolenOccurrenceType;
  plate_group: number;
  observation: string | null;
  is_recovered: boolean;
  recovered_at: string | null;
  recovered_by_id: number | null;
  recovered_notes: string | null;
  created_at: string;
  created_by_id: number;
}

export interface StolenVehicleRecoverPayload {
  recovered_notes?: string | null;
}

export interface StolenVehicleCreatePayload {
  vehicle_type: StolenVehicleType;
  plate: string;
  vehicle_model: string;
  color: string;
  year: number;
  occurrence_type: StolenOccurrenceType;
  observation?: string | null;
}

export interface StolenVehicleSheetEntry {
  id: number | null;
  plate: string | null;
  vehicle_model: string | null;
  color: string | null;
  year: number | null;
  occurrence_type: StolenOccurrenceType | null;
}

export interface StolenVehicleSheetGroup {
  group: number;
  slots: StolenVehicleSheetEntry[];
}

export interface StolenVehicleSheetResponse {
  carros: StolenVehicleSheetGroup[];
  motos: StolenVehicleSheetGroup[];
}
