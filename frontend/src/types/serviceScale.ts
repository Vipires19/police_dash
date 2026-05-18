export type ScaleStatus = "DRAFT" | "PUBLISHED";
export type ScaleModality = "FT" | "ROCAM";

export interface ScaleCalendarDay {
  date: string;
  scale_id: number | null;
  title: string | null;
  status: ScaleStatus | null;
  team_count: number;
}

export interface ScaleCalendarResponse {
  year: number;
  month: number;
  days: ScaleCalendarDay[];
}

export interface StaffAbsenceFlag {
  kind: "FOLGA" | "FERIAS" | "LP";
  label: string;
}

export interface StaffRosterEntry {
  user_id: number;
  patente: string;
  nome_guerra: string;
  display_order: number;
  operational_rank: number;
  absences: StaffAbsenceFlag[];
}

export interface ScaleVehicleOption {
  id: number;
  prefixo: string;
  placa: string;
  modalidade: string;
}

export interface ScaleTeamMemberPublic {
  id: number;
  user_id: number;
  patente: string;
  nome_guerra: string;
  display_order: number;
  assigned_vehicle_id: number | null;
  assigned_vehicle_prefixo: string | null;
  role_label: string | null;
}

export interface ScaleTeamPublic {
  id: number;
  modality: ScaleModality;
  vehicle_id: number | null;
  vehicle_prefixo: string | null;
  vehicle_placa: string | null;
  start_datetime: string;
  end_datetime: string;
  mission_name: string;
  notes: string | null;
  members: ScaleTeamMemberPublic[];
}

export interface ServiceScalePublic {
  id: number;
  scale_date: string;
  title: string;
  description: string | null;
  status: ScaleStatus;
  created_by_id: number;
  created_by_label: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  teams: ScaleTeamPublic[];
}

export interface ScaleDayDetailResponse {
  scale: ServiceScalePublic | null;
  staff_roster: StaffRosterEntry[];
  vehicles_ft: ScaleVehicleOption[];
  vehicles_ro_cam: ScaleVehicleOption[];
}

export interface ScaleLogFeedItem {
  id: number;
  service_scale_id: number;
  scale_date: string;
  scale_title: string;
  action_type: string;
  description: string;
  created_at: string;
  actor_label: string;
}

export interface ScaleHistoryEntry {
  id: number;
  scale_date: string;
  title: string;
  status: ScaleStatus;
  team_count: number;
  published_at: string | null;
  updated_at: string;
}

export interface ScaleHistoryResponse {
  items: ScaleHistoryEntry[];
  total: number;
}

export interface ScaleTeamMemberInput {
  user_id: number;
  assigned_vehicle_id?: number | null;
  role_label?: string | null;
}

export interface ScaleTeamCreatePayload {
  modality: ScaleModality;
  vehicle_id?: number | null;
  start_datetime: string;
  end_datetime: string;
  mission_name: string;
  notes?: string | null;
  members: ScaleTeamMemberInput[];
}

export interface ScaleTeamUpdatePayload {
  modality?: ScaleModality;
  vehicle_id?: number | null;
  start_datetime?: string;
  end_datetime?: string;
  mission_name?: string;
  notes?: string | null;
  members?: ScaleTeamMemberInput[];
}

export const FT_MISSION_PRESETS = ["Tático Comando", "Supervisor Tático", "Força Tática"] as const;
export const ROCAM_MISSION_PRESETS = ["ROCAM 1", "ROCAM 2", "ROCAM 3"] as const;

export interface ScaleExportResponse {
  text: string;
}
