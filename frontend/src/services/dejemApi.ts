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
