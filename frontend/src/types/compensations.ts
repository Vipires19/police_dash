export type CompensationType =
  | "CPJ_SUPPORT"
  | "WEAPON_OCCURRENCE"
  | "RELEVANT_OCCURRENCE"
  | "TWO_WANTED"
  | "FIVE_FLAGRANTS"
  | "FOLGA_MENSAL"
  | "COMPENSACAO"
  | "DS";

export type CompensationEventStatus =
  | "PENDING"
  | "APPROVED"
  | "REJECTED"
  | "CANCELLED"
  | "REVERTED";

export type CompensationLogAction =
  | "CREATED"
  | "APPROVED"
  | "REJECTED"
  | "UPDATED"
  | "CANCELLED"
  | "REVERTED";

export const COMPENSATION_TYPE_LABELS: Record<CompensationType, string> = {
  CPJ_SUPPORT: "Apoio CPJ / operacional (≥4h)",
  WEAPON_OCCURRENCE: "Ocorrência com armas",
  RELEVANT_OCCURRENCE: "Ocorrência de grande relevância (N90/TAT)",
  TWO_WANTED: "02 procurados",
  FIVE_FLAGRANTS: "05 flagrantes",
  FOLGA_MENSAL: "Folga mensal",
  COMPENSACAO: "Compensação",
  DS: "Dispensa de serviço (DS)",
};

export const OPERATIONAL_COMPENSATION_TYPES: CompensationType[] = [
  "FOLGA_MENSAL",
  "COMPENSACAO",
  "DS",
];

export const MERIT_COMPENSATION_TYPES: CompensationType[] = [
  "CPJ_SUPPORT",
  "WEAPON_OCCURRENCE",
  "RELEVANT_OCCURRENCE",
  "TWO_WANTED",
  "FIVE_FLAGRANTS",
];

export const COMPENSATION_STATUS_LABELS: Record<CompensationEventStatus, string> = {
  PENDING: "Pendente",
  APPROVED: "Aprovado",
  REJECTED: "Indeferido",
  CANCELLED: "Cancelado",
  REVERTED: "Revertido",
};

export interface CompensationEventPublic {
  id: number;
  event_type: CompensationType;
  motivo: string;
  status: CompensationEventStatus;
  created_by_id: number;
  decided_by_id: number | null;
  decided_at: string | null;
  decision_motivo: string | null;
  created_at: string;
  updated_at: string;
  participant_user_ids: number[];
  created_by_label?: string | null;
  decided_by_label?: string | null;
}

export interface CompensationEventLogPublic {
  id: number;
  compensation_event_id: number;
  actor_id: number;
  actor_label: string;
  action: CompensationLogAction;
  from_status: CompensationEventStatus | null;
  to_status: CompensationEventStatus | null;
  motivo: string | null;
  details: string | null;
  created_at: string;
}

export interface DsUsagePublic {
  user_id: number;
  year: number;
  used_count: number;
  reference_quota: number;
  display: string;
}

export interface CompensationDashboardSummary {
  pending_count: number;
  approved_recent_count: number;
  ds_usage_samples: DsUsagePublic[];
  recent_events: CompensationEventPublic[];
}

export interface CompensationEventCreatePayload {
  event_type: CompensationType;
  motivo: string;
  participant_user_ids: number[];
}

export interface CompensationEventUpdatePayload {
  event_type?: CompensationType;
  motivo?: string;
  participant_user_ids?: number[];
}
