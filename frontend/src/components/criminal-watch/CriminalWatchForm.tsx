import { useEffect, useState } from "react";
import { ApiError } from "@/services/api";
import * as criminalWatchApi from "@/services/criminalWatchApi";
import * as vehicleQruCodesApi from "@/services/vehicleQruCodesApi";
import type { VehicleQruCodePublic } from "@/types/criminalWatch";

const inputClass =
  "w-full rounded-lg border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none";

const labelClass = "mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500";

interface Props {
  token: string;
  onCreated: () => void;
}

export function CriminalWatchForm({ token, onCreated }: Props) {
  const [qruCodes, setQruCodes] = useState<VehicleQruCodePublic[]>([]);
  const [plate, setPlate] = useState("");
  const [vehicleModel, setVehicleModel] = useState("");
  const [color, setColor] = useState("");
  const [year, setYear] = useState(String(new Date().getFullYear()));
  const [qruCodeId, setQruCodeId] = useState("");
  const [initialNote, setInitialNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    void vehicleQruCodesApi.listActiveVehicleQruCodes(token).then(setQruCodes).catch(() => setQruCodes([]));
  }, [token]);

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
      const qruId = Number(qruCodeId);
      if (!qruId) {
        throw new Error("Selecione um código QRU.");
      }
      if (!initialNote.trim()) {
        throw new Error("A anotação inicial é obrigatória.");
      }
      await criminalWatchApi.createCriminalWatchVehicle(token, {
        plate: plate.trim(),
        vehicle_model: vehicleModel.trim(),
        color: color.trim(),
        year: parsedYear,
        qru_code_id: qruId,
        initial_note: initialNote.trim(),
      });
      setPlate("");
      setVehicleModel("");
      setColor("");
      setInitialNote("");
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

      {qruCodes.length === 0 && (
        <p className="rounded-lg border border-amber-900/60 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
          Nenhum código QRU ativo. Cadastre códigos na aba &quot;QRUs&quot; antes de registrar veículos.
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={labelClass}>Placa</label>
          <input
            className={inputClass}
            value={plate}
            onChange={(e) => setPlate(e.target.value)}
            placeholder="Ex.: ABC1D23"
            required
            maxLength={16}
          />
        </div>
        <div>
          <label className={labelClass}>Modelo</label>
          <input
            className={inputClass}
            value={vehicleModel}
            onChange={(e) => setVehicleModel(e.target.value)}
            placeholder="Ex.: Corolla"
            required
            maxLength={128}
          />
        </div>
        <div>
          <label className={labelClass}>Cor</label>
          <input
            className={inputClass}
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder="Ex.: Preto"
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
        <div className="sm:col-span-2">
          <label className={labelClass}>QRU</label>
          <select
            className={inputClass}
            value={qruCodeId}
            onChange={(e) => setQruCodeId(e.target.value)}
            required
          >
            <option value="">Selecione…</option>
            {qruCodes.map((q) => (
              <option key={q.id} value={q.id}>
                {q.code} — {q.description}
              </option>
            ))}
          </select>
        </div>
        <div className="sm:col-span-2">
          <label className={labelClass}>Anotação inicial</label>
          <textarea
            className={`${inputClass} min-h-[100px] resize-y`}
            value={initialNote}
            onChange={(e) => setInitialNote(e.target.value)}
            placeholder="Ex.: Visto em ponto de tráfico."
            required
            maxLength={4000}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={busy || qruCodes.length === 0}
        className="rounded-lg border border-zinc-600 bg-zinc-100 px-5 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
      >
        {busy ? "Cadastrando…" : "Cadastrar veículo"}
      </button>
    </form>
  );
}
