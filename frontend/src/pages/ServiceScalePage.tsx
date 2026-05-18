import { useCallback, useEffect, useMemo, useState } from "react";
import { ScaleDayDrawer } from "@/components/service-scales/ScaleDayDrawer";
import { ScaleMonthlyCalendar } from "@/components/service-scales/ScaleMonthlyCalendar";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as scalesApi from "@/services/serviceScalesApi";
import type { ScaleCalendarResponse, ScaleDayDetailResponse, ScaleHistoryResponse } from "@/types/serviceScale";
import { SCALE_EDITOR_ROLES } from "@/types";

export function ServiceScalePage() {
  const { token, user } = useAuth();
  const canEdit = user ? SCALE_EDITOR_ROLES.includes(user.role) : false;
  const now = useMemo(() => new Date(), []);
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [cal, setCal] = useState<ScaleCalendarResponse | null>(null);
  const [history, setHistory] = useState<ScaleHistoryResponse | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<ScaleDayDetailResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const loadCalendar = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const c = await scalesApi.getScaleCalendar(token, year, month);
      setCal(c);
    } catch (e) {
      setCal(null);
      setErr(e instanceof ApiError ? e.detail : "Falha ao carregar calendário");
    }
  }, [token, year, month]);

  const loadHistory = useCallback(async () => {
    if (!token) return;
    try {
      const h = await scalesApi.getScaleHistory(token, { limit: 30 });
      setHistory(h);
    } catch {
      setHistory(null);
    }
  }, [token]);

  const loadDay = useCallback(
    async (iso: string) => {
      if (!token) return;
      setErr(null);
      try {
        const d = await scalesApi.getScaleByDate(token, iso);
        setDetail(d);
      } catch (e) {
        setDetail(null);
        setErr(e instanceof ApiError ? e.detail : "Falha ao carregar dia");
      }
    },
    [token],
  );

  useEffect(() => {
    void loadCalendar();
  }, [loadCalendar]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    if (selected) void loadDay(selected);
    else setDetail(null);
  }, [selected, loadDay]);

  const refreshAll = async () => {
    await loadCalendar();
    await loadHistory();
    if (selected) await loadDay(selected);
  };

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setSelected(null);
  };

  const handleCreateScale = async (title: string) => {
    if (!token || !selected) return;
    setBusy(true);
    try {
      await scalesApi.createScale(token, { scale_date: selected, title, status: "DRAFT" });
      await refreshAll();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao criar escala");
    } finally {
      setBusy(false);
    }
  };

  const handlePublish = async (scaleId: number) => {
    if (!token) return;
    setBusy(true);
    try {
      await scalesApi.publishScale(token, scaleId);
      await refreshAll();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao publicar");
    } finally {
      setBusy(false);
    }
  };

  const handleAddTeam = async (scaleId: number, payload: unknown) => {
    if (!token) return;
    setBusy(true);
    try {
      await scalesApi.addScaleTeam(token, scaleId, payload as Parameters<typeof scalesApi.addScaleTeam>[2]);
      await refreshAll();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao salvar equipe");
    } finally {
      setBusy(false);
    }
  };

  const handleEditTeam = async (teamId: number, payload: Parameters<typeof scalesApi.updateScaleTeam>[2]) => {
    if (!token) return;
    setBusy(true);
    try {
      await scalesApi.updateScaleTeam(token, teamId, payload);
      await refreshAll();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao editar equipe");
    } finally {
      setBusy(false);
    }
  };

  const handleRemoveTeam = async (teamId: number) => {
    if (!token) return;
    setBusy(true);
    try {
      await scalesApi.removeScaleTeam(token, teamId);
      await refreshAll();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao remover equipe");
    } finally {
      setBusy(false);
    }
  };

  const handleDeleteScale = async (scaleId: number) => {
    if (!token) return;
    setBusy(true);
    try {
      await scalesApi.deleteScale(token, scaleId);
      setSelected(null);
      setDetail(null);
      await refreshAll();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Erro ao excluir escala");
    } finally {
      setBusy(false);
    }
  };

  return (
    <OperationalLayout>
      <header className="mb-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Escala de Serviço</h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-400">
          Calendário operacional do pelotão. Dias em verde: publicados; em âmbar: rascunho. Clique no dia para montar ou
          consultar equipes.
        </p>
      </header>

      {err && <p className="mb-4 text-sm text-red-400">{err}</p>}

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        {cal && (
          <ScaleMonthlyCalendar
            year={year}
            month={month}
            days={cal.days}
            selected={selected}
            onSelect={setSelected}
            onPrev={() => shiftMonth(-1)}
            onNext={() => shiftMonth(1)}
          />
        )}

        <aside className="rounded-xl border border-zinc-800/80 bg-black/30 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">Histórico</p>
          <ul className="mt-3 max-h-96 space-y-2 overflow-y-auto text-sm">
            {history?.items.map((h) => (
              <li key={h.id}>
                <button
                  type="button"
                  onClick={() => setSelected(h.scale_date)}
                  className="w-full rounded border border-zinc-800/80 px-2 py-2 text-left hover:border-zinc-600"
                >
                  <p className="font-medium text-zinc-200">{h.title}</p>
                  <p className="text-[11px] text-zinc-500">
                    {new Date(h.scale_date + "T12:00:00").toLocaleDateString("pt-BR")} · {h.team_count} eq. · {h.status}
                  </p>
                </button>
              </li>
            ))}
            {history && history.items.length === 0 && (
              <li className="text-zinc-500">Nenhuma escala registrada.</li>
            )}
          </ul>
        </aside>
      </div>

      <div className="mt-4 flex flex-wrap gap-3 text-[10px] uppercase tracking-wider text-zinc-500">
        <span className="inline-flex items-center gap-1">
          <span className="h-3 w-3 rounded bg-emerald-950/60 ring-1 ring-emerald-700/50" /> Publicada
        </span>
        <span className="inline-flex items-center gap-1">
          <span className="h-3 w-3 rounded bg-amber-950/40 ring-1 ring-amber-700/40" /> Rascunho
        </span>
      </div>

      {selected && (
        <>
          <button
            type="button"
            className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
            aria-label="Fechar painel"
            onClick={() => setSelected(null)}
          />
          <ScaleDayDrawer
            open
            isoDate={selected}
            detail={detail}
            canEdit={canEdit}
            busy={busy}
            onClose={() => setSelected(null)}
            onCreateScale={handleCreateScale}
            onPublish={handlePublish}
            onAddTeam={handleAddTeam}
            onEditTeam={handleEditTeam}
            onRemoveTeam={handleRemoveTeam}
            onDeleteScale={handleDeleteScale}
          />
        </>
      )}
    </OperationalLayout>
  );
}
