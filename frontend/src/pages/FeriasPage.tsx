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
import * as vacationsApi from "@/services/vacationsApi";
import type { CalendarVacationEntry, VacationCalendarDay, VacationCalendarResponse } from "@/types/vacation";

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

export function FeriasPage() {
  const { token, user, isApprover } = useAuth();
  const now = useMemo(() => new Date(), []);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [cal, setCal] = useState<VacationCalendarResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const c = await vacationsApi.getVacationCalendar(token, year, month);
      setCal(c);
    } catch (e) {
      setCal(null);
      setErr(e instanceof ApiError ? e.detail : "Falha ao carregar férias");
    }
  }, [token, year, month]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedDay: VacationCalendarDay | undefined = useMemo(() => {
    if (!cal || !selected) return undefined;
    return cal.days.find((d) => d.date === selected);
  }, [cal, selected]);

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setSelected(null);
  };

  return (
    <OperationalLayout>
      <header className="mb-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Férias</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Calendário de afastamentos (férias e LP). Períodos de 15 ou 30 dias. Máximo de 2 policiais simultâneos por
          dia — acima disso a solicitação entra em revisão automática.
        </p>
      </header>

      {err && <p className="mb-4 text-sm text-red-400">{err}</p>}

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
          {isApprover && cal.summary.critical_days && cal.summary.critical_days.length > 0 && (
            <article className="sm:col-span-2 lg:col-span-1">
              <p className="text-[10px] uppercase tracking-wider text-amber-400/90">Dias no limite (2 pol.)</p>
              <p className="mt-1 text-xs text-amber-100/80">{cal.summary.critical_days.length} no mês</p>
            </article>
          )}
        </section>
      )}

      <section className="grid gap-8 lg:grid-cols-[1fr_340px]">
        {cal && (
          <VacationMonthlyCalendar
            year={year}
            month={month}
            days={cal.days}
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
            Solicitar férias / LP
          </button>
          <section className="rounded-xl border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Detalhe do dia</p>
            {!selected && <p className="mt-3 text-sm text-zinc-500">Selecione uma data no calendário.</p>}
            {selected && selectedDay && (
              <ul className="mt-3 max-h-80 space-y-2 overflow-y-auto">
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
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-zinc-400">{formatPeriod(e.start_date, e.end_date)}</p>
                    <p className="mt-1 flex flex-wrap gap-1 text-[10px] uppercase tracking-wide">
                      <span className={["rounded border px-1.5 py-0.5", vacationTypeBadgeClass(e.vacation_type)].join(" ")}>
                        {vacationTypeLabel(e.vacation_type)}
                      </span>
                      <span>{vacationStatusLabel(e.status)}</span>
                      <span className="text-zinc-500">{e.total_days}d</span>
                    </p>
                  </li>
                ))}
                {selectedDay.entries.length === 0 && (
                  <p className="text-sm text-zinc-500">Nenhum afastamento ativo neste dia.</p>
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
          await vacationsApi.requestVacation(token, payload);
          await load();
        }}
      />
    </OperationalLayout>
  );
}
