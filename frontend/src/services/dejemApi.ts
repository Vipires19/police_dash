import { apiFetch } from "@/services/api";
import type {
  DejemAllocationAdminRow,
  DejemAllocationPublic,
  DejemDistributeResponse,
  DejemDistributionPreview,
  DejemInterestAdminRow,
  DejemInterestPublic,
  DejemInterestUpsertPayload,
  DejemMonthCreatePayload,
  DejemMonthPublic,
  DejemMonthUpdatePayload,
  DejemShiftCalendarResponse,
  DejemShiftCreatePayload,
  DejemShiftDashboard,
  DejemShiftDayDetail,
  DejemShiftPublic,
  DejemShiftTemplateCreatePayload,
  DejemShiftTemplatePublic,
  DejemShiftTemplateUpdatePayload,
  DejemShiftUpdatePayload,
  DejemMonthGeneratePayload,
  DejemMonthGeneratePreview,
  DejemMonthGenerateResult,
  DejemAdminAddParticipantPayload,
  DejemEnrollmentResult,
  DejemMyDayDetail,
  DejemParticipantAdminRow,
  DejemOfferEvent,
  DejemOfferEventCreatePayload,
  DejemOfferAvailable,
  DejemIncrementalPreview,
  DejemIncrementalRequest,
  DejemIncrementalResult,
  DejemAllocationSummary,
} from "@/types/dejem";

export async function listDejemMonths(token: string): Promise<DejemMonthPublic[]> {
  return apiFetch<DejemMonthPublic[]>("/dejem/months", { method: "GET", token });
}

export async function getDejemMonth(token: string, monthId: number): Promise<DejemMonthPublic> {
  return apiFetch<DejemMonthPublic>(`/dejem/months/${monthId}`, { method: "GET", token });
}

