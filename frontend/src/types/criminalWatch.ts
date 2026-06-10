export interface VehicleQruCodePublic {
  id: number;
  code: string;
  description: string;
  is_active: boolean;
  created_at: string;
  created_by_id: number;
}

export interface CriminalWatchVehicleCreatePayload {
  plate: string;
  vehicle_model: string;
  color: string;
  year: number;
  qru_code_id: number;
  initial_note: string;
}

export interface CriminalWatchNotePublic {
  id: number;
  vehicle_id: number;
  note: string;
  created_at: string;
  created_by_id: number;
  created_by_label: string | null;
}

export interface CriminalWatchVehiclePublic {
  id: number;
  plate: string;
  vehicle_model: string;
  color: string;
  year: number;
  qru_code_id: number;
  qru_code: string;
  qru_description: string;
  created_at: string;
  created_by_id: number;
  created_by_label: string | null;
}

export interface CriminalWatchVehicleDetail extends CriminalWatchVehiclePublic {
  notes: CriminalWatchNotePublic[];
}

export interface CriminalWatchSheetEntry {
  id: number | null;
  plate_numeric: string | null;
  plate_letters: string | null;
  vehicle_model: string | null;
  color_abbr: string | null;
  year_short: string | null;
  qru_code: string | null;
}

export interface CriminalWatchSheetResponse {
  slots: CriminalWatchSheetEntry[];
}

export interface VehicleQruCodeCreatePayload {
  code: string;
  description: string;
}

export interface VehicleQruCodeUpdatePayload {
  code?: string;
  description?: string;
}
