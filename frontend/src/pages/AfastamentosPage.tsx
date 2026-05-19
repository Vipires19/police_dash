import { useCallback, useEffect, useMemo, useState } from "react";
import { VacationMonthlyCalendar } from "@/components/vacations/VacationMonthlyCalendar";
import { VacationRequestModal } from "@/components/vacations/VacationRequestModal";
import {
  vacationStatusBadgeClass,
  vacationStatusLabel,
  vacationTypeBadgeClass,
  vacationTypeLabel,
} from "@/components/vacations/statusStyles";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as absencesApi from "@/services/absencesApi";
import type {
  CalendarVacationEntry,
  VacationCalendarDay,
  VacationCalendarResponse,
  VacationStatus,
  VacationType,
} from "@/types/vacation";
import { ABSENCE_TYPES as TYPES } from "@/types/vacation";

const CANCELLABLE: VacationStatus[] = ["PENDING", "REVIEW", "APPROVED"];
const STATUSES: VacationStatus[] = ["PENDING", "REVIEW", "APPROVED", "REJECTED", "CANCELLED", "REVERTED"];

function sortEntries(entries: CalendarVacationEntry[]): CalendarVacationEntry[] {
  return [...entries].sort((a, b) => {
    if (a.operational_rank !== b.operational_rank) return a.operational_rank - b.operational_rank;
    if (a.display_order !== b.display_order) return a.display_order - b.display_order;
    return a.nome_guerra.localeCompare(b.nome_guerra);
  });
}

function formatPeriod(start: string, end: string): string {
  const s = new Date(start + "T12:00:00").toLocaleDateString("pt-BR");
  const e = new Date(end + "T12:00:00").toLocaleDateString("pt-BR");
  return `${s} → ${e}`;
}

