export type DejemMonthStatus =
  | "OPEN_INTEREST"
  | "DISTRIBUTED_PENDING"
  | "DISTRIBUTED"
  | "OPEN_SHIFTS"
  | "FINISHED";

export type DejemShiftStatus =
  | "OPEN"
  | "CLOSED"
  | "READY_FOR_MAP"
  | "INTEGRATED"
  | "FINISHED";

export type DejemShiftType = "FT" | "ROCAM" | "OUTROS";

export type ParticipationType = "NORMAL" | "EXTRAORDINARY" | "SUBSTITUTION";

export type ParticipantStatus = "REGISTERED" | "CONFIRMED" | "CANCELLED";

export const DEJEM_MONTH_NAMES = [
  "",
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
] as const;

export function dejemMonthLabel(year: number, month: number): string {
  return `${DEJEM_MONTH_NAMES[month] ?? month}/${year}`.toUpperCase();
}

export const DEJEM_MONTH_STATUS_LABELS: Record<DejemMonthStatus, string> = {
  OPEN_INTEREST: "Manifestação aberta",
  DISTRIBUTED_PENDING: "Aguardando distribuição",
  DISTRIBUTED: "Distribuído",
  OPEN_SHIFTS: "Escalas abertas",
  FINISHED: "Encerrado",
};

export const DEJEM_SHIFT_STATUS_LABELS: Record<DejemShiftStatus, string> = {
  OPEN: "Aberta",
  CLOSED: "Fechada",
  READY_FOR_MAP: "Pronta p/ mapa",
  INTEGRATED: "No Mapa Força",
  FINISHED: "Finalizada",
};

export const DEJEM_SHIFT_TYPE_LABELS: Record<DejemShiftType, string> = {
  FT: "FT",
  ROCAM: "ROCAM",
  OUTROS: "Outros",
};

export const PARTICIPATION_TYPE_LABELS: Record<ParticipationType, string> = {
  NORMAL: "Normal",
  EXTRAORDINARY: "Extraordinária",
  SUBSTITUTION: "Substituição",
};

export const PARTICIPANT_STATUS_LABELS: Record<ParticipantStatus, string> = {
  REGISTERED: "Inscrito",
  CONFIRMED: "Confirmado",
  CANCELLED: "Cancelado",
};

export interface DejemMonthPublic {
  id: number;
  year: number;
  month: number;
  total_available_slots: number;
  monthly_limit_per_officer: number;
  status: DejemMonthStatus;
  created_by_id: number;
  created_at: string;
  updated_at: string;
  interested_count: number;
}

export interface DejemMonthCreatePayload {
  year: number;
  month: number;
  total_available_slots: number;
  monthly_limit_per_officer: number;
}

export interface DejemMonthUpdatePayload {
  total_available_slots?: number;
  monthly_limit_per_officer?: number;
}

export interface DejemInterestUpsertPayload {
  interested: boolean;
  desired_slots: number;
}

export interface DejemInterestPublic {
  id: number;
  month_id: number;
  user_id: number;
  interested: boolean;
  desired_slots: number;
  created_at: string;
}

export interface DejemInterestAdminRow {
  id: number;
  month_id: number;
  user_id: number;
  interested: boolean;
  desired_slots: number;
  created_at: string;
  patente: string;
  nome_guerra: string;
  full_name: string | null;
  role: string;
  organizational_unit: string;
}

export interface DejemDistributionPreview {
  month_id: number;
  total_available_slots: number;
  interested_count: number;
  monthly_limit_per_officer: number;
  base_quantity: number;
  remaining_after_base: number;
}

export interface DejemAllocationPublic {
  id: number;
  month_id: number;
  user_id: number;
  allocated_slots: number;
  used_slots: number;
  remaining_slots: number;
  created_at: string;
}

export interface DejemAllocationAdminRow {
  id: number;
  month_id: number;
  user_id: number;
  allocated_slots: number;
  used_slots: number;
  remaining_slots: number;
  created_at: string;
  desired_slots: number;
  patente: string;
  nome_guerra: string;
  full_name: string | null;
  role: string;
  organizational_unit: string;
  display_order: number;
}

export interface DejemDistributeResponse {
  month: DejemMonthPublic;
  preview: DejemDistributionPreview;
  leftover_slots: number;
  allocations: DejemAllocationAdminRow[];
}

