import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/services/api";
import * as vehicleQruCodesApi from "@/services/vehicleQruCodesApi";
import type { VehicleQruCodePublic } from "@/types/criminalWatch";

const inputClass =
  "w-full rounded-lg border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none";

const labelClass = "mb-1 block text-xs font-medium uppercase tracking-wide text-zinc-500";

interface Props {
  token: string;
}

export function QruCodeAdmin({ token }: Props) {
  const [codes, setCodes] = useState<VehicleQruCodePublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [editCode, setEditCode] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await vehicleQruCodesApi.listVehicleQruCodes(token);
      setCodes(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao carregar QRUs");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await vehicleQruCodesApi.createVehicleQruCode(token, {
        code: code.trim(),
        description: description.trim(),
      });
      setCode("");
      setDescription("");
      setMsg("Código QRU cadastrado.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao cadastrar QRU");
    } finally {
      setBusy(false);
    }
  };

  const startEdit = (row: VehicleQruCodePublic) => {
    setEditId(row.id);
    setEditCode(row.code);
    setEditDescription(row.description);
    setMsg(null);
    setError(null);
  };

  const handleSaveEdit = async () => {
    if (editId === null) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await vehicleQruCodesApi.updateVehicleQruCode(token, editId, {
        code: editCode.trim(),
        description: editDescription.trim(),
      });
      setEditId(null);
      setMsg("Código QRU atualizado.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao atualizar QRU");
    } finally {
      setBusy(false);
    }
  };

  const handleDeactivate = async (id: number) => {
    setBusy(true);
    setError(null);
    setMsg(null);
    try {
      await vehicleQruCodesApi.deactivateVehicleQruCode(token, id);
      setMsg("Código QRU desativado.");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao desativar QRU");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-8">
      {error && (
        <p className="rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">{error}</p>
      )}
      {msg && (
        <p className="rounded-lg border border-emerald-900/60 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-300">
          {msg}
        </p>
      )}

      <form onSubmit={(e) => void handleCreate(e)} className="max-w-xl space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-zinc-400">Cadastrar QRU</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass}>Código</label>
            <input
              className={inputClass}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Ex.: F01"
              required
              maxLength={16}
            />
          </div>
          <div>
            <label className={labelClass}>Descrição</label>
            <input
              className={inputClass}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex.: Drogas"
              required
              maxLength={256}
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={busy}
          className="rounded-lg border border-zinc-600 bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
        >
          {busy ? "Salvando…" : "Cadastrar"}
        </button>
      </form>

      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-zinc-400">Códigos cadastrados</h3>
        {loading && <p className="text-sm text-zinc-500">Carregando…</p>}
        {!loading && codes.length === 0 && (
          <p className="text-sm text-zinc-500">Nenhum código QRU cadastrado.</p>
        )}
        {codes.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-zinc-800/80">
            <table className="min-w-full divide-y divide-zinc-800 text-sm">
              <thead className="bg-zinc-950/80">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                    Código
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                    Descrição
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-zinc-500">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-zinc-500">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60">
                {codes.map((row) => (
                  <tr key={row.id} className="hover:bg-zinc-900/40">
                    {editId === row.id ? (
                      <>
                        <td className="px-4 py-3">
                          <input
                            className={inputClass}
                            value={editCode}
                            onChange={(e) => setEditCode(e.target.value)}
                            maxLength={16}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            className={inputClass}
                            value={editDescription}
                            onChange={(e) => setEditDescription(e.target.value)}
                            maxLength={256}
                          />
                        </td>
                        <td className="px-4 py-3 text-zinc-400">
                          {row.is_active ? "Ativo" : "Inativo"}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => void handleSaveEdit()}
                              className="rounded-md border border-emerald-800/60 px-2 py-1 text-xs text-emerald-300"
                            >
                              Salvar
                            </button>
                            <button
                              type="button"
                              onClick={() => setEditId(null)}
                              className="rounded-md border border-zinc-600 px-2 py-1 text-xs text-zinc-400"
                            >
                              Cancelar
                            </button>
                          </div>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-4 py-3 font-mono text-zinc-200">{row.code}</td>
                        <td className="px-4 py-3 text-zinc-300">{row.description}</td>
                        <td className="px-4 py-3">
                          <span
                            className={[
                              "inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium",
                              row.is_active
                                ? "bg-emerald-950/60 text-emerald-300 ring-1 ring-emerald-800/60"
                                : "bg-zinc-800/60 text-zinc-400 ring-1 ring-zinc-700/60",
                            ].join(" ")}
                          >
                            {row.is_active ? "Ativo" : "Inativo"}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex justify-end gap-2">
                            {row.is_active && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => startEdit(row)}
                                  className="rounded-md border border-zinc-600 px-2 py-1 text-xs text-zinc-300"
                                >
                                  Editar
                                </button>
                                <button
                                  type="button"
                                  disabled={busy}
                                  onClick={() => void handleDeactivate(row.id)}
                                  className="rounded-md border border-red-800/60 px-2 py-1 text-xs text-red-300"
                                >
                                  Desativar
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
