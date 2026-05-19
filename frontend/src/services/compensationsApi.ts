import { apiFetch } from "./api";
import type {
  CompensationDashboardSummary,
  CompensationEventCreatePayload,
  CompensationEventLogPublic,
  CompensationEventPublic,
  CompensationEventStatus,
  CompensationEventUpdatePayload,
  CompensationType,
  DsUsagePublic,
} from "@/types/compensations";
import type { UserCompensationAvailable } from "@/types/leaves";

export async function listCompensations(
  token: string,
  params?: {
    status?: CompensationEventStatus;
    event_type?: CompensationType;
    user_id?: number;
    year?: number;
  },
): Promise<CompensationEventPublic[]> {
  const q = new URLSearchParams();
  if (params?.status) q.set("status", params.status);
  if (params?.event_type) q.set("event_type", params.event_type);
  if (params?.user_id != null) q.set("user_id", String(params.user_id));
  if (params?.year != null) q.set("year", String(params.year));
  const qs = q.toString();
  const path = qs ? `/compensations/?${qs}` : "/compensations/";
  return apiFetch<CompensationEventPublic[]>(path, { method: "GET", token });
}

export async function getCompensationSummary(
  token: string,
  year?: number,
): Promise<CompensationDashboardSummary> {
  const qs = year != null ? `?year=${year}` : "";
  return apiFetch<CompensationDashboardSummary>(`/compensations/summary${qs}`, {
    method: "GET",
    token,
  });
}

export async function getDsUsage(token: string, userId: number, year?: number): Promise<DsUsagePublic> {
  const qs = year != null ? `?year=${year}` : "";
  return apiFetch<DsUsagePublic>(`/compensations/users/${userId}/ds-usage${qs}`, {
    method: "GET",
    token,
  });
}

export async function listCompensationLogs(
  token: string,
  eventId: number,
): Promise<CompensationEventLogPublic[]> {
  return apiFetch<CompensationEventLogPublic[]>(`/compensations/${eventId}/logs`, {
    method: "GET",
    token,
  });
}

export async function listPendingCompensations(token: string): Promise<CompensationEventPublic[]> {
  return apiFetch<CompensationEventPublic[]>("/compensations/pending", { method: "GET", token });
}

export async function listAvailableCompensations(token: string): Promise<UserCompensationAvailable[]> {
  return apiFetch<UserCompensationAvailable[]>("/compensations/available", { method: "GET", token });
}

export async function createCompensationEvent(
  token: string,
  body: CompensationEventCreatePayload,
): Promise<CompensationEventPublic> {
  return apiFetch<CompensationEventPublic>("/compensations/", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function updateCompensationEvent(
  token: string,
  id: number,
  body: CompensationEventUpdatePayload,
): Promise<CompensationEventPublic> {
  return apiFetch<CompensationEventPublic>(`/compensations/${id}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function approveCompensationEvent(
  token: string,
  id: number,
  motivo?: string | null,
): Promise<CompensationEventPublic> {
  return apiFetch<CompensationEventPublic>(`/compensations/${id}/approve`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo: motivo ?? null }),
  });
}

export async function rejectCompensationEvent(
  token: string,
  id: number,
  motivo: string,
): Promise<CompensationEventPublic> {
  return apiFetch<CompensationEventPublic>(`/compensations/${id}/reject`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo }),
  });
}

export async function cancelCompensationEvent(
  token: string,
  id: number,
  motivo: string,
): Promise<CompensationEventPublic> {
  return apiFetch<CompensationEventPublic>(`/compensations/${id}/cancel`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo }),
  });
}

export async function revertCompensationEvent(
  token: string,
  id: number,
  motivo: string,
): Promise<CompensationEventPublic> {
  return apiFetch<CompensationEventPublic>(`/compensations/${id}/revert`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ motivo }),
  });
}
