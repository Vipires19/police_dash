import {
  teamRolesFor,
  type ScaleModality,
  type ScaleTeamMemberPublic,
  type ScaleTeamPublic,
  type TeamRole,
} from "@/types/serviceScale";

export type RoleAssignments = Record<string, number | "">;
export type RoleBikes = Record<string, number | "">;

export function emptyRoleAssignments(modality: ScaleModality): RoleAssignments {
  const out: RoleAssignments = {};
  for (const role of teamRolesFor(modality)) out[role] = "";
  return out;
}

/** Carrega funções a partir da equipe; legado sem role_label usa a ordem da lista. */
export function membersToRoleAssignments(team: ScaleTeamPublic): RoleAssignments {
  const roles = teamRolesFor(team.modality);
  const assignments = emptyRoleAssignments(team.modality);
  const byRole = new Map<string, ScaleTeamMemberPublic>();
  for (const m of team.members) {
    if (m.role_label && (roles as readonly string[]).includes(m.role_label)) {
      byRole.set(m.role_label, m);
    }
  }
  if (byRole.size > 0) {
    for (const role of roles) {
      const m = byRole.get(role);
      if (m) assignments[role] = m.user_id;
    }
    return assignments;
  }
  team.members.forEach((m, i) => {
    if (roles[i]) assignments[roles[i]] = m.user_id;
  });
  return assignments;
}

export function membersToRoleBikes(team: ScaleTeamPublic): RoleBikes {
  const assignments = membersToRoleAssignments(team);
  const bikes: RoleBikes = {};
  for (const role of teamRolesFor(team.modality)) bikes[role] = "";
  for (const m of team.members) {
    const role = (Object.entries(assignments).find(([, uid]) => uid === m.user_id)?.[0] ??
      m.role_label) as string | undefined;
    if (role && m.assigned_vehicle_id) bikes[role] = m.assigned_vehicle_id;
  }
  return bikes;
}

export function assignedUserIds(assignments: RoleAssignments): number[] {
  return Object.values(assignments).filter((v): v is number => typeof v === "number");
}

export function setRoleUser(
  assignments: RoleAssignments,
  role: TeamRole | string,
  userId: number | "",
): RoleAssignments {
  const next = { ...assignments };
  if (userId !== "") {
    for (const key of Object.keys(next)) {
      if (key !== role && next[key] === userId) next[key] = "";
    }
  }
  next[role] = userId;
  return next;
}
