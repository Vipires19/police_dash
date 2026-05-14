import { apiFetch } from "./api";
import type {
  Vehicle,
  VehicleCreatePayload,
  VehicleLog,
  VehicleLogFeedItem,
  VehicleStatusPayload,
  VehicleUpdatePayload,
} from "@/types/vehicle";

export async function listVehicles(token: string): Promise<Vehicle[]> {
  return apiFetch<Vehicle[]>("/vehicles/", { method: "GET", token });
}

export async function createVehicle(token: string, body: VehicleCreatePayload): Promise<Vehicle> {
  return apiFetch<Vehicle>("/vehicles/", {
    method: "POST",
    token,
    body: JSON.stringify(body),
  });
}

export async function updateVehicle(
  token: string,
  id: number,
  body: VehicleUpdatePayload,
): Promise<Vehicle> {
  return apiFetch<Vehicle>(`/vehicles/${id}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function changeVehicleStatus(
  token: string,
  id: number,
  body: VehicleStatusPayload,
): Promise<Vehicle> {
  return apiFetch<Vehicle>(`/vehicles/${id}/status`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function listVehicleLogs(token: string, id: number): Promise<VehicleLog[]> {
  return apiFetch<VehicleLog[]>(`/vehicles/${id}/logs`, { method: "GET", token });
}

export async function listRecentVehicleLogs(token: string, limit = 15): Promise<VehicleLogFeedItem[]> {
  return apiFetch<VehicleLogFeedItem[]>(`/vehicles/recent-logs?limit=${limit}`, {
    method: "GET",
    token,
  });
}
