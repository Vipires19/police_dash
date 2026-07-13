import { useCallback, useEffect, useMemo, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as dejemApi from "@/services/dejemApi";
import {
  DEJEM_MONTH_STATUS_LABELS,
  dejemMonthLabel,
  type DejemAllocationPublic,
  type DejemInterestPublic,
  type DejemMonthPublic,
} from "@/types/dejem";

export function DejemMyPage() {
  const { token } = useAuth();
  const [months, setMonths] = useState<DejemMonthPublic[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [interest, setInterest] = useState<DejemInterestPublic | null>(null);
  const [allocation, setAllocation] = useState<DejemAllocationPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const [wantParticipate, setWantParticipate] = useState(true);
  const [desiredSlots, setDesiredSlots] = useState(1);

  const selected = useMemo(
    () => months.find((m) => m.id === selectedId) ?? null,
    [months, selectedId],
  );

  const isOpen = selected?.status === "OPEN_INTEREST";
  const isDistributed =
    selected?.status === "DISTRIBUTED" ||
    selected?.status === "OPEN_SHIFTS" ||
    selected?.status === "FINISHED";

  const loadMonths = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const list = await dejemApi.listDejemMonths(token);
      setMonths(list);
      setSelectedId((prev) => {
        if (prev && list.some((m) => m.id === prev)) return prev;
        const open = list.find((m) => m.status === "OPEN_INTEREST");
        return open?.id ?? list[0]?.id ?? null;
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar meses DEJEM");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const loadInterest = useCallback(async (monthId: number) => {
    if (!token) return;
    try {
      const row = await dejemApi.getMyDejemInterest(token, monthId);
      setInterest(row);
      if (row) {
        setWantParticipate(row.interested);
        setDesiredSlots(row.interested ? Math.max(1, row.desired_slots) : 1);
      } else {
        setWantParticipate(true);
        setDesiredSlots(1);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar manifestação");
    }
  }, [token]);

  const loadAllocation = useCallback(async (monthId: number, distributed: boolean) => {
    if (!token) return;
    if (!distributed) {
      setAllocation(null);
      return;
    }
    try {
      const row = await dejemApi.getMyDejemAllocation(token, monthId);
      setAllocation(row);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar saldo");
    }
  }, [token]);

  useEffect(() => {
    void loadMonths();
  }, [loadMonths]);

  useEffect(() => {
    if (selectedId == null || !selected) {
      setInterest(null);
      setAllocation(null);
      return;
    }
    void loadInterest(selectedId);
    void loadAllocation(
      selectedId,
      selected.status === "DISTRIBUTED" ||
        selected.status === "OPEN_SHIFTS" ||
        selected.status === "FINISHED",
    );
  }, [selectedId, selected, loadInterest, loadAllocation]);

  const onSave = async () => {
    if (!token || !selected) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    const payload = {
      interested: wantParticipate,
      desired_slots: wantParticipate ? desiredSlots : 0,
    };
    try {
      const saved = interest
        ? await dejemApi.updateMyDejemInterest(token, selected.id, payload)
        : await dejemApi.createMyDejemInterest(token, selected.id, payload);
      setInterest(saved);
      setMsg("Manifestação salva com sucesso.");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao salvar manifestação");
    } finally {
      setBusy(false);
    }
  };

  const onCancel = async () => {
    if (!token || !selected || !interest) return;
    if (!window.confirm("Remover sua manifestação deste mês?")) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.deleteMyDejemInterest(token, selected.id);
      setInterest(null);
      setWantParticipate(true);
      setDesiredSlots(1);
      setMsg("Manifestação removida.");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao remover manifestação");
    } finally {
      setBusy(false);
    }
  };

  return (
    <OperationalLayout>
      <header className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">DEJEM</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Minha DEJEM</h1>
        <p className="mt-2 max-w-xl text-sm text-zinc-400">
          Manifestação de interesse e saldo individual de vagas do mês.
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

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : months.length === 0 ? (
        <p className="text-sm text-zinc-400">Nenhum mês DEJEM disponível no momento.</p>
      ) : (
        <div className="space-y-6">
          <label className="block max-w-sm text-sm">
            <span className="mb-1.5 block text-zinc-400">Mês</span>
            <select
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
              value={selectedId ?? ""}
              onChange={(e) => setSelectedId(Number(e.target.value))}
            >
              {months.map((m) => (
                <option key={m.id} value={m.id}>
                  {dejemMonthLabel(m.year, m.month)} — {DEJEM_MONTH_STATUS_LABELS[m.status]}
                </option>
              ))}
            </select>
          </label>

          {selected && (
            <section className="max-w-xl rounded-xl border border-zinc-800 bg-zinc-950/70 px-6 py-6">
              <h2 className="text-lg font-semibold tracking-wide text-zinc-50">
                DEJEM — {dejemMonthLabel(selected.year, selected.month)}
              </h2>

              <div className="mt-5 space-y-3 border-y border-zinc-800 py-5 text-sm">
                <div className="flex items-baseline justify-between gap-4">
                  <span className="text-zinc-400">Total de vagas da Companhia</span>
                  <span className="font-medium tabular-nums text-zinc-100">
                    {selected.total_available_slots}
                  </span>
                </div>
                <div className="flex items-baseline justify-between gap-4">
                  <span className="text-zinc-400">Limite mensal por policial</span>
                  <span className="font-medium tabular-nums text-zinc-100">
                    {selected.monthly_limit_per_officer}
                  </span>
                </div>
                <div className="flex items-baseline justify-between gap-4">
                  <span className="text-zinc-400">Status</span>
                  <span className="font-medium text-zinc-100">
                    {DEJEM_MONTH_STATUS_LABELS[selected.status]}
                  </span>
                </div>
              </div>

              {isDistributed && (
                <div className="mt-6 rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-4">
                  <p className="text-xs uppercase tracking-wider text-zinc-500">Saldo</p>
                  {allocation ? (
                    <dl className="mt-3 space-y-2 text-sm">
                      <div className="flex justify-between gap-4">
                        <dt className="text-zinc-400">Saldo inicial</dt>
                        <dd className="tabular-nums font-medium text-zinc-100">
                          {allocation.allocated_slots}
                        </dd>
                      </div>
                      <div className="flex justify-between gap-4">
                        <dt className="text-zinc-400">Utilizadas</dt>
                        <dd className="tabular-nums font-medium text-zinc-100">
                          {allocation.used_slots}
                        </dd>
                      </div>
                      <div className="flex justify-between gap-4 border-t border-zinc-800 pt-2">
                        <dt className="text-zinc-400">Disponíveis</dt>
                        <dd className="tabular-nums font-medium text-zinc-50">
                          {allocation.remaining_slots}
                        </dd>
                      </div>
                    </dl>
                  ) : (
                    <p className="mt-2 text-sm text-zinc-500">
                      Você não recebeu vagas neste mês.
                    </p>
                  )}
                  <p className="mt-3 text-xs text-zinc-500">
                    A inscrição nas escalas DEJEM estará disponível em breve.
                  </p>
                </div>
              )}

              {isOpen ? (
                <div className="mt-6 space-y-5">
                  <div>
                    <p className="mb-3 text-sm font-medium text-zinc-200">Manifestação de Interesse</p>
                    <div className="space-y-2">
                      <label className="flex cursor-pointer items-center gap-3 text-sm text-zinc-200">
                        <input
                          type="radio"
                          name="want"
                          checked={wantParticipate}
                          onChange={() => setWantParticipate(true)}
                          className="accent-zinc-200"
                        />
                        Quero participar
                      </label>
                      <label className="flex cursor-pointer items-center gap-3 text-sm text-zinc-200">
                        <input
                          type="radio"
                          name="want"
                          checked={!wantParticipate}
                          onChange={() => setWantParticipate(false)}
                          className="accent-zinc-200"
                        />
                        Não desejo participar
                      </label>
                    </div>
                  </div>

                  {wantParticipate && (
                    <label className="block text-sm">
                      <span className="mb-1.5 block text-zinc-400">Quantidade desejada</span>
                      <input
                        type="number"
                        min={1}
                        max={selected.monthly_limit_per_officer}
                        value={desiredSlots}
                        onChange={(e) => setDesiredSlots(Number(e.target.value))}
                        className="w-28 rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 tabular-nums text-zinc-100"
                      />
                      <span className="mt-1 block text-xs text-zinc-500">
                        Entre 1 e {selected.monthly_limit_per_officer}
                      </span>
                    </label>
                  )}

                  <p className="border-t border-zinc-800 pt-4 text-xs leading-relaxed text-zinc-500">
                    A quantidade informada representa apenas uma preferência. A distribuição será
                    realizada automaticamente após o encerramento da manifestação, respeitando as
                    regras operacionais da Companhia.
                  </p>

                  <div className="flex flex-wrap gap-3">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => void onSave()}
                      className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 transition hover:bg-white disabled:opacity-50"
                    >
                      {busy ? "Salvando…" : "Salvar"}
                    </button>
                    {interest && (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void onCancel()}
                        className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-500 hover:bg-zinc-900 disabled:opacity-50"
                      >
                        Remover manifestação
                      </button>
                    )}
                  </div>
                </div>
              ) : !isDistributed ? (
                <div className="mt-6 space-y-4">
                  <p className="text-sm text-amber-200/90">
                    A manifestação de interesse já foi encerrada.
                    {selected.status === "DISTRIBUTED_PENDING"
                      ? " Aguardando a distribuição das vagas."
                      : ""}
                  </p>
                  {interest ? (
                    <div className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-4 py-3 text-sm text-zinc-300">
                      <p>
                        Sua resposta:{" "}
                        <span className="text-zinc-100">
                          {interest.interested ? "Quero participar" : "Não desejo participar"}
                        </span>
                      </p>
                      {interest.interested && (
                        <p className="mt-1">
                          Quantidade desejada:{" "}
                          <span className="tabular-nums text-zinc-100">{interest.desired_slots}</span>
                        </p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-zinc-500">Você não registrou manifestação neste mês.</p>
                  )}
                </div>
              ) : null}
            </section>
          )}
        </div>
      )}
    </OperationalLayout>
  );
}
