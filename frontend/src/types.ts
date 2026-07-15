export type Role = "ADMIN" | "CMD_TATICO" | "TAT_CMD" | "ADM" | "N90" | "BRACAL" | "ESTAGIO";
export type OrganizationalUnit = "FIRST_PLATOON" | "SECOND_PLATOON" | "COMPANY_ADMIN";
export type Status = "PENDING" | "APPROVED" | "REJECTED";

export interface User {
  id: number;
  email: string;
  patente: string;
  nome_guerra: string;
  full_name: string | null;
  re: string | null;
  address: string | null;
  phone: string | null;
  birth_date: string | null;
  blood_type: string | null;
  display_order: number;
  is_active: boolean;
  role: Role;
  organizational_unit: OrganizationalUnit;
  status: Status;
  created_at: string;
}

export const ALL_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "TAT_CMD", "ADM", "N90", "BRACAL", "ESTAGIO"];

export const ORGANIZATIONAL_UNITS: OrganizationalUnit[] = [
  "FIRST_PLATOON",
  "SECOND_PLATOON",
  "COMPANY_ADMIN",
];

/** Labels curtos (badges, selects de transferência). */
export const ORGANIZATIONAL_UNIT_LABELS: Record<OrganizationalUnit, string> = {
  FIRST_PLATOON: "1º Pelotão",
  SECOND_PLATOON: "2º Pelotão",
  COMPANY_ADMIN: "Administração da Companhia",
};

/** Títulos de seção na listagem de efetivo (visão Companhia). */
export const ORGANIZATIONAL_UNIT_SECTION_LABELS: Record<OrganizationalUnit, string> = {
  FIRST_PLATOON: "1º Pelotão",
  SECOND_PLATOON: "2º Pelotão",
  COMPANY_ADMIN: "Administração",
};

export const ORGANIZATIONAL_UNIT_ORDER: OrganizationalUnit[] = [
  "FIRST_PLATOON",
  "SECOND_PLATOON",
  "COMPANY_ADMIN",
];

/** Branding fixo da plataforma. */
export const PLATFORM_BRAND = "CIA FT";

/** Título do Dashboard conforme unidade organizacional. */
export function dashboardTitleForUnit(unit: OrganizationalUnit): string {
  switch (unit) {
    case "FIRST_PLATOON":
      return "1º Pelotão Força Tática/ROCAM";
    case "SECOND_PLATOON":
      return "2º Pelotão Força Tática/ROCAM";
    case "COMPANY_ADMIN":
      return "Companhia Força Tática/ROCAM";
  }
}

/** Identificação contextual na sidebar (abaixo do brand). */
export function sidebarContextLabel(user: Pick<User, "role" | "organizational_unit">): string {
  if (user.role === "ADMIN" || user.role === "CMD_TATICO") {
    return "COMANDO";
  }
  switch (user.organizational_unit) {
    case "FIRST_PLATOON":
      return "1º PELOTÃO";
    case "SECOND_PLATOON":
      return "2º PELOTÃO";
    case "COMPANY_ADMIN":
      return "ADMINISTRAÇÃO";
  }
}

export const STAFF_EDITOR_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "N90", "TAT_CMD"];

export const SCALE_EDITOR_ROLES: Role[] = ["ADMIN", "N90"];

/** Administração do módulo DEJEM (sem alterar RBAC dos demais módulos). */
export const DEJEM_ADMIN_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "N90", "TAT_CMD", "ADM"];

/** Reabrir distribuição DEJEM. */
export const DEJEM_REOPEN_ROLES: Role[] = ["ADMIN", "CMD_TATICO"];

/** Escalas DEJEM — edição e visualização. */
export const DEJEM_SHIFT_EDITOR_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "ADM"];
export const DEJEM_SHIFT_VIEWER_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "ADM", "TAT_CMD"];

export const APPROVER_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "N90", "TAT_CMD"];

/** Criação e edição operacional de viaturas (comando + braçal; sem estagiário). */
export const VEHICLE_EDITOR_ROLES: Role[] = [...APPROVER_ROLES, "BRACAL"];

export const COMPENSATION_CREATOR_ROLES: Role[] = ["ADMIN", "CMD_TATICO", "N90", "TAT_CMD", "BRACAL"];

export const COMPANY_EFETIVO_VIEW_ROLES: Role[] = ["ADMIN", "CMD_TATICO"];

export function isStaffEditor(role: Role): boolean {
  return STAFF_EDITOR_ROLES.includes(role);
}

export function isApproverRole(role: Role): boolean {
  return APPROVER_ROLES.includes(role);
}

export function isDejemAdminRole(role: Role): boolean {
  return DEJEM_ADMIN_ROLES.includes(role);
}

export function isDejemReopenRole(role: Role): boolean {
  return DEJEM_REOPEN_ROLES.includes(role);
}

export function isDejemShiftViewerRole(role: Role): boolean {
  return DEJEM_SHIFT_VIEWER_ROLES.includes(role);
}

export function isDejemShiftEditorRole(role: Role): boolean {
  return DEJEM_SHIFT_EDITOR_ROLES.includes(role);
}

export function canViewCompanyEfetivo(role: Role): boolean {
  return COMPANY_EFETIVO_VIEW_ROLES.includes(role);
}

export function canRegisterCompensationRole(role: Role): boolean {
  if (role === "ESTAGIO") return false;
  return COMPENSATION_CREATOR_ROLES.includes(role);
}
