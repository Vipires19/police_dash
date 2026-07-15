import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Pencil, X } from "lucide-react";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as scalesApi from "@/services/serviceScalesApi";

interface Props {
  open: boolean;
  scaleId: number | null;
  scaleTitle?: string;
  initialDescription?: string | null;
  busy?: boolean;
  onClose: () => void;
  onPublish: () => void;
  onSaveObservations: (description: string | null) => Promise<void>;
}

export function ScalePublishPreviewModal({
  open,
  scaleId,
  scaleTitle,
  initialDescription,
  busy = false,
  onClose,
  onPublish,
  onSaveObservations,
}: Props) {
  const { token } = useAuth();
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [editingObs, setEditingObs] = useState(false);
  const [obsDraft, setObsDraft] = useState("");
  const [savingObs, setSavingObs] = useState(false);

  const loadPreview = useCallback(
    async (descriptionOverride?: string | null) => {
      if (!token || !scaleId) return;
      setLoading(true);
      setErr(null);
      try {
        const body =
          descriptionOverride !== undefined
            ? { description: descriptionOverride }
            : undefined;
        const res = await scalesApi.previewPublishScale(token, scaleId, body);
        setText(res.text);
        if (descriptionOverride === undefined) {
          setObsDraft(res.description ?? "");
        }
      } catch (e) {
        setText("");
        setErr(e instanceof ApiError ? e.detail : "Falha ao gerar preview da mensagem");
      } finally {
        setLoading(false);
      }
    },
    [token, scaleId],
  );

  useEffect(() => {
    if (open && scaleId) {
      setEditingObs(false);
      setObsDraft(initialDescription ?? "");
      setCopied(false);
      void loadPreview();
    }
    if (!open) {
      setText("");
      setErr(null);
      setCopied(false);
      setEditingObs(false);
    }
  }, [open, scaleId, initialDescription, loadPreview]);

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

  async function handleSaveObs() {
    setSavingObs(true);
    setErr(null);
    try {
      const next = obsDraft.trim() || null;
      await onSaveObservations(next);
      setEditingObs(false);
      await loadPreview(next);
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Falha ao salvar observações");
    } finally {
      setSavingObs(false);
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
        disabled={busy}
      />
      <div className="fixed inset-x-4 top-[6vh] z-[70] mx-auto flex max-h-[88vh] w-full max-w-lg flex-col rounded-xl border border-zinc-700 bg-zinc-950 shadow-2xl sm:inset-x-auto sm:left-1/2 sm:-translate-x-1/2">
        <header className="flex items-start justify-between gap-3 border-b border-zinc-800 px-5 py-4">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-zinc-500">Preview da publicação</p>
            <h2 className="mt-1 text-lg font-semibold text-zinc-50">{scaleTitle ?? "Escala"}</h2>
            <p className="mt-1 text-xs text-zinc-500">Mensagem gerada automaticamente — mesma que será publicada</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded p-2 text-zinc-400 hover:bg-zinc-900 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
          {loading && <p className="text-sm text-zinc-500">Montando mensagem a partir da escala…</p>}
          {err && (
            <p className="rounded border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">{err}</p>
          )}

          {!loading && text && (
            <div className="rounded-2xl border border-zinc-800 bg-[#0b141a] p-3 shadow-inner">
              <div className="mb-2 flex items-center gap-2 px-1">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-[10px] uppercase tracking-wider text-zinc-500">WhatsApp · prévia</span>
              </div>
              <pre className="whitespace-pre-wrap break-words rounded-xl bg-[#005c4b]/15 px-3 py-3 font-mono text-[11px] leading-relaxed text-zinc-100">
                {text}
              </pre>
            </div>
          )}

          {editingObs && (
            <label className="block text-[10px] uppercase tracking-wider text-zinc-500">
              Observações operacionais
              <textarea
                value={obsDraft}
                onChange={(e) => setObsDraft(e.target.value)}
                rows={4}
                placeholder={"• Apoio Operação Saturação.\n• QAP às 08:30."}
                className="mt-1 w-full resize-none rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 font-mono text-xs text-zinc-100"
              />
            </label>
          )}
        </div>

        <footer className="flex flex-col gap-2 border-t border-zinc-800 p-4">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!text || loading || busy}
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
                  📋 Copiar Mensagem
                </>
              )}
            </button>
            {!editingObs ? (
              <button
                type="button"
                disabled={busy || loading}
                onClick={() => setEditingObs(true)}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-zinc-700 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-40"
              >
                <Pencil className="h-4 w-4" />
                Editar Observações
              </button>
            ) : (
              <button
                type="button"
                disabled={savingObs || busy}
                onClick={() => void handleSaveObs()}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-sky-800/60 bg-sky-950/40 py-2 text-sm text-sky-200 disabled:opacity-40"
              >
                {savingObs ? "Salvando…" : "Atualizar preview"}
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={onClose}
              className="flex-1 rounded-lg border border-zinc-700 py-2 text-sm text-zinc-400 hover:bg-zinc-900"
            >
              Cancelar
            </button>
            <button
              type="button"
              disabled={busy || loading || !!err || !text}
              onClick={onPublish}
              className="flex-1 rounded-lg border border-emerald-700/60 bg-emerald-600 py-2 text-sm font-semibold text-white disabled:opacity-40"
            >
              {busy ? "Publicando…" : "Publicar"}
            </button>
          </div>
        </footer>
      </div>
    </>
  );
}
