import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Eye } from "lucide-react";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as opApi from "@/services/operationalPublicationsApi";
import type {
  OperationalPublicationDetail,
  OperationalPublicationHistoryItem,
} from "@/types/operationalPublication";
import { SCALE_EDITOR_ROLES } from "@/types";

export function OperationalPublicationHistoryPage() {
  const { token, user } = useAuth();
  const canEdit = user ? SCALE_EDITOR_ROLES.includes(user.role) : false;
  const [items, setItems] = useState<OperationalPublicationHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const [detail, setDetail] = useState<OperationalPublicationDetail | null>(null);

  const load = useCallback(async () => {
    if (!token) return;
    setErr(null);
    try {
      const h = await opApi.listPublicationHistory(token, { limit: 50 });
      setItems(h.items);
      setTotal(h.total);
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Falha ao carregar histórico");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function openVersion(id: number) {
    if (!token) return;
    try {
      setDetail(await opApi.getPublication(token, id));
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Falha ao abrir versão");
    }
  }

  if (!canEdit && !token) {
    return null;
  }

  return (
    <OperationalLayout>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-zinc-500">
            Versões imutáveis
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-50">Histórico de Publicações</h1>
          <p className="mt-1 text-sm text-zinc-400">{total} registro(s)</p>
        </div>
        <Link
          to="/publicacao-operacional"
          className="inline-flex items-center gap-2 rounded border border-zinc-700 px-3 py-2 text-sm text-zinc-300"
        >
          <ArrowLeft className="h-4 w-4" />
          Centro
        </Link>
      </div>

      {err && (
        <p className="mb-4 rounded border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <ul className="space-y-2">
          {items.map((row) => (
            <li key={row.id}>
              <button
                type="button"
                onClick={() => void openVersion(row.id)}
                className="flex w-full items-start justify-between gap-3 rounded-lg border border-zinc-800 bg-black/30 px-4 py-3 text-left hover:border-zinc-600"
              >
                <div>
                  <p className="text-sm font-medium text-zinc-100">
                    v{row.version} · Nº {row.publication_number} ·{" "}
                    {new Date(row.scale_date + "T12:00:00").toLocaleDateString("pt-BR")}
                  </p>
                  <p className="mt-1 text-xs text-zinc-500">
                    {row.published_by_label ?? "—"} · {row.status}
                    {row.publish_reason ? ` · ${row.publish_reason}` : ""}
                  </p>
                  {row.change_summary && (
                    <p className="mt-1 text-xs text-zinc-400">{row.change_summary}</p>
                  )}
                </div>
                <Eye className="mt-1 h-4 w-4 shrink-0 text-zinc-500" />
              </button>
            </li>
          ))}
          {items.length === 0 && (
            <li className="text-sm text-zinc-500">Nenhuma publicação registrada.</li>
          )}
        </ul>

        <aside className="rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
          {!detail && (
            <p className="text-sm text-zinc-500">Selecione uma versão para visualizar a mensagem e a auditoria.</p>
          )}
          {detail && (
            <div className="space-y-4">
              <div>
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">
                  Versão {detail.version} · {detail.status}
                </p>
                <p className="mt-1 text-sm text-zinc-300">
                  {detail.published_by_label} ·{" "}
                  {detail.published_at
                    ? new Date(detail.published_at).toLocaleString("pt-BR")
                    : "—"}
                </p>
                {detail.previous_publication_id && (
                  <p className="mt-1 text-xs text-zinc-500">
                    Anterior: publicação #{detail.previous_publication_id} (comparação futura)
                  </p>
                )}
              </div>
              {detail.generated_message && (
                <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-black/40 p-3 font-mono text-[11px] text-zinc-200">
                  {detail.generated_message}
                </pre>
              )}
              <div>
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">Auditoria</p>
                <ul className="mt-2 space-y-2">
                  {detail.audits.map((a) => (
                    <li key={a.id} className="rounded border border-zinc-800 px-3 py-2 text-xs text-zinc-400">
                      <span className="font-medium text-zinc-200">{a.action}</span> · {a.actor_label} ·{" "}
                      {new Date(a.created_at).toLocaleString("pt-BR")}
                      {a.details && <p className="mt-1 text-zinc-500">{a.details}</p>}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </aside>
      </div>
    </OperationalLayout>
  );
}
