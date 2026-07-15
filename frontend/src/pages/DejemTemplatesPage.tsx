import { useCallback, useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as dejemApi from "@/services/dejemApi";
import { isDejemShiftEditorRole } from "@/types";
import type {
  DejemShiftTemplatePublic,
  DejemShiftType,
} from "@/types/dejem";
import {
  DEJEM_SHIFT_TYPE_LABELS,
  dejemTimeInputValue,
  formatDejemTime,
} from "@/types/dejem";

type FormState = {
  name: string;
  shift_type: DejemShiftType;
  start_time: string;
  end_time: string;
  default_capacity: number;
  is_active: boolean;
};

const blankForm = (): FormState => ({
  name: "",
  shift_type: "FT",
  start_time: "04:55",
  end_time: "12:55",
  default_capacity: 4,
  is_active: true,
});

export function DejemTemplatesPage() {
  const { token, user } = useAuth();
  const canEdit = user ? isDejemShiftEditorRole(user.role) : false;

  const [rows, setRows] = useState<DejemShiftTemplatePublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(blankForm);
  const [editingId, setEditingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setRows(await dejemApi.listDejemShiftTemplates(token, false));
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao carregar templates");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!canEdit) {
    return <Navigate to="/dejem/shifts" replace />;
  }

  const onSubmit = async () => {
    if (!token) return;
    setBusy(true);
    setError(null);
    setMsg(null);
    const payload = {
      name: form.name.trim(),
      shift_type: form.shift_type,
      start_time: form.start_time.length === 5 ? `${form.start_time}:00` : form.start_time,
      end_time: form.end_time.length === 5 ? `${form.end_time}:00` : form.end_time,
      default_capacity: form.default_capacity,
      is_active: form.is_active,
    };
    try {
      if (editingId != null) {
        await dejemApi.updateDejemShiftTemplate(token, editingId, payload);
        setMsg("Template atualizado.");
      } else {
        await dejemApi.createDejemShiftTemplate(token, payload);
        setMsg("Template criado.");
      }
      setForm(blankForm());
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao salvar template");
    } finally {
      setBusy(false);
    }
  };

  const startEdit = (row: DejemShiftTemplatePublic) => {
    setEditingId(row.id);
    setForm({
      name: row.name,
      shift_type: row.shift_type,
      start_time: dejemTimeInputValue(row.start_time),
      end_time: dejemTimeInputValue(row.end_time),
      default_capacity: row.default_capacity,
      is_active: row.is_active,
    });
  };

  const onDelete = async (id: number) => {
    if (!token || !window.confirm("Excluir este template?")) return;
    setBusy(true);
    setError(null);
    try {
      await dejemApi.deleteDejemShiftTemplate(token, id);
      if (editingId === id) {
        setEditingId(null);
        setForm(blankForm());
      }
      setMsg("Template excluído.");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "Erro ao excluir template");
    } finally {
      setBusy(false);
    }
  };

  return (
    <OperationalLayout>
      <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">DEJEM</p>
          <h1 className="mt-2 text-2xl font-semibold text-zinc-50">Templates de Horários</h1>
          <p className="mt-2 max-w-xl text-sm text-zinc-400">
            Modelos reutilizáveis ao criar escalas no calendário.
          </p>
        </div>
        <Link
          to="/dejem/shifts"
          className="rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-200 hover:border-zinc-500 hover:bg-zinc-900"
        >
          Voltar às Escalas
        </Link>
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

      <section className="mb-8 rounded-xl border border-zinc-800 bg-zinc-950/60 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
          {editingId != null ? "Editar template" : "Novo template"}
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label className="text-sm sm:col-span-2 lg:col-span-1">
            <span className="mb-1 block text-zinc-500">Nome</span>
            <input
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="FT Manhã"
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Tipo</span>
            <select
              value={form.shift_type}
              onChange={(e) =>
                setForm((f) => ({ ...f, shift_type: e.target.value as DejemShiftType }))
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            >
              {(Object.keys(DEJEM_SHIFT_TYPE_LABELS) as DejemShiftType[]).map((k) => (
                <option key={k} value={k}>
                  {DEJEM_SHIFT_TYPE_LABELS[k]}
                </option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Capacidade</span>
            <input
              type="number"
              min={0}
              value={form.default_capacity}
              onChange={(e) =>
                setForm((f) => ({ ...f, default_capacity: Number(e.target.value) }))
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Início</span>
            <input
              type="time"
              value={form.start_time}
              onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block text-zinc-500">Fim</span>
            <input
              type="time"
              value={form.end_time}
              onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="flex items-end gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
              className="accent-zinc-200"
            />
            Ativo
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy || !form.name.trim()}
            onClick={() => void onSubmit()}
            className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
          >
            {editingId != null ? "Salvar" : "Criar template"}
          </button>
          {editingId != null && (
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setEditingId(null);
                setForm(blankForm());
              }}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900"
            >
              Cancelar edição
            </button>
          )}
        </div>
      </section>

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-zinc-400">Nenhum template cadastrado.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-800">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-800 bg-zinc-900/60 text-xs uppercase tracking-wider text-zinc-500">
              <tr>
                <th className="px-4 py-3 font-medium">Nome</th>
                <th className="px-4 py-3 font-medium">Tipo</th>
                <th className="px-4 py-3 font-medium">Horário</th>
                <th className="px-4 py-3 font-medium">Capacidade</th>
                <th className="px-4 py-3 font-medium">Ativo</th>
                <th className="px-4 py-3 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-zinc-900/80">
                  <td className="px-4 py-3 text-zinc-100">{row.name}</td>
                  <td className="px-4 py-3 text-zinc-300">
                    {DEJEM_SHIFT_TYPE_LABELS[row.shift_type]}
                  </td>
                  <td className="px-4 py-3 tabular-nums text-zinc-300">
                    {formatDejemTime(row.start_time)} – {formatDejemTime(row.end_time)}
                  </td>
                  <td className="px-4 py-3 tabular-nums text-zinc-300">{row.default_capacity}</td>
                  <td className="px-4 py-3 text-zinc-300">{row.is_active ? "Sim" : "Não"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => startEdit(row)}
                        className="rounded-md border border-zinc-700 px-2.5 py-1 text-xs text-zinc-300 hover:bg-zinc-900"
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void onDelete(row.id)}
                        className="rounded-md border border-red-900/60 px-2.5 py-1 text-xs text-red-300 hover:bg-red-950/40"
                      >
                        Excluir
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </OperationalLayout>
  );
}
