import { apiFetch } from "./api";
import type {
  VehicleQruCodeCreatePayload,
  VehicleQruCodePublic,
  VehicleQruCodeUpdatePayload,
} from "@/types/criminalWatch";

export async function listVehicleQruCodes(token: string): Promise<VehicleQruCodePublic[]> {
  return apiFetch<VehicleQruCodePublic[]>("/vehicle-qru-codes/", { method: "GET", token });
}

export async function listActiveVehicleQruCodes(token: string): Promise<VehicleQruCodePublic[]> {
  return apiFetch<VehicleQruCodePublic[]>("/vehicle-qru-codes/active", { method: "GET", token });
}

export async function createVehicleQruCode(
  token: string,
  payload: VehicleQruCodeCreatePayload,
): Promise<VehicleQruCodePublic> {
  return apiFetch<VehicleQruCodePublic>("/vehicle-qru-codes/", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });
}

export async function updateVehicleQruCode(
  token: string,
  codeId: number,
  payload: VehicleQruCodeUpdatePayload,
): Promise<VehicleQruCodePublic> {
  return apiFetch<VehicleQruCodePublic>(`/vehicle-qru-codes/${codeId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  });
}

export async function deactivateVehicleQruCode(
  token: string,
  codeId: number,
): Promise<VehicleQruCodePublic> {
  return apiFetch<VehicleQruCodePublic>(`/vehicle-qru-codes/${codeId}/deactivate`, {
    method: "PATCH",
    token,
  });
}
