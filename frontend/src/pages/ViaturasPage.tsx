import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { VehicleStatusBadge } from "@/components/vehicle/VehicleStatusBadge";
import { useAuth } from "@/hooks/AuthContext";
import type { Vehicle, VehicleLog, VehicleStatus } from "@/types/vehicle";
import { ApiError } from "@/services/api";
import * as vehiclesApi from "@/services/vehiclesApi";

const STATUS_OPTIONS: VehicleStatus[] = ["OPERANDO", "BAIXADA", "MANUTENCAO", "RESERVA"];

function groupByModalidade(list: Vehicle[]) {
  const ft = list.filter((v) => v.modalidade === "FT");
  const rocam = list.filter((v) => v.modalidade === "ROCAM");
  return { ft, rocam };
}

export function ViaturasPage() {
  const { token, user } = useAuth();
  const canEdit = user?.role !== "ESTAGIO";

  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [createOpen, setCreateOpen] = useState(false);
  const [detail, setDetail] = useState<Vehicle | null>(null);
  const [detailLogs, setDetailLogs] = useState<VehicleLog[]>([]);
  const [statusTarget, setStatusTarget] = useState<Vehicle | null>(null);
  const [statusVal, setStatusVal] = useState<VehicleStatus>("OPERANDO");
  const [motivo, setMotivo] = useState("");
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    placa: "",
    prefixo: "",
    modelo: "",
    modalidade: "FT" as Vehicle["modalidade"],
    status: "OPERANDO" as VehicleStatus,
  });

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const list = await vehiclesApi.listVehicles(token);
      setVehicles(list);
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar viaturas");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!token || !detail) {
      setDetailLogs([]);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const logs = await vehiclesApi.listVehicleLogs(token, detail.id);
        if (!cancelled) setDetailLogs(logs);
      } catch {
        if (!cancelled) setDetailLogs([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, detail]);

  const { ft, rocam } = useMemo(() => groupByModalidade(vehicles), [vehicles]);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    try {
      await vehiclesApi.createVehicle(token, {
        placa: form.placa,
        prefixo: form.prefixo,
        modelo: form.modelo,
        modalidade: form.modalidade,
        status: form.status,
      });
      setCreateOpen(false);
      setForm({
        placa: "",
        prefixo: "",
        modelo: "",
        modalidade: "FT",
        status: "OPERANDO",
      });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao cadastrar");
    } finally {
      setSaving(false);
    }
  }

  async function onStatusSave(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !statusTarget) return;
    const vid = statusTarget.id;
    setSaving(true);
    setError(null);
    try {
      await vehiclesApi.changeVehicleStatus(token, vid, {
        new_status: statusVal,
        motivo: motivo.trim(),
      });
      setStatusTarget(null);
      setMotivo("");
      await load();
      setDetail((d) => (d && d.id === vid ? { ...d, status: statusVal } : d));
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao atualizar status");
    } finally {
      setSaving(false);
    }
  }

  function openStatus(v: Vehicle) {
    setStatusTarget(v);
    setStatusVal(v.status);
    setMotivo("");
  }

  return (
    <OperationalLayout>
      <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Operacional</p>
          <h1 className="mt-2 text-2xl font-semibold text-zinc-50 sm:text-3xl">Viaturas</h1>
          <p className="mt-2 max-w-xl text-sm text-zinc-400">
            Força Tática (4 rodas) e ROCAM (motos). Histórico completo por viatura.
          </p>
        </div>
        {canEdit && (
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="rounded-lg border border-zinc-600 bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-900 hover:bg-white"
          >
            Nova viatura
          </button>
        )}
      </header>

      {error && (
        <div className="mb-6 rounded-md border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : (
        <div className="space-y-12">
          <ModalidadeSection title="Força Tática (FT)" vehicles={ft} onOpen={setDetail} canEdit={canEdit} onStatus={openStatus} />
          <ModalidadeSection title="ROCAM" vehicles={rocam} onOpen={setDetail} canEdit={canEdit} onStatus={openStatus} />
        </div>
      )}

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 backdrop-blur-sm sm:items-center">
          <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-50">Nova viatura</h2>
              <button type="button" className="text-zinc-500 hover:text-zinc-200" onClick={() => setCreateOpen(false)}>
                ✕
              </button>
            </div>
            <form className="mt-4 space-y-3" onSubmit={(e) => void onCreate(e)}>
              <Field label="Placa">
                <input
                  required
                  className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 font-mono text-sm uppercase"
                  value={form.placa}
                  onChange={(e) => setForm((f) => ({ ...f, placa: e.target.value }))}
                />
              </Field>
              <Field label="Prefixo">
                <input
                  required
                  className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                  value={form.prefixo}
                  onChange={(e) => setForm((f) => ({ ...f, prefixo: e.target.value }))}
                />
              </Field>
              <Field label="Modelo">
                <input
                  required
                  className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                  value={form.modelo}
                  onChange={(e) => setForm((f) => ({ ...f, modelo: e.target.value }))}
                />
              </Field>
              <Field label="Modalidade">
                <select
                  className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                  value={form.modalidade}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, modalidade: e.target.value as Vehicle["modalidade"] }))
                  }
                >
                  <option value="FT">FT</option>
                  <option value="ROCAM">ROCAM</option>
                </select>
              </Field>
              <Field label="Status inicial">
                <select
                  className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                  value={form.status}
                  onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as VehicleStatus }))}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </Field>
              <button
                type="submit"
                disabled={saving}
                className="mt-2 w-full rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
              >
                {saving ? "Salvando…" : "Cadastrar"}
              </button>
            </form>
          </div>
        </div>
      )}

      {statusTarget && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 backdrop-blur-sm sm:items-center">
          <form
            className="w-full max-w-md space-y-4 rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl"
            onSubmit={(e) => void onStatusSave(e)}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-zinc-50">Alterar status — {statusTarget.prefixo}</h2>
              <button type="button" className="text-zinc-500 hover:text-zinc-200" onClick={() => setStatusTarget(null)}>
                ✕
              </button>
            </div>
            <Field label="Novo status">
              <select
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={statusVal}
                onChange={(e) => setStatusVal(e.target.value as VehicleStatus)}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Motivo (obrigatório)">
              <textarea
                required
                minLength={2}
                rows={3}
                className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
              />
            </Field>
            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
            >
              {saving ? "Salvando…" : "Registrar alteração"}
            </button>
          </form>
        </div>
      )}

      {detail && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <aside className="flex h-full w-full max-w-lg flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl">
            <div className="flex items-start justify-between border-b border-zinc-800 px-4 py-4">
              <div>
                <p className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Viatura</p>
                <p className="mt-1 font-mono text-xl font-semibold text-zinc-50">{detail.prefixo}</p>
                <p className="text-sm text-zinc-400">
                  {detail.placa} · {detail.modelo}
                </p>
                <div className="mt-2">
                  <VehicleStatusBadge status={detail.status} />
                </div>
              </div>
              <button type="button" className="text-zinc-500 hover:text-zinc-200" onClick={() => setDetail(null)}>
                ✕
              </button>
            </div>
            <div className="flex flex-wrap gap-2 border-b border-zinc-800 px-4 py-3">
              {canEdit && (
                <button
                  type="button"
                  onClick={() => openStatus(detail)}
                  className="rounded-md border border-zinc-600 px-3 py-1.5 text-xs text-zinc-100 hover:bg-zinc-900"
                >
                  Alterar status
                </button>
              )}
            </div>
            <div className="flex-1 overflow-y-auto px-4 py-4">
              <p className="text-xs uppercase tracking-wider text-zinc-500">Linha do tempo</p>
              <ul className="mt-4 space-y-4 border-l border-zinc-800 pl-4">
                {detailLogs.map((log) => (
                  <li key={log.id} className="relative">
                    <span className="absolute -left-[21px] top-1.5 h-2 w-2 rounded-full bg-zinc-500" />
                    <p className="text-[11px] text-zinc-500">
                      {new Date(log.created_at).toLocaleString("pt-BR")}
                    </p>
                    <p className="mt-1 text-sm text-zinc-200">{log.description}</p>
                    {log.motivo && (
                      <p className="mt-1 text-xs text-zinc-500">
                        Motivo: <span className="text-zinc-300">{log.motivo}</span>
                      </p>
                    )}
                  </li>
                ))}
              </ul>
              {detailLogs.length === 0 && <p className="text-sm text-zinc-500">Sem registros.</p>}
            </div>
          </aside>
        </div>
      )}
    </OperationalLayout>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <label className="text-xs uppercase tracking-wide text-zinc-500">{label}</label>
      <div className="mt-1">{children}</div>
    </div>
  );
}

