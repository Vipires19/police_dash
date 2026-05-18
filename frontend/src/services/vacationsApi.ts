import { apiFetch } from "./api";
import type { VacationCalendarResponse, VacationRequestPublic } from "@/types/vacation";

export interface VacationRequestPayload {
  start_date: string;
  end_date: string;
  vacation_type: "FERIAS" | "LP";
}

export async function getVacationCalendar(
  token: string,
  year?: number,
  month?: number,
): Promise<VacationCalendarResponse> {
  const q = new URLSearchParams();
  if (year != null) q.set("year", String(year));
  if (month != null) q.set("month", String(month));
  const qs = q.toString();
  return apiFetch<VacationCalendarResponse>(`/vacations/calendar${qs ? `?${qs}` : ""}`, {
    method: "GET",
    token,
  });
}

export async function listPendingVacations(token: string): Promise<VacationRequestPublic[]> {
  return apiFetch<VacationRequestPublic[]>("/vacations/pending", { method: "GET", token });
}

export async function requestVacation(
  token: string,
  body: VacationRequestPayload,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>("/vacations/request", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function approveVacation(
  token: string,
  id: number,
  reason?: string | null,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`/vacations/${id}/approve`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason: reason ?? null }),
  });
}

export async function rejectVacation(
  token: string,
  id: number,
  reason: string,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`/vacations/${id}/reject`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason }),
  });
}

export async function cancelVacation(
  token: string,
  id: number,
  reason?: string | null,
): Promise<VacationRequestPublic> {
  return apiFetch<VacationRequestPublic>(`/vacations/${id}/cancel`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ reason: reason ?? null }),
  });
}
