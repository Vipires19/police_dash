import { useCallback, useEffect, useState } from "react";
import { Check, Copy, X } from "lucide-react";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as scalesApi from "@/services/serviceScalesApi";

interface Props {
  open: boolean;
  scaleId: number | null;
  scaleTitle?: string;
  onClose: () => void;
}

export function ScaleExportModal({ open, scaleId, scaleTitle, onClose }: Props) {
  const { token } = useAuth();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const load = useCallback(async () => {
    if (!token || !scaleId) return;
    setLoading(true);
    setErr(null);
    setCopied(false);
    try {
      const res = await scalesApi.exportScale(token, scaleId);
      setText(res.text);
    } catch (e) {
      setText("");
      setErr(e instanceof ApiError ? e.detail : "Falha ao gerar exportação");
    } finally {
      setLoading(false);
    }
  }, [token, scaleId]);

  useEffect(() => {
    if (open && scaleId) void load();
    if (!open) {
      setText("");
      setErr(null);
      setCopied(false);
    }
  }, [open, scaleId, load]);

  async function handleCopy() {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setErr("Não foi possível copiar. Selecione o texto manualmente.");
    }
  }

  if (!open) return null;

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-[60] bg-black/70 backdrop-blur-sm"
        aria-label="Fechar"
        onClick={onClose}
      />
      <div className="fixed inset-x-4 top-[8vh] z-[70] mx-auto flex max-h-[84vh] w-full max-w-lg flex-col rounded-xl border border-zinc-700 bg-zinc-950 shadow-2xl sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2">
        <header className="flex items-start justify-between gap-3 border-b border-zinc-800 px-5 py-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">Exportar escala</p>
            <h2 className="mt-1 text-lg font-semibold text-zinc-50">{scaleTitle ?? "Escala publicada"}</h2>
            <p className="mt-1 text-xs text-zinc-500">Texto pronto para colar no WhatsApp</p>
          </div>
          <button type="button" onClick={onClose} className="rounded p-2 text-zinc-400 hover:bg-zinc-900 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && <p className="text-sm text-zinc-500">Gerando texto operacional…</p>}
          {err && (
            <p className="mb-3 rounded border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
              {err}
            </p>
          )}
          {!loading && text && (
            <textarea
              readOnly
              value={text}
              rows={18}
              className="w-full resize-none rounded-lg border border-zinc-800 bg-black/50 p-3 font-mono text-xs leading-relaxed text-zinc-200"
            />
          )}
        </div>

        <footer className="flex gap-2 border-t border-zinc-800 p-4">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-lg border border-zinc-700 py-2 text-sm text-zinc-400 hover:bg-zinc-900"
          >
            Fechar
          </button>
          <button
            type="button"
            disabled={!text || loading}
            onClick={() => void handleCopy()}
            className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-zinc-500 bg-zinc-100 py-2 text-sm font-medium text-zinc-900 disabled:opacity-40"
          >
            {copied ? (
              <>
                <Check className="h-4 w-4" />
                Copiado
              </>
            ) : (
              <>
                <Copy className="h-4 w-4" />
                Copiar
              </>
            )}
          </button>
        </footer>
      </div>
    </>
  );
}
