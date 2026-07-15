import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as scalesApi from "@/services/serviceScalesApi";
import type { ScaleVersionPublic } from "@/types/serviceScale";

interface Props {
  scaleId: number;
}

export function ScaleVersionsPanel({ scaleId }: Props) {
  const { token } = useAuth();
  const [versions, setVersions] = useState<ScaleVersionPublic[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [exporting, setExporting] = useState<number | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    void scalesApi
      .listScaleVersions(token, scaleId)
      .then((rows) => {
        if (!cancelled) setVersions(rows);
      })
      .catch((e) => {
        if (!cancelled) {
          setErr(e instanceof ApiError ? e.detail : "Erro ao carregar versões");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token, scaleId]);

  const openVersionExport = async (versionNumber: number) => {
    if (!token) return;
    setExporting(versionNumber);
    try {
      const res = await scalesApi.exportScaleVersion(token, scaleId, versionNumber);
      await navigator.clipboard.writeText(res.text);
      window.alert(`Versão ${versionNumber} copiada para a área de transferência.`);
    } catch (e) {
      window.alert(e instanceof ApiError ? e.detail : "Falha ao exportar versão");
    } finally {
      setExporting(null);
    }
  };

  if (versions.length === 0 && !err) return null;

  return (
    <section className="mt-6 space-y-3 border-t border-zinc-800 pt-5">
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-zinc-500">
        Histórico de versões
      </p>
      {err && <p className="text-xs text-red-300">{err}</p>}
      <ul className="space-y-2">
        {versions.map((v) => (
          <li
            key={v.id}
            className="rounded-lg border border-zinc-800 bg-zinc-900/40 px-3 py-2 text-xs text-zinc-300"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="font-medium text-zinc-100">
                  Versão {v.version_number}
                  <span className="ml-2 font-normal text-zinc-500">
                    {new Date(v.published_at).toLocaleString("pt-BR")}
                  </span>
                </p>
                <p className="mt-0.5 text-zinc-500">
                  {v.published_by_label ?? "—"}
                  {v.dejem_integrated_count > 0
                    ? ` · ${v.dejem_integrated_count} DEJEM`
                    : ""}
                </p>
                {v.change_summary && (
                  <p className="mt-1 text-[11px] leading-relaxed text-zinc-400">
                    {v.change_summary}
                  </p>
                )}
              </div>
              <button
                type="button"
                disabled={exporting === v.version_number}
                onClick={() => void openVersionExport(v.version_number)}
                className="shrink-0 text-[11px] text-sky-300 hover:text-sky-200 disabled:opacity-50"
              >
                {exporting === v.version_number ? "…" : "Copiar"}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
