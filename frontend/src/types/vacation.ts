export type VacationType = "FERIAS" | "LP";

export type VacationStatus = "PENDING" | "REVIEW" | "APPROVED" | "REJECTED" | "CANCELLED";

export interface CalendarVacationEntry {
  id: number;
  user_id: number;
  patente: string;
  nome_guerra: string;
  display_order: number;
  vacation_type: VacationType;
  status: VacationStatus;
  start_date: string;
  end_date: string;
  total_days: number;
  operational_rank: number;
}

export interface VacationCalendarDay {
  date: string;
  entries: CalendarVacationEntry[];
  active_count: number;
  is_critical: boolean;
}

export interface VacationCalendarSummary {
  my_pending_count: number;
  command_pending_vacations?: number | null;
  critical_days?: string[] | null;
  currently_away_count?: number | null;
}

export interface VacationCalendarResponse {
  year: number;
  month: number;
  days: VacationCalendarDay[];
  summary: VacationCalendarSummary;
}

export interface VacationRequestPublic {
  id: number;
  user_id: number;
  vacation_type: VacationType;
  start_date: string;
  end_date: string;
  total_days: number;
  status: VacationStatus;
  review_reason: string | null;
  decision_reason: string | null;
  approved_by_id: number | null;
  approved_at: string | null;
  created_at: string;
  patente?: string | null;
  nome_guerra?: string | null;
  display_order?: number | null;
}
