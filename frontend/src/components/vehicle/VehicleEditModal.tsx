import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import type { Vehicle, VehicleStatus, VehicleUpdatePayload } from "@/types/vehicle";
import { VEHICLE_EDIT_STATUS_OPTIONS } from "@/types/vehicle";

export interface VehicleEditFormState {
  placa: string;
  prefixo: string;
  modelo: string;
  modalidade: Vehicle["modalidade"];
  status: VehicleStatus;
  observacoes: string;
  statusMotivo: string;
}

function vehicleToForm(v: Vehicle): VehicleEditFormState {
  return {
    placa: v.placa,
    prefixo: v.prefixo,
    modelo: v.modelo,
    modalidade: v.modalidade,
    status: v.status,
    observacoes: v.observacoes ?? "",
    statusMotivo: "",
  };
}

export function buildVehicleUpdatePayload(
  original: Vehicle,
  form: VehicleEditFormState,
): VehicleUpdatePayload {
  const payload: VehicleUpdatePayload = {
    placa: form.placa.trim().toUpperCase(),
    prefixo: form.prefixo.trim(),
    modelo: form.modelo.trim(),
    modalidade: form.modalidade,
    observacoes: form.observacoes.trim() || null,
  };
  if (form.status !== original.status) {
    payload.status = form.status;
    payload.status_motivo = form.statusMotivo.trim();
  }
  return payload;
}

interface VehicleEditModalProps {
  vehicle: Vehicle;
  saving: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (payload: VehicleUpdatePayload) => void | Promise<void>;
}

export function VehicleEditModal({
  vehicle,
  saving,
  error,
  onClose,
  onSubmit,
}: VehicleEditModalProps) {
  const [form, setForm] = useState(() => vehicleToForm(vehicle));
  const statusChanged = form.status !== vehicle.status;

  useEffect(() => {
    setForm(vehicleToForm(vehicle));
  }, [vehicle]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (statusChanged && !form.statusMotivo.trim()) return;
    void onSubmit(buildVehicleUpdatePayload(vehicle, form));
  }

  return (
    <form
      className="w-full max-w-md space-y-3 rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl"
      onSubmit={handleSubmit}
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-50">Editar viatura — {vehicle.prefixo}</h2>
        <button type="button" className="text-zinc-500 hover:text-zinc-200" onClick={onClose} aria-label="Fechar">
          ✕
        </button>
      </div>

      {error ? (
        <div className="rounded-md border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {error}
        </div>
      ) : null}

      <Field label="Prefixo">
        <input
          required
          className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
          value={form.prefixo}
          onChange={(e) => setForm((f) => ({ ...f, prefixo: e.target.value }))}
        />
      </Field>
      <Field label="Placa">
        <input
          required
          className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 font-mono text-sm uppercase"
          value={form.placa}
          onChange={(e) => setForm((f) => ({ ...f, placa: e.target.value }))}
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
      <Field label="Modalidade operacional">
        <select
          className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
          value={form.modalidade}
          onChange={(e) => setForm((f) => ({ ...f, modalidade: e.target.value as Vehicle["modalidade"] }))}
        >
          <option value="FT">FT</option>
          <option value="ROCAM">ROCAM</option>
        </select>
      </Field>
      <Field label="Status operacional">
        <select
          className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
          value={form.status}
          onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as VehicleStatus }))}
        >
          {VEHICLE_EDIT_STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
          {vehicle.status === "RESERVA" ? <option value="RESERVA">RESERVA</option> : null}
        </select>
      </Field>
      {statusChanged ? (
        <Field label="Motivo da alteração de status (obrigatório)">
          <textarea
            required
            minLength={2}
            rows={2}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
            value={form.statusMotivo}
            onChange={(e) => setForm((f) => ({ ...f, statusMotivo: e.target.value }))}
          />
        </Field>
      ) : null}
      <Field label="Observações">
        <textarea
          rows={3}
          className="w-full rounded-md border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm"
          value={form.observacoes}
          onChange={(e) => setForm((f) => ({ ...f, observacoes: e.target.value }))}
          placeholder="Anotações operacionais (opcional)"
        />
      </Field>
      <button
        type="submit"
        disabled={saving || (statusChanged && !form.statusMotivo.trim())}
        className="mt-2 w-full rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
      >
        {saving ? "Salvando…" : "Salvar alterações"}
      </button>
    </form>
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
