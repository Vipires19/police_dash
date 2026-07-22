import { useCallback, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { DejemGenerateWizard } from "@/components/dejem/DejemGenerateWizard";
import { DejemShiftDayDrawer } from "@/components/dejem/DejemShiftDayDrawer";
import { DejemShiftMonthlyCalendar } from "@/components/dejem/DejemShiftMonthlyCalendar";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as dejemApi from "@/services/dejemApi";
import * as usersApi from "@/services/usersApi";
import * as vehiclesApi from "@/services/vehiclesApi";
import { isDejemShiftEditorRole, isDejemShiftViewerRole, type User } from "@/types";
import type { Vehicle } from "@/types/vehicle";
import type {
  DejemAssignmentRole,
  DejemMonthGeneratePayload,
  DejemMonthGeneratePreview,
  DejemMonthGenerateResult,
  DejemParticipantAdminRow,
  DejemShiftCalendarResponse,
  DejemShiftCreatePayload,
  DejemShiftDashboard,
  DejemShiftDayDetail,
  DejemShiftTemplatePublic,
  DejemShiftUpdatePayload,
  ParticipationType,
} from "@/types/dejem";

export function DejemShiftsPage() {
  const { token, user } = useAuth();
  const canView = user ? isDejemShiftViewerRole(user.role) : false;
  const canEdit = user ? isDejemShiftEditorRole(user.role) : false;

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [cal, setCal] = useState<DejemShiftCalendarResponse | null>(null);
  const [dashboard, setDashboard] = useState<DejemShiftDashboard | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<DejemShiftDayDetail | null>(null);
  const [templates, setTemplates] = useState<DejemShiftTemplatePublic[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [efetivo, setEfetivo] = useState<User[]>([]);
  const [participantsByShift, setParticipantsByShift] = useState<
    Record<number, DejemParticipantAdminRow[]>
  >({});
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setSelected(null);
    setDetail(null);
    setParticipantsByShift({});
  };

  const loadCalendar = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await dejemApi.getDejemShiftCalendar(token, year, month);
      setCal(data);
      if (data.month_id) {
        const dash = await dejemApi.getDejemShiftDashboard(token, data.month_id);
        setDashboard(dash);
      } else {
        setDashboard(null);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar calendário DEJEM");
    } finally {
      setLoading(false);
    }
  }, [token, year, month]);

  const loadTemplates = useCallback(async () => {
    if (!token) return;
    try {
      const rows = await dejemApi.listDejemShiftTemplates(token, false);
      setTemplates(rows);
    } catch {
      /* templates opcionais */
    }
  }, [token]);

  useEffect(() => {
    void loadCalendar();
    void loadTemplates();
  }, [loadCalendar, loadTemplates]);

  useEffect(() => {
    if (!token || !canEdit) return;
    void usersApi
      .listEfetivo(token)
      .then(setEfetivo)
      .catch(() => setEfetivo([]));
    void vehiclesApi
      .listVehicles(token)
      .then(setVehicles)
      .catch(() => setVehicles([]));
  }, [token, canEdit]);

  useEffect(() => {
    if (!token || !selected) {
      setDetail(null);
      return;
    }
    const [y, m, d] = selected.split("-").map(Number);
    let cancelled = false;
    void dejemApi
      .getDejemShiftDay(token, y, m, d)
      .then((res) => {
        if (!cancelled) setDetail(res);
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof ApiError ? e.detail : "Erro ao carregar o dia");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token, selected]);

  if (!canView) {
    return <Navigate to="/dejem/my" replace />;
  }

  const refreshDayAndCalendar = async () => {
    await loadCalendar();
    if (token && selected) {
      const [y, m, d] = selected.split("-").map(Number);
      const res = await dejemApi.getDejemShiftDay(token, y, m, d);
      setDetail(res);
    }
  };

  const onLoadParticipants = useCallback(
    async (shiftId: number) => {
      if (!token) return;
      try {
        const rows = await dejemApi.listDejemShiftParticipants(token, shiftId);
        setParticipantsByShift((prev) => ({ ...prev, [shiftId]: rows }));
      } catch (e) {
        setError(e instanceof ApiError ? e.detail : "Erro ao carregar participantes");
      }
    },
    [token],
  );

  const onCreate = async (payload: DejemShiftCreatePayload) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.createDejemShift(token, payload);
      setMsg("Escala criada.");
      await refreshDayAndCalendar();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao criar escala");
      throw e;
    } finally {
      setBusy(false);
    }
  };

  const onUpdate = async (shiftId: number, payload: DejemShiftUpdatePayload) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.updateDejemShift(token, shiftId, payload);
      setMsg("Escala atualizada.");
      await refreshDayAndCalendar();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao atualizar escala");
      throw e;
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async (shiftId: number) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.deleteDejemShift(token, shiftId);
      setMsg("Escala excluída.");
      await refreshDayAndCalendar();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao excluir escala");
    } finally {
      setBusy(false);
    }
  };

  const onAddParticipant = async (
    shiftId: number,
    userId: number,
    participationType: ParticipationType,
  ) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.addDejemShiftParticipant(token, shiftId, {
        user_id: userId,
        participation_type: participationType,
      });
      setMsg("Participante adicionado.");
      await onLoadParticipants(shiftId);
      await refreshDayAndCalendar();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao adicionar participante");
      throw e;
    } finally {
      setBusy(false);
    }
  };

  const onRemoveParticipant = async (shiftId: number, userId: number) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.removeDejemShiftParticipant(token, shiftId, userId);
      setMsg("Participante removido.");
      await onLoadParticipants(shiftId);
      await refreshDayAndCalendar();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao remover participante");
    } finally {
      setBusy(false);
    }
  };

  const onCloseShift = async (shiftId: number) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await dejemApi.closeDejemShift(token, shiftId);
      setMsg("Escala fechada.");
      await refreshDayAndCalendar();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao fechar escala");
    } finally {
      setBusy(false);
    }
  };

  const onSetRoles = async (
    shiftId: number,
    assignments: { user_id: number; role: DejemAssignmentRole }[],
  ) => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const rows = await dejemApi.setDejemShiftRoles(token, shiftId, { assignments });
      setParticipantsByShift((prev) => ({ ...prev, [shiftId]: rows }));
      setMsg("Funções da equipe atualizadas.");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao salvar funções");
      throw e;
    } finally {
      setBusy(false);
    }
  };

  const onPreview = async (
    payload: DejemMonthGeneratePayload,
  ): Promise<DejemMonthGeneratePreview> => {
    if (!token) throw new Error("Sessão inválida");
    setError(null);
    try {
      return await dejemApi.previewDejemMonthShifts(token, payload);
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : "Erro ao pré-visualizar";
      setError(detail);
      throw new Error(detail);
    }
  };

  const onGenerate = async (
    payload: DejemMonthGeneratePayload,
  ): Promise<DejemMonthGenerateResult> => {
    if (!token) throw new Error("Sessão inválida");
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const res = await dejemApi.generateDejemMonthShifts(token, payload);
      setMsg(
        `Geração concluída: ${res.created} criadas, ${res.ignored} ignoradas, ${res.replaced} substituídas.`,
      );
      setYear(res.year);
      setMonth(res.month);
      await loadCalendar();
      return res;
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : "Erro ao gerar escalas";
      setError(detail);
      throw new Error(detail);
    } finally {
      setBusy(false);
    }
  };

  return (
    <OperationalLayout>
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">DEJEM</p>
          <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Escalas DEJEM</h1>
          <p className="mt-2 max-w-xl text-sm text-zinc-400">
            Calendário administrativo, acompanhamento de vagas e gestão de participantes.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          {canEdit && (
            <>
              <button
                type="button"
                onClick={() => setWizardOpen(true)}
                className="rounded-lg bg-zinc-100 px-3 py-2 font-medium text-zinc-950 hover:bg-white"
              >
                Gerar Escalas do Mês
              </button>
              <Link
                to="/dejem/templates"
                className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-200 hover:border-zinc-500 hover:bg-zinc-900"
              >
                Templates
              </Link>
            </>
          )}
          <Link
            to="/dejem/admin"
            className="rounded-lg border border-zinc-700 px-3 py-2 text-zinc-200 hover:border-zinc-500 hover:bg-zinc-900"
          >
            Administração
          </Link>
        </div>
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

      {dashboard && (
        <section className="mb-6 space-y-3">
          <div className="grid gap-3 sm:grid-cols-3">
            {[
              ["Total de vagas", dashboard.campaign_total_slots ?? 0],
              ["Vagas abertas", dashboard.opened_slots ?? dashboard.total_capacity],
              [
                "Vagas restantes para abertura",
                dashboard.remaining_opening_slots ?? 0,
              ],
            ].map(([label, value]) => (
              <div
                key={String(label)}
                className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-4 py-3"
              >
                <p className="text-[11px] uppercase tracking-wider text-zinc-500">{label}</p>
                <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-50">{value}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {[
              ["Escalas Abertas", dashboard.open_shifts],
              ["Escalas Fechadas", dashboard.closed_shifts],
              ["Vagas Livres", dashboard.total_available],
              ["Vagas Ocupadas", dashboard.total_filled],
              ["Saldo Médio Restante", Number(dashboard.avg_remaining_slots ?? 0).toFixed(1)],
            ].map(([label, value]) => (
              <div
                key={String(label)}
                className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-4 py-3"
              >
                <p className="text-[11px] uppercase tracking-wider text-zinc-500">{label}</p>
                <p className="mt-1 text-xl font-semibold tabular-nums text-zinc-50">{value}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {loading && !cal ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : (
        cal && (
          <DejemShiftMonthlyCalendar
            year={year}
            month={month}
            days={cal.days}
            selected={selected}
            onSelect={setSelected}
            onPrev={() => shiftMonth(-1)}
            onNext={() => shiftMonth(1)}
          />
        )
      )}

      {!cal?.month_id && !loading && (
        <p className="mt-4 text-sm text-zinc-500">
          Nenhum mês DEJEM com distribuição para {String(month).padStart(2, "0")}/{year}. Crie o mês
          e distribua as vagas na área administrativa.
        </p>
      )}

      {selected && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            aria-label="Fechar painel"
            onClick={() => setSelected(null)}
          />
          <DejemShiftDayDrawer
            open
            isoDate={selected}
            detail={detail}
            canEdit={canEdit}
            busy={busy}
            templates={templates.filter((t) => t.is_active)}
            vehicles={vehicles}
            monthId={cal?.month_id ?? detail?.month_id ?? null}
            efetivo={efetivo}
            participantsByShift={participantsByShift}
            onClose={() => setSelected(null)}
            onCreate={onCreate}
            onUpdate={onUpdate}
            onDelete={onDelete}
            onLoadParticipants={onLoadParticipants}
            onAddParticipant={onAddParticipant}
            onRemoveParticipant={onRemoveParticipant}
            onCloseShift={onCloseShift}
            onSetRoles={onSetRoles}
            remainingOpeningSlots={dashboard?.remaining_opening_slots ?? null}
          />
        </>
      )}

      <DejemGenerateWizard
        open={wizardOpen}
        initialYear={year}
        initialMonth={month}
        templates={templates}
        busy={busy}
        onClose={() => setWizardOpen(false)}
        onPreview={onPreview}
        onGenerate={onGenerate}
        onGoToCalendar={(y, m) => {
          setYear(y);
          setMonth(m);
          setSelected(null);
        }}
      />
    </OperationalLayout>
  );
}
