import type { User } from "@/types";
import { apiFetch } from "./api";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  patente: string;
  nome_guerra: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function loginRequest(payload: LoginPayload): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
    token: null,
  });
}

export async function registerRequest(payload: RegisterPayload): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    token: null,
  });
}

export async function meRequest(token: string): Promise<User> {
  return apiFetch<User>("/users/me", { method: "GET", token });
}

export async function pendingUsersRequest(token: string): Promise<User[]> {
  return apiFetch<User[]>("/users/pending", { method: "GET", token });
}

export async function approveUserRequest(
  token: string,
  userId: number,
  body: { decision: "approve" | "reject"; role?: string; organizational_unit?: string },
): Promise<User> {
  return apiFetch<User>(`/users/approve/${userId}`, {
    method: "POST",
    body: JSON.stringify(body),
    token,
  });
}
