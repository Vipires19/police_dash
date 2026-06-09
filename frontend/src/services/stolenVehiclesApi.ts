import { apiFetch } from "./api";
import type {
  StolenVehicleCreatePayload,
  StolenVehiclePublic,
  StolenVehicleRecoverPayload,
  StolenVehicleSheetResponse,
  StolenVehicleType,
} from "@/types/stolenVehicles";

export async function createStolenVehicle(
  token: string,
  payload: StolenVehicleCreatePayload,
): Promise<StolenVehiclePublic> {
  return apiFetch<StolenVehiclePublic>("/stolen-vehicles/", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function listStolenVehicles(
  token: string,
  params?: {
    is_recovered?: boolean;
    vehicle_type?: StolenVehicleType;
    plate_group?: number;
    limit?: number;
  },
): Promise<StolenVehiclePublic[]> {
  const q = new URLSearchParams();
  if (params?.is_recovered != null) q.set("is_recovered", String(params.is_recovered));
  if (params?.vehicle_type) q.set("vehicle_type", params.vehicle_type);
  if (params?.plate_group != null) q.set("plate_group", String(params.plate_group));
  if (params?.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  const path = qs ? `/stolen-vehicles/?${qs}` : "/stolen-vehicles/";
  return apiFetch<StolenVehiclePublic[]>(path, { method: "GET", token });
}

export async function searchStolenVehicles(
  token: string,
  query: string,
  limit = 100,
): Promise<StolenVehiclePublic[]> {
  const q = new URLSearchParams({ q: query, limit: String(limit) });
  return apiFetch<StolenVehiclePublic[]>(`/stolen-vehicles/search?${q}`, {
    method: "GET",
    token,
  });
}

export async function getStolenVehicleSheet(token: string): Promise<StolenVehicleSheetResponse> {
  return apiFetch<StolenVehicleSheetResponse>("/stolen-vehicles/sheet", {
    method: "GET",
    token,
  });
}

export async function recoverStolenVehicle(
  token: string,
  vehicleId: number,
  payload?: StolenVehicleRecoverPayload,
): Promise<StolenVehiclePublic> {
  return apiFetch<StolenVehiclePublic>(`/stolen-vehicles/${vehicleId}/recover`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload ?? {}),
  });
}