export interface DejemShiftPublic {
  id: number;
  month_id: number;
  date: string;
  start_time: string;
  end_time: string;
  shift_type: DejemShiftType;
  capacity: number;
  filled_slots: number;
  available_slots: number;
  status: DejemShiftStatus;
  vehicle_id: number | null;
  vehicle_prefixo: string | null;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface DejemShiftCreatePayload {
  month_id: number;
  date: string;
  start_time: string;
  end_time: string;
  shift_type: DejemShiftType;
  capacity: number;
  status?: DejemShiftStatus;
  vehicle_id?: number | null;
}

export interface DejemShiftUpdatePayload {
  date?: string;
  start_time?: string;
  end_time?: string;
  shift_type?: DejemShiftType;
  capacity?: number;
  status?: DejemShiftStatus;
  vehicle_id?: number | null;
}

export interface DejemShiftCalendarDay {
  date: string;
  shift_count: number;
  total_capacity: number;
  total_filled: number;
  has_open: boolean;
  has_closed: boolean;
  has_finished: boolean;
}

export interface DejemShiftCalendarResponse {
  year: number;
  month: number;
  month_id: number | null;
  days: DejemShiftCalendarDay[];
}

export interface DejemShiftDayDetail {
  date: string;
  month_id: number | null;
  shifts: DejemShiftPublic[];
}

export interface DejemShiftDashboard {
  month_id: number;
  year: number;
  month: number;
  total_shifts: number;
  open_shifts: number;
  closed_shifts: number;
  finished_shifts: number;
  total_capacity: number;
  total_filled: number;
  total_available: number;
  avg_remaining_slots?: number;
}

export interface DejemMyShiftCard {
  id: number;
  month_id: number;
  date: string;
  start_time: string;
  end_time: string;
  shift_type: DejemShiftType;
  capacity: number;
  filled_slots: number;
  available_slots: number;
  status: DejemShiftStatus;
  i_am_enrolled: boolean;
  my_participation_type: ParticipationType | null;
}

export interface DejemMyDayDetail {
  date: string;
  month_id: number | null;
  shifts: DejemMyShiftCard[];
}

export interface DejemParticipantAdminRow {
  id: number;
  shift_id: number;
  user_id: number;
  participation_type: ParticipationType;
  status: ParticipantStatus;
  consumes_balance: boolean;
  created_at: string;
  enrolled_by_id: number | null;
  patente: string;
  nome_guerra: string;
  full_name: string | null;
  remaining_slots: number;
}

export interface DejemAdminAddParticipantPayload {
  user_id: number;
  participation_type: ParticipationType;
}

export interface DejemEnrollmentResult {
  participant_id: number;
  shift_id: number;
  user_id: number;
  participation_type: ParticipationType;
  status: ParticipantStatus;
  consumes_balance: boolean;
  remaining_slots: number | null;
  created_at: string;
}

export interface DejemShiftTemplatePublic {
  id: number;
  name: string;
  shift_type: DejemShiftType;
  start_time: string;
  end_time: string;
  default_capacity: number;
  is_active: boolean;
  created_by_id: number;
  created_at: string;
  updated_at: string;
}

export interface DejemShiftTemplateCreatePayload {
  name: string;
  shift_type: DejemShiftType;
  start_time: string;
  end_time: string;
  default_capacity: number;
  is_active?: boolean;
}

export interface DejemShiftTemplateUpdatePayload {
  name?: string;
  shift_type?: DejemShiftType;
  start_time?: string;
  end_time?: string;
  default_capacity?: number;
  is_active?: boolean;
}

export interface DejemMonthGeneratePayload {
  year: number;
  month: number;
  weekdays: number[];
  template_ids: number[];
  replace_existing?: boolean;
  ignore_holidays?: boolean;
}

export interface DejemMonthGenerateResult {
  year: number;
  month: number;
  month_id: number;
  created: number;
  ignored: number;
  replaced: number;
  elapsed_ms: number;
}

export type DejemGeneratePreviewAction = "CREATE" | "IGNORE" | "REPLACE";

export interface DejemMonthGeneratePreviewItem {
  date: string;
  start_time: string;
  end_time: string;
  shift_type: DejemShiftType;
  capacity: number;
  template_id: number;
  template_name: string;
  action: DejemGeneratePreviewAction;
  status_label: string;
  existing_shift_id: number | null;
}

export interface DejemMonthGeneratePreview {
  year: number;
  month: number;
  month_id: number;
  days_in_month: number;
  selected_days_count: number;
  weekdays: number[];
  weekday_labels: string[];
  template_names: string[];
  replace_existing: boolean;
  planned_shifts: number;
  planned_capacity: number;
  create_count: number;
  ignore_count: number;
  replace_count: number;
  create_capacity: number;
  replace_capacity: number;
  existing_conflicts: number;
  items: DejemMonthGeneratePreviewItem[];
  elapsed_ms: number;
}

/** Normaliza horário da API (HH:MM:SS ou HH:MM) para input type=time. */
export function dejemTimeInputValue(value: string): string {
  return value.slice(0, 5);
}

export function formatDejemTime(value: string): string {
  return value.slice(0, 5);
}
