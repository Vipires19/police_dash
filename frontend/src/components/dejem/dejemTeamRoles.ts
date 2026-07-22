/**
 * Funções DEJEM FT/ROCAM — reutiliza labels e helpers da Escala Operacional.
 */
import {
  FT_TEAM_ROLES,
  ROCAM_TEAM_ROLES,
  teamRolesFor,
  type ScaleModality,
  type TeamRole,
} from "@/types/serviceScale";
import {
  emptyRoleAssignments,
  setRoleUser,
  type RoleAssignments,
} from "@/components/service-scales/teamRoles";

export type DejemAssignmentRole =
  | "MEMBER"
  | "COMMANDER"
  | "DRIVER"
  | "THIRD_MAN"
  | "FOURTH_MAN"
  | "MOTO_2"
  | "MOTO_3";

const LABEL_TO_ROLE: Record<string, DejemAssignmentRole> = {
  "Comandante da Equipe": "COMMANDER",
  Motorista: "DRIVER",
  "3º Homem": "THIRD_MAN",
  "4º Homem": "FOURTH_MAN",
  "Moto 2": "MOTO_2",
  "Moto 3": "MOTO_3",
};

const ROLE_TO_LABEL: Record<DejemAssignmentRole, string> = {
  MEMBER: "Membro",
  COMMANDER: "Comandante da Equipe",
  DRIVER: "Motorista",
  THIRD_MAN: "3º Homem",
  FOURTH_MAN: "4º Homem",
  MOTO_2: "Moto 2",
  MOTO_3: "Moto 3",
};

export function dejemShiftModality(shiftType: string): ScaleModality | null {
  if (shiftType === "FT") return "FT";
  if (shiftType === "ROCAM") return "ROCAM";
  return null;
}

export function dejemTeamRoleLabels(shiftType: string): readonly TeamRole[] {
  const modality = dejemShiftModality(shiftType);
  if (!modality) return [];
  return teamRolesFor(modality);
}

export { FT_TEAM_ROLES, ROCAM_TEAM_ROLES, emptyRoleAssignments, setRoleUser };
export type { RoleAssignments, TeamRole };

export function membersToDejemRoleAssignments(
  shiftType: string,
  members: { user_id: number; role?: DejemAssignmentRole | string | null }[],
): RoleAssignments {
  const modality = dejemShiftModality(shiftType);
  if (!modality) return {};
  const assignments = emptyRoleAssignments(modality);
  for (const m of members) {
    const role = (m.role ?? "MEMBER") as DejemAssignmentRole;
    const label = ROLE_TO_LABEL[role];
    if (label && label in assignments) {
      assignments[label] = m.user_id;
    }
  }
  return assignments;
}

export function roleAssignmentsToPayload(
  assignments: RoleAssignments,
): { user_id: number; role: DejemAssignmentRole }[] {
  const out: { user_id: number; role: DejemAssignmentRole }[] = [];
  for (const [label, uid] of Object.entries(assignments)) {
    if (typeof uid !== "number") continue;
    const role = LABEL_TO_ROLE[label];
    if (!role) continue;
    out.push({ user_id: uid, role });
  }
  return out;
}

export function assignmentRoleLabel(role: DejemAssignmentRole | string | null | undefined): string {
  if (!role) return ROLE_TO_LABEL.MEMBER;
  return ROLE_TO_LABEL[role as DejemAssignmentRole] ?? String(role);
}
