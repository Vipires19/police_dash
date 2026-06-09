import { useState } from "react";
import { ApiError } from "@/services/api";
import * as stolenVehiclesApi from "@/services/stolenVehiclesApi";
import type { StolenVehiclePublic } from "@/types/stolenVehicles";
import {
  STOLEN_OCCURRENCE_TYPE_LABELS,
  STOLEN_VEHICLE_TYPE_LABELS,
} from "@/types/stolenVehicles";

const inputClass =
  "w-full rounded-lg border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none";

interface Props {
  token: string;
  onRecovered: () => void;
}

export function StolenVehicleSearch({ token, onRecovered }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StolenVehiclePublic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recoveringId, setRecoveringId] = useState<number | null>(null);
  const [recoverNotes, setRecoverNotes] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const term = query.trim();
    if (!term) return;
    setLoading(true);
    setError(null);
    try {
      const rows = await stolenVehiclesApi.searchStolenVehicles(token, term);
      setResults(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro na pesquisa");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRecover = async (id: number) => {
    setRecoveringId(id);
    setError(null);
    try {
      const updated = await stolenVehiclesApi.recoverStolenVehicle(token, id, {
        recovered_notes: recoverNotes.trim() || null,
      });
      setRecoverNotes("");
      setResults((prev) => prev.map((r) => (r.id === id ? updated : r)));
      onRecovered();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao marcar como localizado");
    } finally {
      setRecoveringId(null);
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={(e) => void handleSearch(e)} className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
            Pesquisar (placa, veículo ou cor)
          </label>
          <input
            className={inputClass}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex.: CG, Vermelha, AAA1234"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="rounded-lg border border-zinc-600 bg-zinc-100 px-5 py-2.5 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
        >
          {loading ? "Buscando…" : "Pesquisar"}
        </button>
      </form>

      {error && (
        <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">{error}</p>
      )}

      {results.length > 0 && (
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
            Observação da localização (opcional)
          </label>
          <input
            className={`${inputClass} mb-4 max-w-xl`}
            value={recoverNotes}
            onChange={(e) => setRecoverNotes(e.target.value)}
            placeholder="Ex.: Recuperado na ocorrência 1234/2026"
            maxLength={4000}
          />
        </div>
      )}

      {results.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-zinc-800/80">
          <table className="min-w-full divide-y divide-zinc-800 text-sm">
            <thead className="bg-zinc-950/80">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Veículo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Placa
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Tipo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Natureza
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Ação
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {results.map((row) => (
                <tr key={row.id} className="hover:bg-zinc-900/40">
                  <td className="px-4 py-3 text-zinc-200">
                    <span className="font-medium">{row.vehicle_model}</span>
                    <span className="text-zinc-500"> · {row.color}</span>
                    <span className="text-zinc-500"> · {row.year}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-zinc-300">{row.plate}</td>
                  <td className="px-4 py-3 text-zinc-400">{STOLEN_VEHICLE_TYPE_LABELS[row.vehicle_type]}</td>
                  <td className="px-4 py-3 text-zinc-400">{STOLEN_OCCURRENCE_TYPE_LABELS[row.occurrence_type]}</td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      <span
                        className={[
                          "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
                          row.is_recovered
                            ? "bg-emerald-950/60 text-emerald-300 ring-1 ring-emerald-800/60"
                            : "bg-amber-950/60 text-amber-300 ring-1 ring-amber-800/60",
                        ].join(" ")}
                      >
                        {row.is_recovered ? "Localizado" : "Não localizado"}
                      </span>
                      {row.recovered_notes && (
                        <p className="text-xs text-zinc-500">{row.recovered_notes}</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {!row.is_recovered && (
                      <button
                        type="button"
                        disabled={recoveringId === row.id}
                        onClick={() => void handleRecover(row.id)}
                        className="rounded-md border border-emerald-800/60 bg-emerald-950/40 px-3 py-1.5 text-xs font-medium text-emerald-300 hover:bg-emerald-900/40 disabled:opacity-50"
                      >
                        {recoveringId === row.id ? "Salvando…" : "Marcar como localizado"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && query.trim() && results.length === 0 && !error && (
        <p className="text-sm text-zinc-500">Nenhum veículo encontrado para &quot;{query.trim()}&quot;.</p>
      )}
    </div>
  );
}
