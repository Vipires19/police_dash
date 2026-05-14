const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { token?: string | null } = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = init.token ?? localStorage.getItem("token");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const { token: _t, ...rest } = init;
  const res = await fetch(`${API_URL}${path}`, { ...rest, headers });
  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text) as unknown;
    } catch {
      data = { detail: text };
    }
  }
  if (!res.ok) {
    const obj = data as { detail?: unknown };
    const detail =
      typeof obj?.detail === "string"
        ? obj.detail
        : Array.isArray(obj?.detail)
          ? obj.detail
              .map((d: { msg?: string }) => d.msg ?? JSON.stringify(d))
              .join("; ")
          : res.statusText;
    throw new ApiError(res.status, detail || "Erro na requisição");
  }
  return data as T;
}
