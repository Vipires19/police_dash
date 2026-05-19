import { useCallback, useEffect, useMemo, useState } from "react";
import { Share2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ScaleExportModal } from "@/components/service-scales/ScaleExportModal";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import type { VehicleLogFeedItem } from "@/types/vehicle";
import type { LeaveCalendarResponse } from "@/types/leaves";
import type { VacationCalendarResponse } from "@/types/vacation";
import type { ScaleLogFeedItem } from "@/types/serviceScale";
import { ApiError } from "@/services/api";
import * as vehiclesApi from "@/services/vehiclesApi";
import * as leavesApi from "@/services/leavesApi";
import * as vacationsApi from "@/services/vacationsApi";
import * as scalesApi from "@/services/serviceScalesApi";
import * as compensationsApi from "@/services/compensationsApi";
import type { CompensationDashboardSummary } from "@/types/compensations";
import { COMPENSATION_TYPE_LABELS } from "@/types/compensations";

const FEED_LIMIT = 3;

function feedGlyph(log: VehicleLogFeedItem): string {
  if (log.action_type === "CREATED" || log.action_type === "RETURNED") return "🟢";
  if (log.new_status === "BAIXADA") return "🔴";
  if (log.new_status === "MANUTENCAO") return "🟡";
  if (log.new_status === "RESERVA") return "⚪";
  return "🔵";
}

