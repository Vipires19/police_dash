import { useCallback, useEffect, useMemo, useState } from "react";
import { LeaveRequestModal } from "@/components/folgas/LeaveRequestModal";
import { MonthlyCalendar } from "@/components/folgas/MonthlyCalendar";
import { leaveStatusBadgeClass, leaveStatusLabel } from "@/components/folgas/statusStyles";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as leavesApi from "@/services/leavesApi";
import * as compensationsApi from "@/services/compensationsApi";
import type {
  CalendarDay,
  CalendarLeaveEntry,
  LeaveCalendarResponse,
  UserCompensationAvailable,
} from "@/types/leaves";

function sortEntries(entries: CalendarLeaveEntry[]): CalendarLeaveEntry[] {
  return [...entries].sort((a, b) => {
    if (a.operational_rank !== b.operational_rank) return a.operational_rank - b.operational_rank;
    if (a.display_order !== b.display_order) return a.display_order - b.display_order;
    return a.nome_guerra.localeCompare(b.nome_guerra);
  });
}

export function FolgasPage() {
  const { token, user, isApprover } = useAuth();
  const now = useMemo(() => new Date(), []);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [cal, setCal] = useState<LeaveCalendarResponse | null>(null);
  const [credits, setCredits] = useState<UserCompensationAvailable[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const [c, av] = await Promise.all([
        leavesApi.getLeaveCalendar(token, year, month),
        compensationsApi.listAvailableCompensations(token),
      ]);
      setCal(c);
      setCredits(av);
    } catch (e) {
      setCal(null);
      setErr(e instanceof ApiError ? e.detail : "Falha ao carregar folgas");
    }
  }, [token, year, month]);

  useEffect(() => {
    void load();
  }, [load]);

  const monthBookable = useMemo(() => {
    if (!cal?.booking_policy) return true;
    return cal.booking_policy.allowed_year_months.some((ym) => ym.year === year && ym.month === month);
  }, [cal, year, month]);

  const bookingHint = cal?.booking_policy?.operational_hint ?? "";

  useEffect(() => {
    setSelected((prev) => {
      if (!prev) return null;
      const parts = prev.split("-").map(Number);
      const [y, m] = parts;
      if (y === year && m === month) return prev;
      return null;
    });
  }, [year, month]);

  useEffect(() => {
    if (!monthBookable) setSelected(null);
  }, [monthBookable]);

  const selectedDay: CalendarDay | undefined = useMemo(() => {
    if (!cal || !selected) return undefined;
    return cal.days.find((d) => d.date === selected);
  }, [cal, selected]);

  const openRequest = (iso: string) => {
    setSelected(iso);
    setModalOpen(true);
  };

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
  };

  return (
    <OperationalLayout>
      <header className="mb-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Folgas</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Calendário mensal, solicitação de folga mensal ou por compensação aprovada. Indicadores discretos: azul
          pendente, amarelo revisão automática, verde aprovado, vermelho indeferido. A janela do mês seguinte obedece
          à regra do dia 25 (também validada na API).
        </p>
      </header>

      {err && <p className="mb-4 text-sm text-red-400">{err}</p>}

      {cal && (
        <div className="mb-6 grid gap-4 rounded-xl border border-zinc-800/80 bg-zinc-950/50 p-4 sm:grid-cols-3">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">Minhas pendentes</p>
            <p className="mt-1 text-2xl font-semibold text-zinc-100">{cal.summary.my_pending_count}</p>
          </div>
          {isApprover && cal.summary.command_pending_leaves != null && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-zinc-500">Fila comando (folgas)</p>
              <p className="mt-1 text-2xl font-semibold text-zinc-100">{cal.summary.command_pending_leaves}</p>
            </div>
          )}
          {isApprover && cal.summary.command_pending_compensations != null && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-zinc-500">Eventos compensação</p>
              <p className="mt-1 text-2xl font-semibold text-zinc-100">{cal.summary.command_pending_compensations}</p>
            </div>
          )}
        </div>
      )}

      {cal && !monthBookable && (
        <p className="mb-4 text-xs text-amber-200/90">{bookingHint}</p>
      )}

      <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
        {cal && (
          <MonthlyCalendar
            year={year}
            month={month}
            days={cal.days}
            selected={selected}
            onSelect={(iso) => {
              setSelected(iso);
            }}
            onPrev={() => shiftMonth(-1)}
            onNext={() => shiftMonth(1)}
            bookableMonth={monthBookable}
            bookingBlockedTitle={cal.booking_policy.operational_hint}
          />
        )}
        <div className="space-y-4">
          <button
            type="button"
            disabled={!selected || !monthBookable}
            onClick={() => selected && monthBookable && openRequest(selected)}
            className="w-full rounded-lg border border-zinc-600 bg-zinc-900/80 py-3 text-sm font-medium text-zinc-100 hover:border-zinc-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Solicitar folga no dia selecionado
          </button>
          <div className="rounded-xl border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Detalhe do dia</p>
            {!selected && <p className="mt-3 text-sm text-zinc-500">Selecione uma data no calendário.</p>}
            {selected && selectedDay && (
              <ul className="mt-3 max-h-72 space-y-2 overflow-y-auto">
                {sortEntries(selectedDay.entries).map((e) => (
                  <li
                    key={e.id}
                    className={[
                      "rounded-lg border px-3 py-2 text-xs",
                      leaveStatusBadgeClass(e.status),
                      e.user_id === user?.id ? "ring-1 ring-zinc-400/40" : "",
                    ].join(" ")}
                  >
                    <p className="font-medium">
                      {e.patente} {e.nome_guerra}
                    </p>
                    <p className="mt-1 text-[10px] uppercase tracking-wide text-zinc-400">
                      {e.leave_type === "MONTHLY" ? "Mensal" : "Compensação"} · {leaveStatusLabel(e.status)}
                    </p>
                  </li>
                ))}
                {selectedDay.entries.length === 0 && (
                  <p className="text-sm text-zinc-500">Nenhuma solicitação ativa neste dia.</p>
                )}
              </ul>
            )}
          </div>
        </div>
      </div>

      <LeaveRequestModal
        open={modalOpen}
        dateIso={selected}
        availableCredits={credits}
        onClose={() => setModalOpen(false)}
        onSubmit={async (payload) => {
          if (!token) return;
          await leavesApi.requestLeave(token, payload);
          await load();
        }}
      />
    </OperationalLayout>
  );
}