export async function createDejemMonth(
  token: string,
  payload: DejemMonthCreatePayload,
): Promise<DejemMonthPublic> {
  return apiFetch<DejemMonthPublic>("/dejem/months", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function updateDejemMonth(
  token: string,
  monthId: number,
  payload: DejemMonthUpdatePayload,
): Promise<DejemMonthPublic> {
  return apiFetch<DejemMonthPublic>(`/dejem/months/${monthId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  });
}

export async function closeDejemInterest(token: string, monthId: number): Promise<DejemMonthPublic> {
  return apiFetch<DejemMonthPublic>(`/dejem/months/${monthId}/close-interest`, {
    method: "POST",
    token,
  });
}

export async function getMyDejemInterest(
  token: string,
  monthId: number,
): Promise<DejemInterestPublic | null> {
  return apiFetch<DejemInterestPublic | null>(`/dejem/months/${monthId}/interest`, {
    method: "GET",
    token,
  });
}

export async function createMyDejemInterest(
  token: string,
  monthId: number,
  payload: DejemInterestUpsertPayload,
): Promise<DejemInterestPublic> {
  return apiFetch<DejemInterestPublic>(`/dejem/months/${monthId}/interest`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function updateMyDejemInterest(
  token: string,
  monthId: number,
  payload: DejemInterestUpsertPayload,
): Promise<DejemInterestPublic> {
  return apiFetch<DejemInterestPublic>(`/dejem/months/${monthId}/interest`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  });
}

export async function deleteMyDejemInterest(token: string, monthId: number): Promise<void> {
  await apiFetch<void>(`/dejem/months/${monthId}/interest`, {
    method: "DELETE",
    token,
  });
}

export async function listDejemMonthInterests(
  token: string,
  monthId: number,
): Promise<DejemInterestAdminRow[]> {
  return apiFetch<DejemInterestAdminRow[]>(`/dejem/months/${monthId}/interests`, {
    method: "GET",
    token,
  });
}

export async function getDejemDistributionPreview(
  token: string,
  monthId: number,
): Promise<DejemDistributionPreview> {
  return apiFetch<DejemDistributionPreview>(`/dejem/months/${monthId}/distribution-preview`, {
    method: "GET",
    token,
  });
}

export async function distributeDejemMonth(
  token: string,
  monthId: number,
): Promise<DejemDistributeResponse> {
  return apiFetch<DejemDistributeResponse>(`/dejem/months/${monthId}/distribute`, {
    method: "POST",
    token,
  });
}

export async function reopenDejemDistribution(
  token: string,
  monthId: number,
): Promise<DejemMonthPublic> {
  return apiFetch<DejemMonthPublic>(`/dejem/months/${monthId}/reopen-distribution`, {
    method: "POST",
    token,
  });
}

export async function listDejemMonthAllocations(
  token: string,
  monthId: number,
): Promise<DejemAllocationAdminRow[]> {
  return apiFetch<DejemAllocationAdminRow[]>(`/dejem/months/${monthId}/allocations`, {
    method: "GET",
    token,
  });
}

export async function getMyDejemAllocation(
  token: string,
  monthId: number,
): Promise<DejemAllocationPublic | null> {
  return apiFetch<DejemAllocationPublic | null>(`/dejem/months/${monthId}/allocation`, {
    method: "GET",
    token,
  });
}

export async function getDejemShiftCalendar(
  token: string,
  year: number,
  month: number,
): Promise<DejemShiftCalendarResponse> {
  return apiFetch<DejemShiftCalendarResponse>(
    `/dejem/shifts/calendar?year=${year}&month=${month}`,
    { method: "GET", token },
  );
}

export async function getDejemShiftDay(
  token: string,
  year: number,
  month: number,
  day: number,
): Promise<DejemShiftDayDetail> {
  return apiFetch<DejemShiftDayDetail>(
    `/dejem/shifts/day?year=${year}&month=${month}&day=${day}`,
    { method: "GET", token },
  );
}

export async function getDejemShiftDashboard(
  token: string,
  monthId: number,
): Promise<DejemShiftDashboard> {
  return apiFetch<DejemShiftDashboard>(`/dejem/months/${monthId}/shifts/dashboard`, {
    method: "GET",
    token,
  });
}

export async function createDejemShift(
  token: string,
  payload: DejemShiftCreatePayload,
): Promise<DejemShiftPublic> {
  return apiFetch<DejemShiftPublic>("/dejem/shifts", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function updateDejemShift(
  token: string,
  shiftId: number,
  payload: DejemShiftUpdatePayload,
): Promise<DejemShiftPublic> {
  return apiFetch<DejemShiftPublic>(`/dejem/shifts/${shiftId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  });
}

export async function deleteDejemShift(token: string, shiftId: number): Promise<void> {
  await apiFetch<void>(`/dejem/shifts/${shiftId}`, { method: "DELETE", token });
}

export async function listDejemShiftTemplates(
  token: string,
  activeOnly = false,
): Promise<DejemShiftTemplatePublic[]> {
  const q = activeOnly ? "?active_only=true" : "";
  return apiFetch<DejemShiftTemplatePublic[]>(`/dejem/shift-templates${q}`, {
    method: "GET",
    token,
  });
}

export async function createDejemShiftTemplate(
  token: string,
  payload: DejemShiftTemplateCreatePayload,
): Promise<DejemShiftTemplatePublic> {
  return apiFetch<DejemShiftTemplatePublic>("/dejem/shift-templates", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function updateDejemShiftTemplate(
  token: string,
  templateId: number,
  payload: DejemShiftTemplateUpdatePayload,
): Promise<DejemShiftTemplatePublic> {
  return apiFetch<DejemShiftTemplatePublic>(`/dejem/shift-templates/${templateId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  });
}

export async function deleteDejemShiftTemplate(token: string, templateId: number): Promise<void> {
  await apiFetch<void>(`/dejem/shift-templates/${templateId}`, { method: "DELETE", token });
}

export async function previewDejemMonthShifts(
  token: string,
  payload: DejemMonthGeneratePayload,
): Promise<DejemMonthGeneratePreview> {
  return apiFetch<DejemMonthGeneratePreview>("/dejem/shifts/generate/preview", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function generateDejemMonthShifts(
  token: string,
  payload: DejemMonthGeneratePayload,
): Promise<DejemMonthGenerateResult> {
  return apiFetch<DejemMonthGenerateResult>("/dejem/shifts/generate", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function getMyDejemCalendar(
  token: string,
  year: number,
  month: number,
): Promise<DejemShiftCalendarResponse> {
  const q = new URLSearchParams({ year: String(year), month: String(month) });
  return apiFetch<DejemShiftCalendarResponse>(`/dejem/my/calendar?${q}`, {
    method: "GET",
    token,
  });
}

export async function getMyDejemDay(
  token: string,
  year: number,
  month: number,
  day: number,
): Promise<DejemMyDayDetail> {
  const q = new URLSearchParams({
    year: String(year),
    month: String(month),
    day: String(day),
  });
  return apiFetch<DejemMyDayDetail>(`/dejem/my/day?${q}`, { method: "GET", token });
}

export async function enrollDejemShift(
  token: string,
  shiftId: number,
): Promise<DejemEnrollmentResult> {
  return apiFetch<DejemEnrollmentResult>(`/dejem/shifts/${shiftId}/enroll`, {
    method: "POST",
    token,
  });
}

export async function cancelDejemEnrollment(
  token: string,
  shiftId: number,
): Promise<DejemEnrollmentResult> {
  return apiFetch<DejemEnrollmentResult>(`/dejem/shifts/${shiftId}/enroll`, {
    method: "DELETE",
    token,
  });
}

export async function listDejemShiftParticipants(
  token: string,
  shiftId: number,
): Promise<DejemParticipantAdminRow[]> {
  return apiFetch<DejemParticipantAdminRow[]>(`/dejem/shifts/${shiftId}/participants`, {
    method: "GET",
    token,
  });
}

export async function addDejemShiftParticipant(
  token: string,
  shiftId: number,
  payload: DejemAdminAddParticipantPayload,
): Promise<DejemEnrollmentResult> {
  return apiFetch<DejemEnrollmentResult>(`/dejem/shifts/${shiftId}/participants`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function removeDejemShiftParticipant(
  token: string,
  shiftId: number,
  userId: number,
): Promise<DejemEnrollmentResult> {
  return apiFetch<DejemEnrollmentResult>(
    `/dejem/shifts/${shiftId}/participants/${userId}`,
    { method: "DELETE", token },
  );
}

export async function closeDejemShift(
  token: string,
  shiftId: number,
): Promise<DejemShiftPublic> {
  return apiFetch<DejemShiftPublic>(`/dejem/shifts/${shiftId}/close`, {
    method: "POST",
    token,
  });
}

/* --- Operations DEJEM: offers + incremental (sem novos endpoints) --- */

export async function listDejemOfferHistory(
  token: string,
  campaignId: number,
): Promise<DejemOfferEvent[]> {
  return apiFetch<DejemOfferEvent[]>(
    `/operations/dejem/offers/history?campaign_id=${campaignId}`,
    { method: "GET", token },
  );
}

export async function getDejemOfferAvailable(
  token: string,
  campaignId: number,
): Promise<DejemOfferAvailable> {
  return apiFetch<DejemOfferAvailable>(
    `/operations/dejem/offers/available?campaign_id=${campaignId}`,
    { method: "GET", token },
  );
}

export async function createDejemOfferEvent(
  token: string,
  payload: DejemOfferEventCreatePayload,
): Promise<DejemOfferEvent> {
  return apiFetch<DejemOfferEvent>("/operations/dejem/offers/", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function getDejemIncrementalPreview(
  token: string,
  campaignId: number,
): Promise<DejemIncrementalPreview> {
  return apiFetch<DejemIncrementalPreview>(
    `/operations/dejem/allocations/preview?campaign_id=${campaignId}`,
    { method: "GET", token },
  );
}

export async function runDejemIncremental(
  token: string,
  payload: DejemIncrementalRequest,
): Promise<DejemIncrementalResult> {
  return apiFetch<DejemIncrementalResult>("/operations/dejem/allocations/incremental", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function redistributeDejemRemaining(
  token: string,
  payload: DejemIncrementalRequest,
): Promise<DejemIncrementalResult> {
  return apiFetch<DejemIncrementalResult>(
    "/operations/dejem/allocations/redistribute-remaining",
    {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    },
  );
}

export async function getDejemAllocationSummary(
  token: string,
  campaignId: number,
): Promise<DejemAllocationSummary> {
  return apiFetch<DejemAllocationSummary>(
    `/operations/dejem/allocations/allocation-summary?campaign_id=${campaignId}`,
    { method: "GET", token },
  );
}
