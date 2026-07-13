import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as dejemApi from "@/services/dejemApi";
import {
  ORGANIZATIONAL_UNIT_LABELS,
  isDejemReopenRole,
  type OrganizationalUnit,
  type Role,
} from "@/types";
import {
  DEJEM_MONTH_NAMES,
  DEJEM_MONTH_STATUS_LABELS,
  dejemMonthLabel,
  type DejemAllocationAdminRow,
  type DejemDistributionPreview,
  type DejemInterestAdminRow,
  type DejemMonthPublic,
} from "@/types/dejem";

const ROLE_LABELS: Record<string, string> = {
  ADMIN: "Admin",
  CMD_TATICO: "Cmd. Tático",
  TAT_CMD: "Tat. Cmd",
  ADM: "ADM",
  N90: "N90",
  BRACAL: "Braçal",
  ESTAGIO: "Estágio",
};

export function DejemAdminPage() {
  const { token, user, isDejemAdmin } = useAuth();
  const canReopen = user ? isDejemReopenRole(user.role) : false;

  const [months, setMonths] = useState<DejemMonthPublic[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [interests, setInterests] = useState<DejemInterestAdminRow[]>([]);
  const [allocations, setAllocations] = useState<DejemAllocationAdminRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const [previewOpen, setPreviewOpen] = useState(false);
  const [preview, setPreview] = useState<DejemDistributionPreview | null>(null);
  const [previewMonth, setPreviewMonth] = useState<DejemMonthPublic | null>(null);

  const now = new Date();
  const [formYear, setFormYear] = useState(now.getFullYear());
  const [formMonth, setFormMonth] = useState(now.getMonth() + 1);
  const [formSlots, setFormSlots] = useState(97);
  const [formLimit, setFormLimit] = useState(10);

  const selected = useMemo(
    () => months.find((m) => m.id === selectedId) ?? null,
    [months, selectedId],
  );

  const loadMonths = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const list = await dejemApi.listDejemMonths(token);
      setMonths(list);
      setSelectedId((prev) => {
        if (prev && list.some((m) => m.id === prev)) return prev;
        return list[0]?.id ?? null;
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar meses DEJEM");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const loadInterests = useCallback(
    async (monthId: number) => {
      if (!token) return;
      try {
        const rows = await dejemApi.listDejemMonthInterests(token, monthId);
        setInterests(rows);
      } catch (e) {
        setError(e instanceof ApiError ? e.detail : "Erro ao carregar interessados");
      }
    },
    [token],
  );

  const loadAllocations = useCallback(
    async (monthId: number, status: DejemMonthPublic["status"]) => {
      if (!token) return;
      if (status !== "DISTRIBUTED" && status !== "OPEN_SHIFTS" && status !== "FINISHED") {
        setAllocations([]);
        return;
      }
      try {
        const rows = await dejemApi.listDejemMonthAllocations(token, monthId);
        setAllocations(rows);
      } catch (e) {
        setError(e instanceof ApiError ? e.detail : "Erro ao carregar alocações");
      }
    },
    [token],
  );

  useEffect(() => {
    void loadMonths();
  }, [loadMonths]);

  useEffect(() => {
    if (selectedId == null || !selected) {
      setInterests([]);
      setAllocations([]);
      return;
    }
    void loadInterests(selectedId);
    void loadAllocations(selectedId, selected.status);
  }, [selectedId, selected, loadInterests, loadAllocations]);

  if (!isDejemAdmin) {
    return <Navigate to="/dejem/my" replace />;
  }

  const onCreate = async () => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const created = await dejemApi.createDejemMonth(token, {
        year: formYear,
        month: formMonth,
        total_available_slots: formSlots,
        monthly_limit_per_officer: formLimit,
      });
      setMsg(`Mês ${dejemMonthLabel(created.year, created.month)} criado.`);
      await loadMonths();
      setSelectedId(created.id);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao criar mês");
    } finally {
      setBusy(false);
    }
  };

  const onCloseInterest = async (month: DejemMonthPublic) => {
    if (!token) return;
    if (
      !window.confirm(
        `Encerrar a manifestação de ${dejemMonthLabel(month.year, month.month)}? Após isso, nenhum policial poderá alterar sua resposta.`,
      )
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const updated = await dejemApi.closeDejemInterest(token, month.id);
      setMsg("Manifestação encerrada. Status: aguardando distribuição.");
      setMonths((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setSelectedId(updated.id);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao encerrar manifestação");
    } finally {
      setBusy(false);
    }
  };

  const openDistributeModal = async (month: DejemMonthPublic) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const p = await dejemApi.getDejemDistributionPreview(token, month.id);
      setPreview(p);
      setPreviewMonth(month);
      setPreviewOpen(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao preparar distribuição");
    } finally {
      setBusy(false);
    }
  };

  const confirmDistribute = async () => {
    if (!token || !previewMonth) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const res = await dejemApi.distributeDejemMonth(token, previewMonth.id);
      setMonths((prev) => prev.map((m) => (m.id === res.month.id ? res.month : m)));
      setSelectedId(res.month.id);
      setAllocations(res.allocations);
      setPreviewOpen(false);
      setPreview(null);
      setPreviewMonth(null);
      setMsg(
        `Distribuição concluída. ${res.allocations.length} saldos criados` +
          (res.leftover_slots > 0 ? ` (${res.leftover_slots} vagas sem destinatário).` : "."),
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao distribuir vagas");
    } finally {
      setBusy(false);
    }
  };

  const onReopen = async (month: DejemMonthPublic) => {
    if (!token) return;
    if (
      !window.confirm(
        `Reabrir a distribuição de ${dejemMonthLabel(month.year, month.month)}? Os saldos atuais serão excluídos.`,
      )
    ) {
      return;
    }
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const updated = await dejemApi.reopenDejemDistribution(token, month.id);
      setMonths((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      setAllocations([]);
      setSelectedId(updated.id);
      setMsg("Distribuição reaberta. É possível distribuir novamente.");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao reabrir distribuição");
    } finally {
      setBusy(false);
    }
  };

  const interestedOnly = interests.filter((i) => i.interested);
  const showAllocations =
    selected &&
    (selected.status === "DISTRIBUTED" ||
      selected.status === "OPEN_SHIFTS" ||
      selected.status === "FINISHED");

  return (
    <OperationalLayout>
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">DEJEM</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Administração DEJEM</h1>
        <p className="mt-2 max-w-xl text-sm text-zinc-400">
          Manifestação de interesse, distribuição automática de vagas e saldos individuais.
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </p>
      )}
      {msg && (
        <p className="mb-4 rounded-lg border border-emerald-900/50 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">
          {msg}
        </p>
      )}

      <section className="mb-8 rounded-xl border border-zinc-800 bg-zinc-950/60 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
          Novo mês DEJEM
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Ano</span>
            <input
              type="number"
              min={2000}
              max={2100}
              value={formYear}
              onChange={(e) => setFormYear(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Mês</span>
            <select
              value={formMonth}
              onChange={(e) => setFormMonth(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            >
              {DEJEM_MONTH_NAMES.slice(1).map((name, idx) => (
                <option key={name} value={idx + 1}>
                  {name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Total de vagas</span>
            <input
              type="number"
              min={0}
              value={formSlots}
              onChange={(e) => setFormSlots(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Limite mensal</span>
            <input
              type="number"
              min={1}
              value={formLimit}
              onChange={(e) => setFormLimit(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => void onCreate()}
          className="mt-4 rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 transition hover:bg-white disabled:opacity-50"
        >
          Criar mês
        </button>
      </section>

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : months.length === 0 ? (
        <p className="text-sm text-zinc-400">Nenhum mês cadastrado.</p>
      ) : (
        <div className="space-y-6">
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-zinc-800 bg-zinc-900/60 text-xs uppercase tracking-wider text-zinc-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Mês</th>
                  <th className="px-4 py-3 font-medium">Vagas</th>
                  <th className="px-4 py-3 font-medium">Limite</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Interessados</th>
                  <th className="px-4 py-3 font-medium">Ações</th>
                </tr>
              </thead>
              <tbody>
                {months.map((m) => {
                  const active = m.id === selectedId;
                  return (
                    <tr
                      key={m.id}
                      className={[
                        "border-b border-zinc-900/80 cursor-pointer transition-colors",
                        active ? "bg-zinc-900/70" : "hover:bg-zinc-900/40",
                      ].join(" ")}
                      onClick={() => setSelectedId(m.id)}
                    >
                      <td className="px-4 py-3 font-medium text-zinc-100">
                        {dejemMonthLabel(m.year, m.month)}
                      </td>
                      <td className="px-4 py-3 tabular-nums text-zinc-300">
                        {m.total_available_slots}
                      </td>
                      <td className="px-4 py-3 tabular-nums text-zinc-300">
                        {m.monthly_limit_per_officer}
                      </td>
                      <td className="px-4 py-3 text-zinc-300">
                        {DEJEM_MONTH_STATUS_LABELS[m.status]}
                      </td>
                      <td className="px-4 py-3 tabular-nums text-zinc-300">
                        {m.interested_count}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          {m.status === "OPEN_INTEREST" && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={(e) => {
                                e.stopPropagation();
                                void onCloseInterest(m);
                              }}
                              className="rounded-md border border-amber-800/70 px-2.5 py-1 text-xs text-amber-200 hover:bg-amber-950/40 disabled:opacity-50"
                            >
                              Encerrar Manifestação
                            </button>
                          )}
                          {m.status === "DISTRIBUTED_PENDING" && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={(e) => {
                                e.stopPropagation();
                                void openDistributeModal(m);
                              }}
                              className="rounded-md border border-emerald-800/70 px-2.5 py-1 text-xs text-emerald-200 hover:bg-emerald-950/40 disabled:opacity-50"
                            >
                              Distribuir Vagas
                            </button>
                          )}
                          {m.status === "DISTRIBUTED" && canReopen && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={(e) => {
                                e.stopPropagation();
                                void onReopen(m);
                              }}
                              className="rounded-md border border-zinc-600 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
                            >
                              Reabrir Distribuição
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {selected && !showAllocations && (
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-300">
                Interessados — {dejemMonthLabel(selected.year, selected.month)}
                <span className="ml-2 font-normal normal-case tracking-normal text-zinc-500">
                  ({interestedOnly.length} desejam participar / {interests.length} manifestações)
                </span>
              </h2>

              {interests.length === 0 ? (
                <p className="text-sm text-zinc-500">Nenhuma manifestação registrada neste mês.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-zinc-800">
                  <table className="min-w-full text-left text-sm">
                    <thead className="border-b border-zinc-800 bg-zinc-900/60 text-xs uppercase tracking-wider text-zinc-500">
                      <tr>
                        <th className="px-4 py-3 font-medium">Nome</th>
                        <th className="px-4 py-3 font-medium">Pelotão</th>
                        <th className="px-4 py-3 font-medium">Role</th>
                        <th className="px-4 py-3 font-medium">Participa</th>
                        <th className="px-4 py-3 font-medium">Qtd. desejada</th>
                        <th className="px-4 py-3 font-medium">Data</th>
                      </tr>
                    </thead>
                    <tbody>
                      {interests.map((row) => (
                        <tr key={row.id} className="border-b border-zinc-900/80">
                          <td className="px-4 py-3 text-zinc-100">
                            {row.patente} {row.nome_guerra}
                          </td>
                          <td className="px-4 py-3 text-zinc-300">
                            {ORGANIZATIONAL_UNIT_LABELS[row.organizational_unit as OrganizationalUnit] ??
                              row.organizational_unit}
                          </td>
                          <td className="px-4 py-3 text-zinc-300">
                            {ROLE_LABELS[row.role as Role] ?? row.role}
                          </td>
                          <td className="px-4 py-3 text-zinc-300">
                            {row.interested ? "Sim" : "Não"}
                          </td>
                          <td className="px-4 py-3 tabular-nums text-zinc-300">
                            {row.interested ? row.desired_slots : "—"}
                          </td>
                          <td className="px-4 py-3 text-zinc-400">
                            {new Date(row.created_at).toLocaleString("pt-BR")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {selected && showAllocations && (
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-300">
                Resultado da distribuição — {dejemMonthLabel(selected.year, selected.month)}
              </h2>
              {allocations.length === 0 ? (
                <p className="text-sm text-zinc-500">Nenhuma alocação registrada.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-zinc-800">
                  <table className="min-w-full text-left text-sm">
                    <thead className="border-b border-zinc-800 bg-zinc-900/60 text-xs uppercase tracking-wider text-zinc-500">
                      <tr>
                        <th className="px-4 py-3 font-medium">Policial</th>
                        <th className="px-4 py-3 font-medium">Pelotão</th>
                        <th className="px-4 py-3 font-medium">Qtd. desejada</th>
                        <th className="px-4 py-3 font-medium">Vagas recebidas</th>
                        <th className="px-4 py-3 font-medium">Saldo disponível</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allocations.map((row) => (
                        <tr key={row.id} className="border-b border-zinc-900/80">
                          <td className="px-4 py-3 text-zinc-100">
                            {row.patente} {row.nome_guerra}
                          </td>
                          <td className="px-4 py-3 text-zinc-300">
                            {ORGANIZATIONAL_UNIT_LABELS[row.organizational_unit as OrganizationalUnit] ??
                              row.organizational_unit}
                          </td>
                          <td className="px-4 py-3 tabular-nums text-zinc-300">{row.desired_slots}</td>
                          <td className="px-4 py-3 tabular-nums text-zinc-100">{row.allocated_slots}</td>
                          <td className="px-4 py-3 tabular-nums text-zinc-100">{row.remaining_slots}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
        </div>
      )}

      {previewOpen && preview && previewMonth && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-950 p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-zinc-50">Distribuir Vagas</h3>
            <p className="mt-1 text-sm text-zinc-400">
              {dejemMonthLabel(previewMonth.year, previewMonth.month)}
            </p>
            <dl className="mt-5 space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-400">Total de vagas</dt>
                <dd className="tabular-nums text-zinc-100">{preview.total_available_slots}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-400">Interessados</dt>
                <dd className="tabular-nums text-zinc-100">{preview.interested_count}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-400">Limite mensal</dt>
                <dd className="tabular-nums text-zinc-100">{preview.monthly_limit_per_officer}</dd>
              </div>
              <div className="flex justify-between gap-4 border-t border-zinc-800 pt-2">
                <dt className="text-zinc-400">Quantidade base</dt>
                <dd className="tabular-nums text-zinc-100">{preview.base_quantity}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-zinc-400">Vagas remanescentes</dt>
                <dd className="tabular-nums text-zinc-100">{preview.remaining_after_base}</dd>
              </div>
            </dl>
            <p className="mt-4 text-xs leading-relaxed text-zinc-500">
              A redistribuição das sobras segue a antiguidade do efetivo (patente e ordem
              institucional). A operação só pode ser executada uma vez, salvo reabertura por
              ADMIN/CMD_TATICO.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  setPreviewOpen(false);
                  setPreview(null);
                  setPreviewMonth(null);
                }}
                className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void confirmDistribute()}
                className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
              >
                {busy ? "Distribuindo…" : "Confirmar distribuição"}
              </button>
            </div>
          </div>
        </div>
      )}
    </OperationalLayout>
  );
}
