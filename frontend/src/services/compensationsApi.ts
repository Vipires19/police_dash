import { apiFetch } from "./api";
import type { CompensationEventPublic, UserCompensationAvailable } from "@/types/leaves";

export interface CompensationEventCreatePayload {
  event_type: CompensationEventPublic["event_type"];
  motivo: string;
  participant_user_ids: number[];
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