function ModalidadeSection({
  title,
  vehicles,
  onOpen,
  canEdit,
  onStatus,
}: {
  title: string;
  vehicles: Vehicle[];
  onOpen: (v: Vehicle) => void;
  canEdit: boolean;
  onStatus: (v: Vehicle) => void;
}) {
  return (
    <section>
      <h2 className="border-b border-zinc-800 pb-2 text-sm font-semibold uppercase tracking-[0.2em] text-zinc-400">
        {title}
      </h2>
      {vehicles.length === 0 ? (
        <p className="mt-4 text-sm text-zinc-600">Nenhuma viatura cadastrada.</p>
      ) : (
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {vehicles.map((v) => (
            <article
              key={v.id}
              className="rounded-xl border border-zinc-800/90 bg-gradient-to-br from-zinc-900/60 to-black/40 p-4 shadow-inner shadow-black/30"
            >
              <button type="button" onClick={() => onOpen(v)} className="w-full text-left">
                <p className="font-mono text-lg font-semibold text-zinc-100">{v.prefixo}</p>
                <p className="mt-1 text-sm text-zinc-400">Modelo: {v.modelo}</p>
                <p className="mt-1 font-mono text-xs text-zinc-500">{v.placa}</p>
                <div className="mt-3">
                  <VehicleStatusBadge status={v.status} />
                </div>
              </button>
              {canEdit && (
                <button
                  type="button"
                  onClick={() => onStatus(v)}
                  className="mt-3 w-full rounded-md border border-zinc-700 py-1.5 text-xs text-zinc-300 hover:bg-zinc-900"
                >
                  Status
                </button>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
