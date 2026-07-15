import { apiFetch } from "@/services/api";
import type {
  ScaleCalendarResponse,
  ScaleDayDetailResponse,
  ScaleHistoryResponse,
  ScaleLogFeedItem,
  ScaleTeamCreatePayload,
  ScaleTeamMemberInput,
  ScaleExportResponse,
  ScaleTeamUpdatePayload,
  ScaleVersionDetail,
  ScaleVersionPublic,
  ServiceScalePublic,
} from "@/types/serviceScale";

export function getScaleCalendar(token: string, year: number, month: number) {
  return apiFetch<ScaleCalendarResponse>(
    `/service-scales/calendar?year=${year}&month=${month}`,
    { token },
  );
}

export function getScaleByDate(token: string, isoDate: string) {
  return apiFetch<ScaleDayDetailResponse>(`/service-scales/${isoDate}`, { token });
}

export function getScaleHistory(
  token: string,
  params?: { from?: string; to?: string; status?: string; limit?: number; offset?: number },
) {
  const q = new URLSearchParams();
  if (params?.from) q.set("from", params.from);
  if (params?.to) q.set("to", params.to);
  if (params?.status) q.set("status", params.status);
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  const qs = q.toString();
  return apiFetch<ScaleHistoryResponse>(`/service-scales/history${qs ? `?${qs}` : ""}`, { token });
}

export function listRecentScaleEvents(token: string, limit = 12) {
  return apiFetch<ScaleLogFeedItem[]>(`/service-scales/recent-events?limit=${limit}`, { token });
}

export function createScale(
  token: string,
  body: { scale_date: string; title: string; description?: string | null; status?: string },
) {
  return apiFetch<ServiceScalePublic>("/service-scales/", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export function updateScale(
  token: string,
  scaleId: number,
  body: { title?: string; description?: string | null; fardamento?: string | null },
) {
  return apiFetch<ServiceScalePublic>(`/service-scales/${scaleId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export function addScaleTeam(token: string, scaleId: number, body: ScaleTeamCreatePayload) {
  return apiFetch<ServiceScalePublic>(`/service-scales/${scaleId}/teams`, {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export function previewPublishScale(
  token: string,
  scaleId: number,
  body?: { description?: string | null },
) {
  return apiFetch<{
    text: string;
    fardamento: string | null;
    description: string | null;
    team_count: number;
    dejem_count: number;
  }>(`/service-scales/${scaleId}/publish/preview`, {
    method: "POST",
    token,
    body: JSON.stringify(body ?? {}),
  });
}

export function publishScale(token: string, scaleId: number) {
  return apiFetch<ServiceScalePublic>(`/service-scales/${scaleId}/publish`, {
    method: "POST",
    token,
  });
}

export function unpublishScale(token: string, scaleId: number) {
  return apiFetch<ServiceScalePublic>(`/service-scales/${scaleId}/unpublish`, {
    method: "POST",
    token,
  });
}

export function listScaleVersions(token: string, scaleId: number) {
  return apiFetch<ScaleVersionPublic[]>(`/service-scales/${scaleId}/versions`, {
    method: "GET",
    token,
  });
}

export function getScaleVersion(token: string, scaleId: number, versionNumber: number) {
  return apiFetch<ScaleVersionDetail>(
    `/service-scales/${scaleId}/versions/${versionNumber}`,
    { method: "GET", token },
  );
}

export function exportScaleVersion(token: string, scaleId: number, versionNumber: number) {
  return apiFetch<{ text: string }>(
    `/service-scales/${scaleId}/versions/${versionNumber}/export`,
    { method: "GET", token },
  );
}

export function updateScaleTeam(token: string, teamId: number, body: ScaleTeamUpdatePayload) {
  return apiFetch<ServiceScalePublic>(`/service-scales/team/${teamId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export function updateScaleTeamMembers(token: string, teamId: number, members: ScaleTeamMemberInput[]) {
  return apiFetch<ServiceScalePublic>(`/service-scales/team/${teamId}/members`, {
    method: "PATCH",
    token,
    body: JSON.stringify({ members }),
  });
}

export function removeScaleTeam(token: string, teamId: number) {
  return apiFetch<ServiceScalePublic>(`/service-scales/team/${teamId}/remove`, {
    method: "PATCH",
    token,
  });
}

export function deleteScale(token: string, scaleId: number) {
  return apiFetch<void>(`/service-scales/${scaleId}`, { method: "DELETE", token });
}

export function exportScale(token: string, scaleId: number) {
  return apiFetch<ScaleExportResponse>(`/service-scales/${scaleId}/export`, { token });
}
