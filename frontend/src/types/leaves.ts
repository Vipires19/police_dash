export type LeaveType = "MONTHLY" | "COMPENSATION" | "DS";

export type LeaveStatus = "PENDING" | "REVIEW" | "APPROVED" | "REJECTED" | "CANCELLED";

export type {
  CompensationType,
  CompensationEventStatus,
  CompensationEventPublic,
} from "@/types/compensations";

export type UserCompensationStatus = "AVAILABLE" | "USED";

export interface CalendarLeaveEntry {
  id: number;
  leave_on: string;
  user_id: number;
  patente: string;
  nome_guerra: string;
  display_order: number;
  leave_type: LeaveType;
  status: LeaveStatus;
  operational_rank: number;
}

export interface CalendarDay {
  date: string;
  entries: CalendarLeaveEntry[];
  active_count: number;
  is_critical: boolean;
}

export interface LeaveCalendarSummary {
  my_pending_count: number;
  command_pending_leaves?: number | null;
  command_pending_compensations?: number | null;
  critical_days?: string[] | null;
}

export interface YearMonth {
  year: number;
  month: number;
}

export interface LeaveBookingPolicy {
  reference_date: string;
  allowed_year_months: YearMonth[];
  operational_hint: string;
}

export interface LeaveCalendarResponse {
  year: number;
  month: number;
  days: CalendarDay[];
  summary: LeaveCalendarSummary;
  booking_policy: LeaveBookingPolicy;
}

export interface LeaveRequestPublic {
  id: number;
  user_id: number;
  leave_on: string;
  leave_type: LeaveType;
  user_compensation_id: number | null;
  status: LeaveStatus;
  review_reason: string | null;
  decision_motivo: string | null;
  decided_by_id: number | null;
  decided_at: string | null;
  created_at: string;
  patente?: string | null;
  nome_guerra?: string | null;
  display_order?: number | null;
}

export interface UserCompensationPublic {
  id: number;
  user_id: number;
  compensation_event_id: number;
  status: UserCompensationStatus;
  created_at: string;
  display_label?: string;
}

/** Crédito disponível retornado por GET /compensations/available */
export interface UserCompensationAvailable {
  id: number;
  type: CompensationType;
  label: string;
  event_date: string;
  description: string;
}
