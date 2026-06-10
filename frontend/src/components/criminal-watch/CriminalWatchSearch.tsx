import { useState } from "react";
import { ApiError } from "@/services/api";
import * as criminalWatchApi from "@/services/criminalWatchApi";
import type { CriminalWatchVehiclePublic } from "@/types/criminalWatch";
import { CriminalWatchDetail } from "./CriminalWatchDetail";

const inputClass =
  "w-full rounded-lg border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR");
}

interface Props {
  token: string;
  onDataChanged: () => void;
}

export function CriminalWatchSearch({ token, onDataChanged }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CriminalWatchVehiclePublic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const term = query.trim();
    if (!term) return;
    setLoading(true);
    setError(null);
    try {
      const rows = await criminalWatchApi.searchCriminalWatchVehicles(token, term);
      setResults(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro na pesquisa");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleted = (id: number) => {
    setResults((prev) => prev.filter((r) => r.id !== id));
    setSelectedId(null);
    onDataChanged();
  };

  return (
    <div className="space-y-6">
      <form onSubmit={(e) => void handleSearch(e)} className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500">
            Pesquisar (placa, modelo, cor ou QRU)
          </label>
          <input
            className={inputClass}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ex.: ABC1D23, Corolla, F01"
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
        <div className="overflow-x-auto rounded-xl border border-zinc-800/80">
          <table className="min-w-full divide-y divide-zinc-800 text-sm">
            <thead className="bg-zinc-950/80">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Placa
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Modelo
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Cor
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Ano
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  QRU
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                  Cadastro
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {results.map((row) => (
                <tr
                  key={row.id}
                  className="cursor-pointer hover:bg-zinc-900/40"
                  onClick={() => setSelectedId(row.id)}
                >
                  <td className="px-4 py-3 font-mono text-zinc-300">{row.plate}</td>
                  <td className="px-4 py-3 text-zinc-200">{row.vehicle_model}</td>
                  <td className="px-4 py-3 text-zinc-400">{row.color}</td>
                  <td className="px-4 py-3 text-zinc-400">{row.year}</td>
                  <td className="px-4 py-3 text-zinc-400">
                    {row.qru_code}
                    <span className="text-zinc-600"> · {row.qru_description}</span>
                  </td>
                  <td className="px-4 py-3 text-zinc-500">{formatDate(row.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && query.trim() && results.length === 0 && !error && (
        <p className="text-sm text-zinc-500">Nenhum veículo encontrado para &quot;{query.trim()}&quot;.</p>
      )}

      {selectedId !== null && (
        <CriminalWatchDetail
          token={token}
          vehicleId={selectedId}
          onClose={() => setSelectedId(null)}
          onUpdated={onDataChanged}
          onDeleted={() => handleDeleted(selectedId)}
        />
      )}
    </div>
  );
}
