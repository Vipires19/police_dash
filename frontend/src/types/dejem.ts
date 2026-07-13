export type DejemMonthStatus =
  | "OPEN_INTEREST"
  | "DISTRIBUTED_PENDING"
  | "DISTRIBUTED"
  | "OPEN_SHIFTS"
  | "FINISHED";

export type DejemShiftStatus = "OPEN" | "CLOSED" | "FINISHED";

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
  FINISHED: "Finalizada",
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
