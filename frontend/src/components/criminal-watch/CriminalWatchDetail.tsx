import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { ApiError } from "@/services/api";
import * as criminalWatchApi from "@/services/criminalWatchApi";
import type { CriminalWatchVehicleDetail } from "@/types/criminalWatch";

const inputClass =
  "w-full rounded-lg border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-zinc-500 focus:outline-none";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("pt-BR");
}

interface Props {
  token: string;
  vehicleId: number;
  onClose: () => void;
  onUpdated: () => void;
  onDeleted: () => void;
}

export function CriminalWatchDetail({ token, vehicleId, onClose, onUpdated, onDeleted }: Props) {
  const [detail, setDetail] = useState<CriminalWatchVehicleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newNote, setNewNote] = useState("");
  const [adding, setAdding] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await criminalWatchApi.getCriminalWatchVehicle(token, vehicleId);
      setDetail(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao carregar ficha");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [token, vehicleId]);

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    setAdding(true);
    setError(null);
    try {
      await criminalWatchApi.addCriminalWatchNote(token, vehicleId, newNote.trim());
      setNewNote("");
      await load();
      onUpdated();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao adicionar anotação");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await criminalWatchApi.deleteCriminalWatchVehicle(token, vehicleId);
      onDeleted();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Erro ao excluir veículo");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Fechar"
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative z-10 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Ficha técnica</p>
            <h3 className="mt-1 text-xl font-semibold text-zinc-50">
              {detail?.plate ?? "Carregando…"}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-2 text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <p className="mb-4 rounded-lg border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </p>
        )}

        {loading && <p className="text-sm text-zinc-500">Carregando…</p>}

        {detail && !loading && (
          <div className="space-y-6">
            <dl className="grid gap-3 sm:grid-cols-2 text-sm">
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Placa</dt>
                <dd className="font-mono text-zinc-200">{detail.plate}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Modelo</dt>
                <dd className="text-zinc-200">{detail.vehicle_model}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Cor</dt>
                <dd className="text-zinc-200">{detail.color}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Ano</dt>
                <dd className="text-zinc-200">{detail.year}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">QRU</dt>
                <dd className="text-zinc-200">{detail.qru_code}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Descrição do QRU</dt>
                <dd className="text-zinc-200">{detail.qru_description}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Data de cadastro</dt>
                <dd className="text-zinc-200">{formatDate(detail.created_at)}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase tracking-wide text-zinc-500">Cadastrado por</dt>
                <dd className="text-zinc-200">{detail.created_by_label ?? "—"}</dd>
              </div>
            </dl>

            <section>
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
                Histórico operacional
              </h4>
              {detail.notes.length === 0 ? (
                <p className="text-sm text-zinc-500">Nenhuma anotação registrada.</p>
              ) : (
                <ul className="space-y-3">
                  {detail.notes.map((n) => (
                    <li
                      key={n.id}
                      className="rounded-lg border border-zinc-800/80 bg-zinc-900/40 px-4 py-3"
                    >
                      <p className="text-xs text-zinc-500">{formatDate(n.created_at)}</p>
                      <p className="mt-1 text-sm text-zinc-200">{n.note}</p>
                      {n.created_by_label && (
                        <p className="mt-1 text-xs text-zinc-600">{n.created_by_label}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <form onSubmit={(e) => void handleAddNote(e)} className="space-y-3">
              <label className="block text-xs font-medium uppercase tracking-wide text-zinc-500">
                Nova anotação
              </label>
              <textarea
                className={`${inputClass} min-h-[80px] resize-y`}
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="Ex.: Abordado pela FT."
                maxLength={4000}
              />
              <button
                type="submit"
                disabled={adding || !newNote.trim()}
                className="rounded-lg border border-zinc-600 bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 hover:bg-white disabled:opacity-50"
              >
                {adding ? "Salvando…" : "Adicionar"}
              </button>
            </form>

            {deleteConfirm ? (
              <div className="rounded-lg border border-red-900/60 bg-red-950/20 p-4">
                <p className="text-sm text-zinc-300">
                  Tem certeza que deseja excluir este veículo?
                  <br />
                  Esta ação não poderá ser desfeita. Todas as anotações serão removidas.
                </p>
                <div className="mt-3 flex gap-2">
                  <button
                    type="button"
                    disabled={deleting}
                    onClick={() => setDeleteConfirm(false)}
                    className="rounded-md border border-zinc-600 px-3 py-1.5 text-xs font-medium text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    disabled={deleting}
                    onClick={() => void handleDelete()}
                    className="rounded-md border border-red-800/60 bg-red-950/40 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-900/40 disabled:opacity-50"
                  >
                    {deleting ? "Excluindo…" : "Excluir"}
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setDeleteConfirm(true)}
                className="rounded-md border border-red-800/60 bg-red-950/40 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-900/40"
              >
                Excluir registro
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
