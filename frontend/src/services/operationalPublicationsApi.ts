import { apiFetch } from "@/services/api";
import type {
  OperationalPublicationCenterDay,
  OperationalPublicationDetail,
  OperationalPublicationHistoryResponse,
  OperationalPublicationPublic,
} from "@/types/operationalPublication";

export function getPublicationCenter(token: string, day: string) {
  return apiFetch<OperationalPublicationCenterDay>(
    `/operational-publications/center?day=${encodeURIComponent(day)}`,
    { token },
  );
}

export function listPublicationHistory(
  token: string,
  params?: { scale_date?: string; limit?: number; offset?: number },
) {
  const q = new URLSearchParams();
  if (params?.scale_date) q.set("scale_date", params.scale_date);
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiFetch<OperationalPublicationHistoryResponse>(
    `/operational-publications/history${qs ? `?${qs}` : ""}`,
    { token },
  );
}

export function createDraftByDate(token: string, scaleDate: string) {
  return apiFetch<OperationalPublicationPublic>(
    `/operational-publications/draft/by-date/${scaleDate}`,
    { method: "POST", token },
  );
}

export function validatePublication(token: string, publicationId: number) {
  return apiFetch<OperationalPublicationPublic>(
    `/operational-publications/${publicationId}/validate`,
    { method: "POST", token },
  );
}

export function publishPublication(
  token: string,
  publicationId: number,
  body?: { acknowledge_risks?: boolean; reason?: string | null },
) {
  return apiFetch<OperationalPublicationPublic>(
    `/operational-publications/${publicationId}/publish`,
    {
      method: "POST",
      token,
      body: JSON.stringify(body ?? {}),
    },
  );
}

export function getPublication(token: string, publicationId: number) {
  return apiFetch<OperationalPublicationDetail>(`/operational-publications/${publicationId}`, {
    token,
  });
}

export function refreshPublication(token: string, publicationId: number) {
  return apiFetch<OperationalPublicationPublic>(
    `/operational-publications/${publicationId}/refresh`,
    { method: "POST", token },
  );
}