function todayIsoLocal(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, token, isApprover } = useAuth();
  const [scaleEvents, setScaleEvents] = useState<ScaleLogFeedItem[]>([]);
  const [scaleErr, setScaleErr] = useState<string | null>(null);
  const [feed, setFeed] = useState<VehicleLogFeedItem[]>([]);
  const [feedErr, setFeedErr] = useState<string | null>(null);
  const [leaveCal, setLeaveCal] = useState<LeaveCalendarResponse | null>(null);
  const [leaveErr, setLeaveErr] = useState<string | null>(null);
  const [vacationCal, setVacationCal] = useState<VacationCalendarResponse | null>(null);
  const [vacationErr, setVacationErr] = useState<string | null>(null);
  const [exportScaleId, setExportScaleId] = useState<number | null>(null);
  const [exportScaleTitle, setExportScaleTitle] = useState("");
  const [compSummary, setCompSummary] = useState<CompensationDashboardSummary | null>(null);
  const [compErr, setCompErr] = useState<string | null>(null);

  const todayIso = useMemo(() => todayIsoLocal(), []);

  const nowYm = useMemo(() => {
    const d = new Date();
    return { y: d.getFullYear(), m: d.getMonth() + 1 };
  }, []);

  const awayToday = useMemo(() => {
    const leaveDay = leaveCal?.days.find((d) => d.date === todayIso);
    const vacDay = vacationCal?.days.find((d) => d.date === todayIso);
    const folgas =
      leaveDay?.entries.filter((e) => e.status === "APPROVED").map((e) => ({
        id: e.id,
        patente: e.patente,
        nome_guerra: e.nome_guerra,
        leave_type: e.leave_type,
      })) ?? [];
    const approvedVac = vacDay?.entries.filter((e) => e.status === "APPROVED") ?? [];
    const ferias = approvedVac
      .filter((e) => e.vacation_type === "FERIAS")
      .map((e) => ({ id: e.id, patente: e.patente, nome_guerra: e.nome_guerra }));
    const lp = approvedVac
      .filter((e) => e.vacation_type === "LP")
      .map((e) => ({ id: e.id, patente: e.patente, nome_guerra: e.nome_guerra }));
    const outros = approvedVac
      .filter((e) => e.vacation_type !== "FERIAS" && e.vacation_type !== "LP")
      .map((e) => ({
        id: e.id,
        patente: e.patente,
        nome_guerra: e.nome_guerra,
        vacation_type: e.vacation_type,
      }));
    return {
      folgas,
      ferias,
      lp,
      outros,
      total: folgas.length + ferias.length + lp.length + outros.length,
    };
  }, [leaveCal, vacationCal, todayIso]);

  const loadScaleEvents = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await scalesApi.listRecentScaleEvents(token, FEED_LIMIT);
      setScaleEvents(rows);
      setScaleErr(null);
    } catch (e) {
      setScaleErr(e instanceof ApiError ? e.detail : "Escalas indisponíveis");
    }
  }, [token]);

  const loadFeed = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await vehiclesApi.listRecentVehicleLogs(token, FEED_LIMIT);
      setFeed(rows);
      setFeedErr(null);
    } catch (e) {
      setFeedErr(e instanceof ApiError ? e.detail : "Logs indisponíveis");
    }
  }, [token]);

  const loadLeaves = useCallback(async () => {
    if (!token) return;
    try {
      const c = await leavesApi.getLeaveCalendar(token, nowYm.y, nowYm.m);
      setLeaveCal(c);
      setLeaveErr(null);
    } catch (e) {
      setLeaveCal(null);
      setLeaveErr(e instanceof ApiError ? e.detail : "Resumo de folgas indisponível");
    }
  }, [token, nowYm.y, nowYm.m]);

  const loadVacations = useCallback(async () => {
    if (!token || !isApprover) return;
    try {
      const c = await vacationsApi.getVacationCalendar(token, nowYm.y, nowYm.m);
      setVacationCal(c);
      setVacationErr(null);
    } catch (e) {
      setVacationCal(null);
      setVacationErr(e instanceof ApiError ? e.detail : "Resumo de férias indisponível");
    }
  }, [token, isApprover, nowYm.y, nowYm.m]);

  useEffect(() => {
    void loadScaleEvents();
  }, [loadScaleEvents]);

  useEffect(() => {
    void loadFeed();
  }, [loadFeed]);

  useEffect(() => {
    void loadLeaves();
  }, [loadLeaves]);

  useEffect(() => {
    void loadVacations();
  }, [loadVacations]);

  const loadCompensations = useCallback(async () => {
    if (!token) return;
    try {
      const s = await compensationsApi.getCompensationSummary(token, nowYm.y);
      setCompSummary(s);
      setCompErr(null);
    } catch (e) {
      setCompSummary(null);
      setCompErr(e instanceof ApiError ? e.detail : "Resumo de compensações indisponível");
    }
  }, [token, nowYm.y]);

  useEffect(() => {
    void loadCompensations();
  }, [loadCompensations]);

  const todayLabel = useMemo(
    () => new Date(todayIso + "T12:00:00").toLocaleDateString("pt-BR", { weekday: "long", day: "2-digit", month: "long" }),
    [todayIso],
  );

  return (
    <OperationalLayout>
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-8 shadow-inner shadow-black/40">
        <p className="text-xs uppercase tracking-[0.4em] text-zinc-500">Painel inicial</p>
        <h2 className="mt-3 text-3xl font-semibold text-zinc-50">1° Pel Força Tática/ROCAM</h2>
        {user && (
          <p className="mt-6 text-xl text-zinc-200">
            Bem-vindo {user.patente} {user.nome_guerra}
          </p>
        )}
        <section className="mt-8 grid gap-4 border-t border-zinc-800/80 pt-6 text-sm text-zinc-400 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Folgas pendentes (suas)</p>
            {leaveErr && <p className="mt-2 text-xs text-red-400">{leaveErr}</p>}
            {!leaveErr && leaveCal && (
              <p className="mt-2 text-2xl font-semibold text-zinc-100">{leaveCal.summary.my_pending_count}</p>
            )}
          </div>
          <article className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
            <p className="text-xs uppercase tracking-wide text-zinc-500">Suas DS ({nowYm.y})</p>
            {compErr && <p className="mt-2 text-xs text-red-400">{compErr}</p>}
            {!compErr && compSummary?.ds_usage_samples[0] && (
              <p className="mt-2 text-lg font-semibold text-sky-200">{compSummary.ds_usage_samples[0].display}</p>
            )}
          </article>
          {isApprover && (
            <>
              <div className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-wide text-zinc-500">Fila folgas (comando)</p>
                {!leaveErr && leaveCal?.summary.command_pending_leaves != null && (
                  <p className="mt-2 text-2xl font-semibold text-zinc-100">
                    {leaveCal.summary.command_pending_leaves}
                  </p>
                )}
              </div>
              <article className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-wide text-zinc-500">Compensações pendentes</p>
                {!leaveErr && leaveCal?.summary.command_pending_compensations != null && (
                  <p className="mt-2 text-2xl font-semibold text-zinc-100">
                    {leaveCal.summary.command_pending_compensations}
                  </p>
                )}
              </article>
              <article className="rounded-lg border border-zinc-800/80 bg-black/30 p-4">
                <p className="text-xs uppercase tracking-wide text-zinc-500">Afastamentos pendentes</p>
                {vacationErr && <p className="mt-2 text-xs text-red-400">{vacationErr}</p>}
                {!vacationErr && vacationCal?.summary.command_pending_vacations != null && (
                  <p className="mt-2 text-2xl font-semibold text-zinc-100">
                    {vacationCal.summary.command_pending_vacations}
                  </p>
                )}
              </article>
            </>
          )}
        </section>

        {isApprover && (
          <article className="mt-4 rounded-lg border border-zinc-800/80 bg-black/30 p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Afastados hoje</p>
              <p className="text-[11px] capitalize text-zinc-600">{todayLabel}</p>
            </div>
            <p className="mt-1 text-2xl font-semibold text-zinc-100">{awayToday.total}</p>
            {(leaveErr || vacationErr) && (
              <p className="mt-2 text-xs text-red-400">{leaveErr ?? vacationErr}</p>
            )}
            {!leaveErr && !vacationErr && (
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-sky-400/90">Folgas</p>
                  {awayToday.folgas.length === 0 ? (
                    <p className="mt-2 text-xs text-zinc-600">Nenhum policial de folga hoje.</p>
                  ) : (
                    <ul className="mt-2 space-y-1">
                      {awayToday.folgas.map((p) => (
                        <li key={p.id} className="text-sm text-zinc-200">
                          {p.patente} {p.nome_guerra}
                          {p.leave_type === "COMPENSATION" && (
                            <span className="ml-1 text-[10px] text-zinc-500">(comp.)</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-violet-400/90">Férias</p>
                  {awayToday.ferias.length === 0 ? (
                    <p className="mt-2 text-xs text-zinc-600">Nenhum policial de férias hoje.</p>
                  ) : (
                    <ul className="mt-2 space-y-1">
                      {awayToday.ferias.map((p) => (
                        <li key={p.id} className="text-sm text-zinc-200">
                          {p.patente} {p.nome_guerra}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-amber-400/90">LP</p>
                  {awayToday.lp.length === 0 ? (
                    <p className="mt-2 text-xs text-zinc-600">Nenhum policial em LP hoje.</p>
                  ) : (
                    <ul className="mt-2 space-y-1">
                      {awayToday.lp.map((p) => (
                        <li key={p.id} className="text-sm text-zinc-200">
                          {p.patente} {p.nome_guerra}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-teal-400/90">Outros afastamentos</p>
                  {awayToday.outros.length === 0 ? (
                    <p className="mt-2 text-xs text-zinc-600">Nenhum outro afastamento hoje.</p>
                  ) : (
                    <ul className="mt-2 space-y-1">
                      {awayToday.outros.map((p) => (
                        <li key={p.id} className="text-sm text-zinc-200">
                          {p.patente} {p.nome_guerra}{" "}
                          <span className="text-zinc-500">({p.vacation_type.replace(/_/g, " ")})</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </article>
        )}

        {isApprover && vacationCal?.summary.critical_days && vacationCal.summary.critical_days.length > 0 && (
          <article className="mt-4 rounded-lg border border-violet-900/50 bg-violet-950/20 p-4 text-sm text-violet-100/90">
            <p className="text-xs font-semibold uppercase tracking-wider text-violet-400/90">
              Dias com simultaneidade crítica — férias/LP (2 policiais)
            </p>
            <p className="mt-2 font-mono text-xs text-violet-100/80">
              {vacationCal.summary.critical_days
                .map((d) => new Date(d + "T12:00:00").toLocaleDateString("pt-BR"))
                .join(" · ")}
            </p>
          </article>
        )}
        {isApprover && leaveCal?.summary.critical_days && leaveCal.summary.critical_days.length > 0 && (
          <div className="mt-4 rounded-lg border border-amber-900/50 bg-amber-950/20 p-4 text-sm text-amber-100/90">
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-400/90">
              Dias com efetivo crítico (≥4 policiais)
            </p>
            <p className="mt-2 font-mono text-xs text-amber-100/80">
              {leaveCal.summary.critical_days
                .map((d) => new Date(d + "T12:00:00").toLocaleDateString("pt-BR"))
                .join(" · ")}
            </p>
          </div>
        )}
      </section>

      {compSummary && compSummary.recent_events.length > 0 && (
        <section className="mt-8 rounded-xl border border-zinc-800 bg-zinc-950/60 p-6 shadow-inner shadow-black/30">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Compensações</p>
              <h3 className="mt-2 text-lg font-semibold text-zinc-100">Atividade recente</h3>
            </div>
            <button
              type="button"
              onClick={() => navigate("/compensacoes")}
              className="text-xs text-sky-400 hover:underline"
            >
              Ver todas
            </button>
          </div>
          <ul className="mt-4 space-y-3">
            {compSummary.recent_events.slice(0, 5).map((ev) => (
              <li key={ev.id} className="rounded-lg border border-zinc-800/60 bg-black/30 px-3 py-2 text-sm">
                <span className="font-medium text-zinc-200">{COMPENSATION_TYPE_LABELS[ev.event_type]}</span>
                <span className="ml-2 text-[10px] uppercase text-zinc-500">{ev.status}</span>
                <p className="mt-1 line-clamp-1 text-xs text-zinc-500">{ev.motivo}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-8 rounded-xl border border-zinc-800 bg-zinc-950/60 p-6 shadow-inner shadow-black/30">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Escalas de Serviço</p>
        <h3 className="mt-2 text-lg font-semibold text-zinc-100">Últimas alterações operacionais</h3>
        <p className="mt-1 text-xs text-zinc-600">Exibindo as {FEED_LIMIT} mais recentes</p>
        {scaleErr && <p className="mt-3 text-sm text-red-400">{scaleErr}</p>}
        {!scaleErr && scaleEvents.length === 0 && (
          <p className="mt-4 text-sm text-zinc-500">Nenhum evento de escala registrado.</p>
        )}
        <ul className="mt-4 divide-y divide-zinc-800/80">
          {scaleEvents.map((ev) => (
            <li key={ev.id} className="flex items-start gap-2 py-3 first:pt-0">
              <button
                type="button"
                onClick={() => navigate(`/escala-servico`)}
                className="min-w-0 flex-1 text-left hover:opacity-90"
              >
                <p className="text-sm text-zinc-200">
                  {new Date(ev.scale_date + "T12:00:00").toLocaleDateString("pt-BR")} — {ev.scale_title}
                </p>
                <p className="mt-1 text-xs text-zinc-400">{ev.description}</p>
                <p className="mt-1 text-[11px] text-zinc-500">
                  {new Date(ev.created_at).toLocaleString("pt-BR")} · {ev.actor_label}
                </p>
              </button>
              <button
                type="button"
                title="Exportar escala"
                onClick={() => {
                  setExportScaleId(ev.service_scale_id);
                  setExportScaleTitle(ev.scale_title);
                }}
                className="shrink-0 rounded border border-zinc-700 p-1.5 text-zinc-400 hover:border-sky-800 hover:text-sky-300"
              >
                <Share2 className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="mt-8 rounded-xl border border-zinc-800 bg-zinc-950/60 p-6 shadow-inner shadow-black/30">
        <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Viaturas</p>
        <h3 className="mt-2 text-lg font-semibold text-zinc-100">Últimos registros operacionais</h3>
        <p className="mt-1 text-xs text-zinc-600">Exibindo os {FEED_LIMIT} mais recentes</p>
        {feedErr && <p className="mt-3 text-sm text-red-400">{feedErr}</p>}
        {!feedErr && feed.length === 0 && (
          <p className="mt-4 text-sm text-zinc-500">Nenhum log registrado ainda.</p>
        )}
        <ul className="mt-4 divide-y divide-zinc-800/80">
          {feed.map((log) => (
            <li key={log.id} className="flex gap-3 py-3 first:pt-0">
              <span className="shrink-0 pt-0.5 text-base leading-none">{feedGlyph(log)}</span>
              <div className="min-w-0">
                <p className="text-sm text-zinc-200">
                  <span className="font-mono text-zinc-400">{log.vehicle_prefixo}</span> — {log.description}
                </p>
                <p className="mt-1 text-[11px] text-zinc-500">
                  {new Date(log.created_at).toLocaleString("pt-BR")} · {log.actor_label}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <ScaleExportModal
        open={exportScaleId !== null}
        scaleId={exportScaleId}
        scaleTitle={exportScaleTitle}
        onClose={() => {
          setExportScaleId(null);
          setExportScaleTitle("");
        }}
      />
    </OperationalLayout>
  );
}
