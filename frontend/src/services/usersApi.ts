import type { OrganizationalUnit, Role, User } from "@/types";
import { apiFetch } from "./api";

export interface UserProfilePatch {
  full_name?: string | null;
  re?: string | null;
  address?: string | null;
  phone?: string | null;
  birth_date?: string | null;
  blood_type?: string | null;
  patente?: string | null;
  nome_guerra?: string | null;
  is_active?: boolean | null;
  role?: Role | null;
  organizational_unit?: OrganizationalUnit | null;
}

export async function listEfetivo(token: string): Promise<User[]> {
  return apiFetch<User[]>("/users/efetivo", { method: "GET", token });
}

export async function getUser(token: string, userId: number): Promise<User> {
  return apiFetch<User>(`/users/${userId}`, { method: "GET", token });
}

export async function patchUser(token: string, userId: number, body: UserProfilePatch): Promise<User> {
  return apiFetch<User>(`/users/${userId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(body),
  });
}

export async function reorderEfetivo(
  token: string,
  payload: { patente: string; ordered_user_ids: number[] },
): Promise<void> {
  await apiFetch<unknown>("/users/efetivo/reorder", {
    method: "PUT",
    token,
    body: JSON.stringify({
      patente: payload.patente,
      ordered_user_ids: payload.ordered_user_ids,
    }),
  });
}
