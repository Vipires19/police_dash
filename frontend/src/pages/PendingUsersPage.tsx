import { useEffect, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import type { Role, User } from "@/types";
import { ApiError } from "@/services/api";
import * as authApi from "@/services/authApi";

const ROLES: Role[] = ["ADMIN", "N90", "TAT_CMD", "BRACAL", "ESTAGIO"];

export function PendingUsersPage() {
  const { token, refreshUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const list = await authApi.pendingUsersRequest(token);
      setUsers(list);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar pendentes");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  async function handleDecision(u: User, decision: "approve" | "reject", role?: Role) {
    if (!token) return;
    setActionId(u.id);
    setError(null);
    try {
      await authApi.approveUserRequest(token, u.id, {
        decision,
        role: decision === "approve" ? role : undefined,
      });
      await load();
      void refreshUser();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro na operação");
    } finally {
      setActionId(null);
    }
  }

  return (
    <OperationalLayout>
      <section className="space-y-4">
        <header>
          <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Administração</p>
          <h2 className="text-2xl font-semibold text-zinc-50">Cadastros pendentes</h2>
          <p className="text-sm text-zinc-400">
            Perfis autorizados: ADMIN, N90 e TAT_CMD podem aprovar ou rejeitar novos usuários.
          </p>
        </header>
        {error && (
          <div className="rounded-md border border-red-900/60 bg-red-950/40 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        )}
        <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950/70">
          {loading ? (
            <p className="p-6 text-sm text-zinc-400">Carregando fila…</p>
          ) : users.length === 0 ? (
            <p className="p-6 text-sm text-zinc-400">Nenhum cadastro pendente.</p>
          ) : (
            <table className="min-w-full divide-y divide-zinc-800 text-sm">
              <thead className="bg-black/40 text-left text-xs uppercase tracking-wide text-zinc-500">
                <tr>
                  <th className="px-4 py-3">E-mail</th>
                  <th className="px-4 py-3">Patente</th>
                  <th className="px-4 py-3">Nome guerra</th>
                  <th className="px-4 py-3">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-900">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-900/40">
                    <td className="px-4 py-3 text-zinc-300">{u.email}</td>
                    <td className="px-4 py-3 text-zinc-200">{u.patente}</td>
                    <td className="px-4 py-3 text-zinc-200">{u.nome_guerra}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <select
                          id={`role-${u.id}`}
                          defaultValue="BRACAL"
                          className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-100"
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            disabled={actionId === u.id}
                            onClick={() => {
                              const sel = document.getElementById(
                                `role-${u.id}`,
                              ) as HTMLSelectElement;
                              void handleDecision(u, "approve", sel.value as Role);
                            }}
                            className="rounded-md border border-zinc-600 px-3 py-1 text-xs text-zinc-100 hover:bg-zinc-900 disabled:opacity-50"
                          >
                            Aprovar
                          </button>
                          <button
                            type="button"
                            disabled={actionId === u.id}
                            onClick={() => void handleDecision(u, "reject")}
                            className="rounded-md border border-zinc-800 px-3 py-1 text-xs text-zinc-400 hover:border-red-900 hover:text-red-200 disabled:opacity-50"
                          >
                            Rejeitar
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </OperationalLayout>
  );
}