export function AfastamentosPage() {
  const { token, user, isApprover } = useAuth();
  const now = useMemo(() => new Date(), []);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [cal, setCal] = useState<VacationCalendarResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [typeFilter, setTypeFilter] = useState<VacationType | "">("");
  const [statusFilter, setStatusFilter] = useState<VacationStatus | "">("");
  const [cancelTargetId, setCancelTargetId] = useState<number | null>(null);
  const [cancelMotivo, setCancelMotivo] = useState("");
  const [cancelBusy, setCancelBusy] = useState(false);
  const [editTarget, setEditTarget] = useState<CalendarVacationEntry | null>(null);
  const [editStart, setEditStart] = useState("");
  const [editEnd, setEditEnd] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editBusy, setEditBusy] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const c = await absencesApi.getAbsenceCalendar(token, year, month);
      setCal(c);
    } catch (e) {
      setCal(null);
      setErr(e instanceof ApiError ? e.detail : "Falha ao carregar afastamentos");
    }
  }, [token, year, month]);

  useEffect(() => {
    void load();
  }, [load]);

  const filteredDays = useMemo(() => {
    if (!cal) return [];
    return cal.days.map((d) => ({
      ...d,
      entries: d.entries.filter((e) => {
        if (typeFilter && e.vacation_type !== typeFilter) return false;
        if (statusFilter && e.status !== statusFilter) return false;
        return true;
      }),
    }));
  }, [cal, typeFilter, statusFilter]);

  const selectedDay: VacationCalendarDay | undefined = useMemo(() => {
    if (!selected) return undefined;
    return filteredDays.find((d) => d.date === selected);
  }, [filteredDays, selected]);

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setSelected(null);
    setCancelTargetId(null);
    setEditTarget(null);
  };

  const canCancel = (e: CalendarVacationEntry) =>
    e.user_id === user?.id && CANCELLABLE.includes(e.status);

  const canEdit = (e: CalendarVacationEntry) =>
    e.user_id === user?.id && (e.status === "PENDING" || e.status === "REVIEW");

  async function confirmCancel(id: number, status: VacationStatus) {
    if (!token) return;
    if (status === "APPROVED" && cancelMotivo.trim().length < 3) {
      setErr("Informe o motivo do cancelamento (mín. 3 caracteres).");
      return;
    }
    setCancelBusy(true);
    setErr(null);
    try {
      await absencesApi.cancelAbsence(token, id, cancelMotivo.trim() || null);
      setMsg("Afastamento cancelado.");
      setCancelTargetId(null);
      setCancelMotivo("");
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Não foi possível cancelar");
    } finally {
      setCancelBusy(false);
    }
  }

  async function saveEdit() {
    if (!token || !editTarget) return;
    setEditBusy(true);
    setErr(null);
    try {
      await absencesApi.updateAbsence(token, editTarget.id, {
        start_date: editStart,
        end_date: editEnd,
        notes: editNotes.trim() || null,
      });
      setMsg("Afastamento atualizado.");
      setEditTarget(null);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Não foi possível editar");
    } finally {
      setEditBusy(false);
    }
  }

  return (
    <OperationalLayout>
      <header className="mb-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Afastamentos</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Férias, LP, LTS, cursos e demais afastamentos em um calendário único. Férias/LP: 15 ou 30 dias e limite de 2
          policiais/dia. Demais tipos: período livre, sem simultaneidade.
        </p>
      </header>

      {err && <p className="mb-4 text-sm text-red-400">{err}</p>}
      {msg && (
        <p className="mb-4 rounded-md border border-emerald-900/50 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-200">
          {msg}
        </p>
      )}

      {cal && (
        <section className="mb-6 grid gap-4 rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4 sm:grid-cols-2 lg:grid-cols-4">
          <article>
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">Minhas pendentes</p>
            <p className="mt-1 text-2xl font-semibold text-zinc-100">{cal.summary.my_pending_count}</p>
          </article>
          {isApprover && cal.summary.command_pending_vacations != null && (
            <article>
              <p className="text-[10px] uppercase tracking-wider text-zinc-500">Fila comando</p>
              <p className="mt-1 text-2xl font-semibold text-zinc-100">{cal.summary.command_pending_vacations}</p>
            </article>
          )}
          {isApprover && cal.summary.currently_away_count != null && (
            <article>
              <p className="text-[10px] uppercase tracking-wider text-zinc-500">Afastados hoje</p>
              <p className="mt-1 text-2xl font-semibold text-zinc-100">{cal.summary.currently_away_count}</p>
            </article>
          )}
        </section>
      )}

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value as VacationType | "")}
        >
          <option value="">Todos os tipos</option>
          {TYPES.map((t) => (
            <option key={t} value={t}>
              {vacationTypeLabel(t)}
            </option>
          ))}
        </select>
        <select
          className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as VacationStatus | "")}
        >
          <option value="">Todos os status</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {vacationStatusLabel(s)}
            </option>
          ))}
        </select>
      </div>

      <section className="mt-6 grid gap-8 lg:grid-cols-[1fr_340px]">
        {cal && (
          <VacationMonthlyCalendar
            year={year}
            month={month}
            days={filteredDays}
            selected={selected}
            onSelect={setSelected}
            onPrev={() => shiftMonth(-1)}
            onNext={() => shiftMonth(1)}
          />
        )}
        <aside className="space-y-4">
          <button
            type="button"
            onClick={() => setModalOpen(true)}
            className="w-full rounded-lg border border-zinc-600 bg-zinc-900/80 py-3 text-sm font-medium text-zinc-100 hover:border-zinc-400"
          >
            Solicitar afastamento
          </button>
          <section className="rounded-xl border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Detalhe do dia</p>
            {!selected && <p className="mt-3 text-sm text-zinc-500">Selecione uma data no calendário.</p>}
            {selected && selectedDay && (
              <ul className="mt-3 max-h-96 space-y-2 overflow-y-auto">
                {sortEntries(selectedDay.entries).map((e) => (
                  <li
                    key={e.id}
                    className={[
                      "rounded-lg border px-3 py-2 text-xs",
                      vacationStatusBadgeClass(e.status),
                      e.user_id === user?.id ? "ring-1 ring-zinc-400/40" : "",
                    ].join(" ")}
                  >
                    <p className="font-medium">
                      {e.patente} {e.nome_guerra}
                      {e.user_id === user?.id && <span className="ml-1 text-zinc-500">(você)</span>}
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-zinc-400">{formatPeriod(e.start_date, e.end_date)}</p>
                    <p className="mt-1 flex flex-wrap gap-1 text-[10px] uppercase tracking-wide">
                      <span className={["rounded border px-1.5 py-0.5", vacationTypeBadgeClass(e.vacation_type)].join(" ")}>
                        {vacationTypeLabel(e.vacation_type)}
                      </span>
                      <span>{vacationStatusLabel(e.status)}</span>
                      <span className="text-zinc-500">{e.total_days}d</span>
                    </p>
                    {e.notes && <p className="mt-1 text-[10px] text-zinc-400">{e.notes}</p>}
                    {canEdit(e) && editTarget?.id !== e.id && (
                      <button
                        type="button"
                        className="mt-2 w-full rounded border border-zinc-600 py-1 text-[10px] uppercase text-zinc-300"
                        onClick={() => {
                          setEditTarget(e);
                          setEditStart(e.start_date);
                          setEditEnd(e.end_date);
                          setEditNotes(e.notes ?? "");
                          setCancelTargetId(null);
                        }}
                      >
                        Editar
                      </button>
                    )}
                    {editTarget?.id === e.id && (
                      <div className="mt-2 space-y-2">
                        <input
                          type="date"
                          value={editStart}
                          onChange={(ev) => setEditStart(ev.target.value)}
                          className="w-full rounded border border-zinc-700 bg-black/50 px-2 py-1 text-[11px]"
                        />
                        <input
                          type="date"
                          value={editEnd}
                          onChange={(ev) => setEditEnd(ev.target.value)}
                          className="w-full rounded border border-zinc-700 bg-black/50 px-2 py-1 text-[11px]"
                        />
                        <textarea
                          rows={2}
                          value={editNotes}
                          onChange={(ev) => setEditNotes(ev.target.value)}
                          className="w-full rounded border border-zinc-700 bg-black/50 px-2 py-1 text-[11px]"
                        />
                        <div className="flex gap-2">
                          <button
                            type="button"
                            disabled={editBusy}
                            onClick={() => void saveEdit()}
                            className="flex-1 rounded border border-emerald-800/80 py-1 text-[10px] text-emerald-200"
                          >
                            Salvar
                          </button>
                          <button
                            type="button"
                            onClick={() => setEditTarget(null)}
                            className="flex-1 rounded border border-zinc-600 py-1 text-[10px] text-zinc-400"
                          >
                            Voltar
                          </button>
                        </div>
                      </div>
                    )}
                    {canCancel(e) && cancelTargetId !== e.id && (
                      <button
                        type="button"
                        className="mt-2 w-full rounded border border-zinc-600 py-1 text-[10px] uppercase text-zinc-300"
                        onClick={() => {
                          setCancelTargetId(e.id);
                          setCancelMotivo("");
                          setEditTarget(null);
                        }}
                      >
                        Cancelar
                      </button>
                    )}
                    {cancelTargetId === e.id && (
                      <div className="mt-2 space-y-2">
                        <textarea
                          placeholder={e.status === "APPROVED" ? "Motivo obrigatório" : "Motivo opcional"}
                          rows={2}
                          value={cancelMotivo}
                          onChange={(ev) => setCancelMotivo(ev.target.value)}
                          className="w-full rounded border border-zinc-700 bg-black/50 px-2 py-1 text-[11px]"
                        />
                        <div className="flex gap-2">
                          <button
                            type="button"
                            disabled={cancelBusy}
                            onClick={() => void confirmCancel(e.id, e.status)}
                            className="flex-1 rounded border border-red-800/80 py-1 text-[10px] text-red-200"
                          >
                            Confirmar
                          </button>
                          <button
                            type="button"
                            onClick={() => setCancelTargetId(null)}
                            className="flex-1 rounded border border-zinc-600 py-1 text-[10px] text-zinc-400"
                          >
                            Voltar
                          </button>
                        </div>
                      </div>
                    )}
                  </li>
                ))}
                {selectedDay.entries.length === 0 && (
                  <p className="text-sm text-zinc-500">Nenhum afastamento neste dia com os filtros atuais.</p>
                )}
              </ul>
            )}
          </section>
        </aside>
      </section>

      <VacationRequestModal
        open={modalOpen}
        defaultStart={selected}
        onClose={() => setModalOpen(false)}
        onSubmit={async (payload) => {
          if (!token) return;
          await absencesApi.requestAbsence(token, payload);
          await load();
        }}
      />
    </OperationalLayout>
  );
}
