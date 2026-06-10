import { apiFetch } from "./api";
import type {
  CriminalWatchNotePublic,
  CriminalWatchSheetResponse,
  CriminalWatchVehicleCreatePayload,
  CriminalWatchVehicleDetail,
  CriminalWatchVehiclePublic,
} from "@/types/criminalWatch";

export async function createCriminalWatchVehicle(
  token: string,
  payload: CriminalWatchVehicleCreatePayload,
): Promise<CriminalWatchVehiclePublic> {
  return apiFetch<CriminalWatchVehiclePublic>("/criminal-watch-vehicles/", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function searchCriminalWatchVehicles(
  token: string,
  query: string,
  limit = 100,
): Promise<CriminalWatchVehiclePublic[]> {
  const q = new URLSearchParams({ q: query, limit: String(limit) });
  return apiFetch<CriminalWatchVehiclePublic[]>(`/criminal-watch-vehicles/search?${q}`, {
    method: "GET",
    token,
  });
}

export async function getCriminalWatchVehicle(
  token: string,
  vehicleId: number,
): Promise<CriminalWatchVehicleDetail> {
  return apiFetch<CriminalWatchVehicleDetail>(`/criminal-watch-vehicles/${vehicleId}`, {
    method: "GET",
    token,
  });
}

export async function deleteCriminalWatchVehicle(token: string, vehicleId: number): Promise<void> {
  return apiFetch<void>(`/criminal-watch-vehicles/${vehicleId}`, { method: "DELETE", token });
}

export async function addCriminalWatchNote(
  token: string,
  vehicleId: number,
  note: string,
): Promise<CriminalWatchNotePublic> {
  return apiFetch<CriminalWatchNotePublic>(`/criminal-watch-vehicles/${vehicleId}/notes`, {
    method: "POST",
    token,
    body: JSON.stringify({ note }),
  });
}

export async function getCriminalWatchSheet(token: string): Promise<CriminalWatchSheetResponse> {
  return apiFetch<CriminalWatchSheetResponse>("/criminal-watch-vehicles/sheet", {
    method: "GET",
    token,
  });
}
