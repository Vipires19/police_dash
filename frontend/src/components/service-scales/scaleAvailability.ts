import type { ScaleTeamPublic } from "@/types/serviceScale";

export interface ScaleUsage {
  usedFtVehicleIds: Set<number>;
  usedRoCamMotoIds: Set<number>;
  usedUserIds: Set<number>;
}

export function gatherScaleUsage(teams: ScaleTeamPublic[], excludeTeamId?: number): ScaleUsage {
  const usedFtVehicleIds = new Set<number>();
  const usedRoCamMotoIds = new Set<number>();
  const usedUserIds = new Set<number>();

  for (const team of teams) {
    if (excludeTeamId !== undefined && team.id === excludeTeamId) continue;
    if (team.modality === "FT" && team.vehicle_id) usedFtVehicleIds.add(team.vehicle_id);
    for (const m of team.members) {
      usedUserIds.add(m.user_id);
      if (m.assigned_vehicle_id) usedRoCamMotoIds.add(m.assigned_vehicle_id);
    }
  }

  return { usedFtVehicleIds, usedRoCamMotoIds, usedUserIds };
}

export function filterFtVehicles<T extends { id: number }>(
  vehicles: T[],
  usage: ScaleUsage,
  currentVehicleId?: number | null,
): T[] {
  return vehicles.filter((v) => !usage.usedFtVehicleIds.has(v.id) || v.id === currentVehicleId);
}

export function filterRoCamMotos<T extends { id: number }>(
  vehicles: T[],
  usage: ScaleUsage,
  currentMotoId?: number | null,
): T[] {
  return vehicles.filter((v) => !usage.usedRoCamMotoIds.has(v.id) || v.id === currentMotoId);
}

export function isUserAvailable(userId: number, usage: ScaleUsage): boolean {
  return !usage.usedUserIds.has(userId);
}
