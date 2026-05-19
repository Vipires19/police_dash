import { apiFetch } from "./api";
import type {
  VacationCalendarResponse,
  VacationRequestPublic,
  VacationStatus,
  VacationType,
} from "@/types/vacation";

const BASE = "/absences";

export interface AbsenceRequestPayload {
  start_date: string;
  end_date: string;
  vacation_type: VacationType;
  notes?: string | null;
}

export interface AbsenceUpdatePayload {
  start_date?: string;
  end_date?: string;
  vacation_type?: VacationType;
  notes?: string | null;
}

export async function getAbsenceCalendar(
  token: string,
  year?: number,
  month?: number,
): Promise<VacationCalendarResponse> {
  const q = new URLSearchParams();
  if (year != null) q.set("year", String(year));
  if (month != null) q.set("month", String(month));
  const qs = q.toString();
  return apiFetch<VacationCalendarResponse>(`${BASE}/calendar${qs ? `?${qs}` : ""}`, {
    method: "GET",
    token,
  });
}

export async function listAbsences(
  token: string,
  params?: {
    status?: VacationStatus;
    type?: VacationType;
    user_id?: number;
    year?: number;
    month?: number;
  },
): Promise<VacationRequestPublic[]> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.type) q.set("type", params.type);
  if (params?.user_id != null) q.set("user_id", String(params.user_id));
  if (params?.year != null) q.set("year", String(params.year));
  if (params?.month != null) q.set("month", String(params.month));
  const qs = q.toString();
  const path = qs ? `${BASE}/?${qs}` : `${BASE}/`;
  return apiFetch<VacationRequestPublic[]>(path, { method: "GET", token });
}

export async function listPendingAbsences(token: string): Promise<VacationRequestPublic[]> {
  return apiFetch<VacationRequestPublic[]>(`${BASE}/pending`, { method: "GET", token });
}

export async function requestAbsence(
  token: string,
  body: AbsenceRequestPayload,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`${BASE}/request`, {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function updateAbsence(
  token: string,
  id: number,
  body: AbsenceUpdatePayload,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`${BASE}/${id}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function approveAbsence(
  token: string,
  id: number,
  reason?: string | null,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`${BASE}/${id}/approve`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason: reason ?? null }),
  });
}

export async function rejectAbsence(
  token: string,
  id: number,
  reason: string,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`${BASE}/${id}/reject`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason }),
  });
}

export async function cancelAbsence(
  token: string,
  id: number,
  reason?: string | null,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`${BASE}/${id}/cancel`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason: reason ?? null }),
  });
}

export async function revertAbsence(
  token: string,
  id: number,
  reason: string,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`${BASE}/${id}/revert`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason }),
  });
}
