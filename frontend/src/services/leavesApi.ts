import { apiFetch } from "./api";
import type { LeaveCalendarResponse, LeaveRequestPublic } from "@/types/leaves";

export interface LeaveRequestPayload {
  leave_on: string;
  leave_type: "MONTHLY" | "COMPENSATION";
  user_compensation_id?: number | null;
}

export async function getLeaveCalendar(
  token: string,
  year?: number,
  month?: number,
): Promise<LeaveCalendarResponse> {
  const q = new URLSearchParams();
  if (year != null) q.set("year", String(year));
  if (month != null) q.set("month", String(month));
  const qs = q.toString();
  return apiFetch<LeaveCalendarResponse>(`/leaves/calendar${qs ? `?${qs}` : ""}`, { method: "GET", token });
}

export async function listPendingLeaves(token: string): Promise<LeaveRequestPublic[]> {
  return apiFetch<LeaveRequestPublic[]>("/leaves/pending", { method: "GET", token });
}

export async function requestLeave(token: string, body: LeaveRequestPayload): Promise<LeaveRequestPublic> {
  return apiFetch<LeaveRequestPublic>("/leaves/request", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function approveLeave(token: string, id: number, motivo?: string | null): Promise<LeaveRequestPublic> {
  return apiFetch<LeaveRequestPublic>(`/leaves/${id}/approve`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo: motivo ?? null }),
  });
}

export async function rejectLeave(token: string, id: number, motivo: string): Promise<LeaveRequestPublic> {
  return apiFetch<LeaveRequestPublic>(`/leaves/${id}/reject`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo }),
  });
}

export async function cancelLeave(token: string, id: number, motivo?: string | null): Promise<LeaveRequestPublic> {
  return apiFetch<LeaveRequestPublic>(`/leaves/${id}/cancel`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo: motivo ?? null }),
  });
}
