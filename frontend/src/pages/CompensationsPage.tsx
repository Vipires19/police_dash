import { useCallback, useEffect, useMemo, useState } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import {
  compensationStatusBadgeClass,
  compensationStatusLabel,
} from "@/components/compensations/statusStyles";
import { OrgUnitBadge, orgBadgeVariantForViewer } from "@/components/OrgUnitBadge";
import { useAuth } from "@/hooks/AuthContext";
import type { User } from "@/types";
import type {
  CompensationEventLogPublic,
  CompensationEventPublic,
  CompensationEventStatus,
  CompensationType,
} from "@/types/compensations";
import {
  COMPENSATION_TYPE_LABELS,
  MERIT_COMPENSATION_TYPES,
} from "@/types/compensations";
import { ApiError } from "@/services/api";
import * as compensationsApi from "@/services/compensationsApi";
import * as usersApi from "@/services/usersApi";

export function CompensationsPage() {
  const { token, user, canRegisterCompensation, isApprover } = useAuth();
  const year = new Date().getFullYear();

  const [efetivo, setEfetivo] = useState<User[]>([]);
  const [events, setEvents] = useState<CompensationEventPublic[]>([]);
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof compensationsApi.getCompensationSummary>> | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<CompensationEventStatus | "">("");
  const [typeFilter, setTypeFilter] = useState<CompensationType | "">("");
  const [userFilter, setUserFilter] = useState<number | "">("");

  const [createOpen, setCreateOpen] = useState(false);
  const [eventType, setEventType] = useState<CompensationType>("CPJ_SUPPORT");
  const [motivo, setMotivo] = useState("");
  const [picked, setPicked] = useState<Record<number, boolean>>({});
  const [busy, setBusy] = useState(false);

  const [detail, setDetail] = useState<CompensationEventPublic | null>(null);
  const [logs, setLogs] = useState<CompensationEventLogPublic[]>([]);
  const [actionMotivo, setActionMotivo] = useState("");

  const efetivoMap = useMemo(() => new Map(efetivo.map((u) => [u.id, u])), [efetivo]);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [list, sum, staff] = await Promise.all([
        compensationsApi.listCompensations(token, {
          status: statusFilter || undefined,
          event_type: typeFilter || undefined,
          user_id: userFilter === "" ? undefined : userFilter,
          year,
        }),
        compensationsApi.getCompensationSummary(token, year),
        usersApi.listEfetivo(token),
      ]);
      setEvents(list);
      setSummary(sum);
      setEfetivo(staff.filter((u) => u.status === "APPROVED"));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar compensações");
    } finally {
      setLoading(false);
    }
  }, [token, statusFilter, typeFilter, userFilter, year]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (user && !isApprover) setUserFilter(user.id);
  }, [user, isApprover]);

  useEffect(() => {
    if (!token || !detail) {
      setLogs([]);
      return;
    }
    let cancelled = false;
    void compensationsApi.listCompensationLogs(token, detail.id).then((rows) => {
      if (!cancelled) setLogs(rows);
    });
    return () => {
      cancelled = true;
    };
  }, [token, detail]);

  const selectedIds = useMemo(
    () => Object.entries(picked).filter(([, v]) => v).map(([k]) => Number(k)),
    [picked],
  );

  async function submitCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setBusy(true);
    setMsg(null);
    setError(null);
    try {
      await compensationsApi.createCompensationEvent(token, {
        event_type: eventType,
        motivo,
        participant_user_ids: selectedIds,
      });
      setMsg("Evento registrado e encaminhado ao comando.");
      setCreateOpen(false);
      setMotivo("");
      setPicked({});
      await load();
    } catch (ex) {
      setError(ex instanceof ApiError ? ex.detail : "Falha ao registrar");
    } finally {
      setBusy(false);
    }
  }

  async function runAction(kind: "cancel" | "revert") {
    if (!token || !detail || !actionMotivo.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const updated =
        kind === "cancel"
          ? await compensationsApi.cancelCompensationEvent(token, detail.id, actionMotivo.trim())
          : await compensationsApi.revertCompensationEvent(token, detail.id, actionMotivo.trim());
      setDetail(updated);
      setActionMotivo("");
      setMsg(kind === "cancel" ? "Evento cancelado." : "Evento revertido.");
      await load();
    } catch (ex) {
      setError(ex instanceof ApiError ? ex.detail : "Falha na operação");
    } finally {
      setBusy(false);
    }
  }

  function formatParticipants(ids: number[]) {
    return ids
      .map((id) => {
        const u = efetivoMap.get(id);
        return u ? `${u.patente} ${u.nome_guerra}` : `#${id}`;
      })
      .join(", ");
  }

  return (
    <OperationalLayout>
      <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold text-zinc-50 sm:text-3xl">Compensações</h1>
            {user && <OrgUnitBadge variant={orgBadgeVariantForViewer(user)} />}
          </div>
          <p className="mt-2 max-w-xl text-sm text-zinc-400">
            Cadastro de méritos que geram crédito de compensação. Folgas mensais e DS são solicitadas na aba Folgas.
          </p>
        </div>
        {canRegisterCompensation && (
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="rounded-lg border border-zinc-600 bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white"
          >
            Novo evento
          </button>
        )}
      </header>

      {error && (
        <div className="mb-4 rounded-md border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {msg && (
        <div className="mb-4 rounded-md border border-emerald-900/50 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-200">
          {msg}
        </div>
      )}

      {summary && (
        <div className="mb-8 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">Pendentes (comando)</p>
            <p className="mt-1 text-2xl font-semibold text-amber-200">{summary.pending_count}</p>
          </div>
          <div className="rounded-xl border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">Aprovados no ano</p>
            <p className="mt-1 text-2xl font-semibold text-emerald-200">{summary.approved_recent_count}</p>
          </div>
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-3">
        <select
          className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as CompensationEventStatus | "")}
        >
          <option value="">Todos os status</option>
          {(["PENDING", "APPROVED", "REJECTED", "CANCELLED", "REVERTED"] as CompensationEventStatus[]).map((s) => (
            <option key={s} value={s}>
              {compensationStatusLabel(s)}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as CompensationType | "")}
        >
          <option value="">Todos os tipos</option>
          {MERIT_COMPENSATION_TYPES.map((t) => (
            <option key={t} value={t}>
              {COMPENSATION_TYPE_LABELS[t]}
            </option>
          ))}
        </select>
        {isApprover && (
          <select
            className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
            value={userFilter === "" ? "" : String(userFilter)}
            onChange={(e) => setUserFilter(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Todos os policiais</option>
            {efetivo.map((u) => (
              <option key={u.id} value={u.id}>
                {u.patente} {u.nome_guerra}
              </option>
            ))}
          </select>
        )}
        {isApprover && (
          <button
            type="button"
            onClick={() => setUserFilter("")}
            className="rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-300 hover:bg-zinc-900"
          >
            Todas
          </button>
        )}
        {isApprover && (
          <button
            type="button"
            onClick={() => user && setUserFilter(user.id)}
            className="rounded-lg border border-zinc-700 px-3 py-2 text-xs text-zinc-300 hover:bg-zinc-900"
          >
            Minhas
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : events.length === 0 ? (
        <p className="text-sm text-zinc-500">Nenhuma compensação encontrada.</p>
      ) : (
        <ul className="space-y-3">
          {events.map((ev) => (
            <li
              key={ev.id}
              className="cursor-pointer rounded-xl border border-zinc-800/80 bg-zinc-950/40 p-4 transition hover:border-zinc-600"
              onClick={() => {
                setDetail(ev);
                setActionMotivo("");
              }}
            >
              <div>
                <p className="font-medium text-zinc-100">{COMPENSATION_TYPE_LABELS[ev.event_type]}</p>
                <span
                  className={`mt-1 inline-block rounded border px-2 py-0.5 text-[10px] uppercase ${compensationStatusBadgeClass(ev.status)}`}
                >
                  {compensationStatusLabel(ev.status)}
                </span>
              </div>
              <p className="mt-2 line-clamp-2 text-xs text-zinc-400">{ev.motivo}</p>
              <p className="mt-2 text-[10px] text-zinc-500">
                {formatParticipants(ev.participant_user_ids)} · {new Date(ev.created_at).toLocaleString("pt-BR")}
              </p>
            </li>
          ))}
        </ul>
      )}

      {createOpen && canRegisterCompensation && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 backdrop-blur-sm sm:items-center">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-50">Nova compensação (mérito)</h2>
              <button type="button" className="text-zinc-500 hover:text-zinc-200" onClick={() => setCreateOpen(false)}>
                ✕
              </button>
            </div>
            <form className="mt-4 space-y-4" onSubmit={(e) => void submitCreate(e)}>
              <div>
                <label className="text-xs text-zinc-500">Tipo</label>
                <select
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value as CompensationType)}
                >
                  {MERIT_COMPENSATION_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {COMPENSATION_TYPE_LABELS[t]}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-zinc-500">Motivo / relato</label>
                <textarea
                  required
                  minLength={3}
                  rows={4}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                />
              </div>
              <div>
                <p className="text-xs text-zinc-500">Envolvidos</p>
                <div>
                  {efetivo.map((u) => (
                    <label key={u.id} className="flex cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={!!picked[u.id]}
                        onChange={(e) => setPicked((p) => ({ ...p, [u.id]: e.target.checked }))}
                      />
                      {u.patente} {u.nome_guerra}
                    </label>
                  ))}
                </div>
              </div>
              <button
                type="submit"
                disabled={busy || selectedIds.length === 0}
                className="w-full rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-semibold text-zinc-900 disabled:opacity-50"
              >
                {busy ? "Enviando…" : "Registrar"}
              </button>
            </form>
          </div>
        </div>
      )}

      {detail && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <aside className="flex h-full w-full max-w-lg flex-col border-l border-zinc-800 bg-zinc-950">
            <div className="border-b border-zinc-800 p-4">
              <button type="button" className="float-right text-zinc-500" onClick={() => setDetail(null)}>
                ✕
              </button>
              <p className="font-medium text-zinc-50">{COMPENSATION_TYPE_LABELS[detail.event_type]}</p>
              <span
                className={`mt-2 inline-block rounded border px-2 py-0.5 text-[10px] uppercase ${compensationStatusBadgeClass(detail.status)}`}
              >
                {compensationStatusLabel(detail.status)}
              </span>
              <p className="mt-3 whitespace-pre-wrap text-sm text-zinc-300">{detail.motivo}</p>
              <p className="mt-2 text-xs text-zinc-500">{formatParticipants(detail.participant_user_ids)}</p>
              {detail.created_by_label && (
                <p className="mt-1 text-xs text-zinc-500">Criado por: {detail.created_by_label}</p>
              )}
              {detail.decided_by_label && (
                <p className="text-xs text-zinc-500">
                  Decisão: {detail.decided_by_label}
                  {detail.decided_at ? ` · ${new Date(detail.decided_at).toLocaleString("pt-BR")}` : ""}
                </p>
              )}
            </div>
            {(canRegisterCompensation || isApprover) &&
              (detail.status === "PENDING" || detail.status === "APPROVED") && (
                <div className="space-y-2 border-b border-zinc-800 p-4">
                  <textarea
                    placeholder="Motivo da ação"
                    className="w-full rounded border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                    value={actionMotivo}
                    onChange={(e) => setActionMotivo(e.target.value)}
                  />
                  {canRegisterCompensation && detail.status === "PENDING" && (
                    <button
                      type="button"
                      disabled={busy || !actionMotivo.trim()}
                      onClick={() => void runAction("cancel")}
                      className="w-full rounded border border-zinc-600 py-2 text-xs text-zinc-200 disabled:opacity-50"
                    >
                      Cancelar pendência
                    </button>
                  )}
                  {detail.status === "APPROVED" && (
                    <>
                      {isApprover && (
                        <button
                          type="button"
                          disabled={busy || !actionMotivo.trim()}
                          onClick={() => void runAction("revert")}
                          className="w-full rounded border border-violet-800/80 py-2 text-xs text-violet-200 disabled:opacity-50"
                        >
                          Reverter aprovação
                        </button>
                      )}
                      {canRegisterCompensation && (
                        <button
                          type="button"
                          disabled={busy || !actionMotivo.trim()}
                          onClick={() => void runAction("cancel")}
                          className="w-full rounded border border-zinc-600 py-2 text-xs text-zinc-200 disabled:opacity-50"
                        >
                          Cancelar
                        </button>
                      )}
                    </>
                  )}
                </div>
              )}
            <div className="flex-1 overflow-y-auto p-4">
              <p className="text-xs uppercase tracking-wider text-zinc-500">Histórico</p>
              <ul className="mt-3 space-y-3">
                {logs.map((log) => (
                  <li key={log.id} className="rounded border border-zinc-800/60 bg-black/30 p-3 text-xs">
                    <p className="text-zinc-400">{new Date(log.created_at).toLocaleString("pt-BR")}</p>
                    <p className="mt-1 font-medium text-zinc-200">
                      {log.action} — {log.actor_label}
                    </p>
                    {log.motivo && <p className="mt-1 text-zinc-400">{log.motivo}</p>}
                    {log.details && <p className="mt-1 text-zinc-500">{log.details}</p>}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      )}
    </OperationalLayout>
  );
}
