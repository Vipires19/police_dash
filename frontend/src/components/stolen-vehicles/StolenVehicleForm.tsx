import { useState } from "react";
import { ApiError } from "@/services/api";
import * as stolenVehiclesApi from "@/services/stolenVehiclesApi";
import type { StolenOccurrenceType, StolenVehicleType } from "@/types/stolenVehicles";
import {
  STOLEN_OCCURRENCE_TYPE_LABELS,
  STOLEN_VEHICLE_TYPE_LABELS,
} from "@/types/stolenVehicles";

const inputClass =
  "w-full rounded-lg border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none";

const labelClass = "mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500";

interface Props {
  token: string;
  onCreated: () => void;
}

export function StolenVehicleForm({ token, onCreated }: Props) {
  const [vehicleType, setVehicleType] = useState<StolenVehicleType>("CARRO");
  const [plate, setPlate] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [color, setColor] = useState("");
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [occurrenceType, setOccurrenceType] = useState<StolenOccurrenceType>("FURTO");
  const [observation, setObservation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      const parsedYear = Number(year);
      if (!Number.isInteger(parsedYear) || parsedYear < 1900 || parsedYear > 2100) {
        throw new Error("Ano inválido.");
      }
      await stolenVehiclesApi.createStolenVehicle(token, {
        vehicle_type: vehicleType,
        plate: plate.trim(),
        vehicle_model: vehicleModel.trim(),
        color: color.trim(),
        year: parsedYear,
        occurrence_type: occurrenceType,
        observation: observation.trim() || null,
      });
      setPlate("");
      setVehicleModel("");
      setColor("");
      setObservation("");
      setMsg("Veículo cadastrado com sucesso.");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : err instanceof Error ? err.message : "Erro ao cadastrar");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="max-w-2xl space-y-5">
      {error && (
        <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">{error}</p>
      )}
      {msg && (
        <p className="rounded-lg border border-emerald-900/60 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-300">
          {msg}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Tipo</label>
          <select
            className={inputClass}
            value={vehicleType}
            onChange={(e) => setVehicleType(e.target.value as StolenVehicleType)}
          >
            {(Object.keys(STOLEN_VEHICLE_TYPE_LABELS) as StolenVehicleType[]).map((t) => (
              <option key={t} value={t}>
                {STOLEN_VEHICLE_TYPE_LABELS[t]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Natureza</label>
          <select
            className={inputClass}
            value={occurrenceType}
            onChange={(e) => setOccurrenceType(e.target.value as StolenOccurrenceType)}
          >
            {(Object.keys(STOLEN_OCCURRENCE_TYPE_LABELS) as StolenOccurrenceType[]).map((t) => (
              <option key={t} value={t}>
                {STOLEN_OCCURRENCE_TYPE_LABELS[t]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Placa</label>
          <input
            className={inputClass}
            value={plate}
            onChange={(e) => setPlate(e.target.value.toUpperCase())}
            placeholder="Ex.: FWB0F63"
            required
            maxLength={16}
          />
        </div>
        <div>
          <label className={labelClass}>Veículo / Modelo</label>
          <input
            className={inputClass}
            value={vehicleModel}
            onChange={(e) => setVehicleModel(e.target.value)}
            placeholder="Ex.: CG 160"
            required
            maxLength={128}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Cor</label>
          <input
            className={inputClass}
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder="Ex.: Vermelha"
            required
            maxLength={64}
          />
        </div>
        <div>
          <label className={labelClass}>Ano</label>
          <input
            className={inputClass}
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            min={1900}
            max={2100}
            required
          />
        </div>
      </div>

      <div>
        <label className={labelClass}>Observação (opcional)</label>
        <textarea
          className={`${inputClass} min-h-[80px] resize-y`}
          value={observation}
          onChange={(e) => setObservation(e.target.value)}
          maxLength={4000}
        />
      </div>

      <button
        type="submit"
        disabled={busy}
        className="rounded-lg border border-zinc-600 bg-zinc-100 px-5 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
      >
        {busy ? "Salvando…" : "Cadastrar veículo"}
      </button>
    </form>
  );
}
