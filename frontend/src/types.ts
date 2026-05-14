export type Role = "ADMIN" | "N90" | "TAT_CMD" | "BRACAL" | "ESTAGIO";
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
  status: Status;
  created_at: string;
}

export const STAFF_EDITOR_ROLES: Role[] = ["ADMIN", "N90", "TAT_CMD"];

export const APPROVER_ROLES: Role[] = ["ADMIN", "N90", "TAT_CMD"];

export function isStaffEditor(role: Role): boolean {
  return STAFF_EDITOR_ROLES.includes(role);
}
