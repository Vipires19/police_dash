import { useCallback, useEffect, useMemo, useState } from "react";
import { Check, AlertTriangle, Circle, Rocket, RefreshCw, History, Copy } from "lucide-react";
import { Link } from "react-router-dom";
import { OperationalLayout } from "@/layouts/OperationalLayout";
import { useAuth } from "@/hooks/AuthContext";
import { ApiError } from "@/services/api";
import * as opApi from "@/services/operationalPublicationsApi";
import type {
  ChecklistItem,
  ChecklistItemLevel,
  OperationalPublicationCenterDay,
} from "@/types/operationalPublication";
import { SCALE_EDITOR_ROLES } from "@/types";

function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function levelIcon(level: ChecklistItemLevel) {
  if (level === "OK") return <Check className="h-4 w-4 text-emerald-400" />;
  if (level === "WARN") return <AlertTriangle className="h-4 w-4 text-amber-400" />;
  if (level === "ERROR") return <AlertTriangle className="h-4 w-4 text-red-400" />;
  return <Circle className="h-4 w-4 text-zinc-500" />;
}

function levelBadge(level: ChecklistItemLevel) {
  if (level === "OK") return "border-emerald-800/60 bg-emerald-950/40 text-emerald-200";
  if (level === "WARN") return "border-amber-800/60 bg-amber-950/30 text-amber-200";
  if (level === "ERROR") return "border-red-900/50 bg-red-950/40 text-red-200";
  return "border-zinc-700 bg-zinc-900/50 text-zinc-400";
}

function ChecklistCard({ item }: { item: ChecklistItem }) {
  return (
    <article className={`rounded-lg border p-4 ${levelBadge(item.level)}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] opacity-70">{item.title}</p>
          <p className="mt-2 text-sm leading-relaxed">{item.detail}</p>
        </div>
        <span className="mt-0.5 shrink-0">{levelIcon(item.level)}</span>
      </div>
    </article>
  );
}

export function OperationalPublicationPage() {
  const { token, user } = useAuth();
  const canEdit = user ? SCALE_EDITOR_ROLES.includes(user.role) : false;
  const [day, setDay] = useState(todayIso);
  const [center, setCenter] = useState<OperationalPublicationCenterDay | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [ackRisk, setAckRisk] = useState(false);
  const [reason, setReason] = useState("");
  const [copied, setCopied] = useState(false);

  const load = useCallback(async () => {
    if (!token || !canEdit) return;
    setErr(null);
    try {
      const c = await opApi.getPublicationCenter(token, day);
      setCenter(c);
    } catch (e) {
      setCenter(null);
      setErr(e instanceof ApiError ? e.detail : "Falha ao carregar centro de publicação");
    }
  }, [token, day, canEdit]);

  useEffect(() => {
    void load();
  }, [load]);

  const checklist = center?.checklist;
  const active = center?.active_publication;
  const message = active?.generated_message;

  const displayDate = useMemo(
    () =>
      new Date(day + "T12:00:00").toLocaleDateString("pt-BR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      }),
    [day],
  );

  async function handleConsolidate() {
    if (!token) return;
    setBusy(true);
    setErr(null);
    try {
      await opApi.createDraftByDate(token, day);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Falha ao consolidar");
    } finally {
      setBusy(false);
    }
  }

  async function handleValidate() {
    if (!token || !active) return;
    setBusy(true);
    setErr(null);
    try {
      await opApi.validatePublication(token, active.id);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Falha ao validar");
    } finally {
      setBusy(false);
    }
  }

  async function handlePublish() {
    if (!token || !active) return;
    setBusy(true);
    setErr(null);
    try {
      await opApi.publishPublication(token, active.id, {
        acknowledge_risks: ackRisk,
        reason: reason.trim() || null,
      });
      setAckRisk(false);
      setReason("");
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.detail : "Falha ao publicar");
    } finally {
      setBusy(false);
    }
  }

  async function handleCopy() {
    if (!message) return;
    try {
      await navigator.clipboard.writeText(message);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setErr("Não foi possível copiar a mensagem");
    }
  }

  if (!canEdit) {
    return (
      <OperationalLayout>
        <p className="text-sm text-zinc-400">Acesso restrito a N90 / ADMIN.</p>
      </OperationalLayout>
    );
  }

  return (
    <OperationalLayout>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-zinc-500">
            Documento oficial do serviço
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-zinc-50">Publicação Operacional</h1>
          <p className="mt-1 text-sm capitalize text-zinc-400">{displayDate}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <input
            type="date"
            value={day}
            onChange={(e) => setDay(e.target.value)}
            className="rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
          />
          <Link
            to="/publicacao-operacional/historico"
            className="inline-flex items-center gap-2 rounded border border-zinc-700 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-900"
          >
            <History className="h-4 w-4" />
            Histórico
          </Link>
        </div>
      </div>

      {err && (
        <p className="mb-4 rounded border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      {!center?.service_scale_id && (
        <div className="rounded-xl border border-amber-900/40 bg-amber-950/20 p-5 text-sm text-amber-100">
          Não há Escala Operacional para este dia. Crie a escala em{" "}
          <Link to="/escala-servico" className="underline">
            Escala de Serviço
          </Link>{" "}
          e depois consolide aqui.
        </div>
      )}

      {center?.service_scale_id && (
        <>
          <div className="mb-4 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleConsolidate()}
              className="inline-flex items-center gap-2 rounded border border-zinc-600 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 hover:bg-zinc-800 disabled:opacity-40"
            >
              <RefreshCw className="h-4 w-4" />
              {active ? "Reconsolidar" : "Consolidar Draft"}
            </button>
            {active && (
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleValidate()}
                className="rounded border border-sky-800/50 bg-sky-950/30 px-3 py-2 text-sm text-sky-200 disabled:opacity-40"
              >
                Validar
              </button>
            )}
            {active && (
              <span className="inline-flex items-center rounded border border-zinc-700 px-2 py-1 text-[11px] uppercase tracking-wider text-zinc-400">
                {active.status} · v{active.version} · Nº {active.publication_number}
              </span>
            )}
            {center.latest_published && (
              <span className="inline-flex items-center rounded border border-emerald-900/40 px-2 py-1 text-[11px] text-emerald-300/90">
                Última publicada: v{center.latest_published.version}
              </span>
            )}
          </div>

          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {(checklist?.items ?? []).map((item) => (
              <ChecklistCard key={item.key} item={item} />
            ))}
          </section>

          {message && (
            <section className="mt-6 rounded-xl border border-zinc-800 bg-black/30 p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">
                  Mensagem operacional (preview)
                </p>
                <button
                  type="button"
                  onClick={() => void handleCopy()}
                  className="inline-flex items-center gap-1 rounded border border-zinc-700 px-2 py-1 text-xs text-zinc-300"
                >
                  <Copy className="h-3 w-3" />
                  {copied ? "Copiado" : "Copiar"}
                </button>
              </div>
              <pre className="max-h-72 overflow-auto whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-zinc-200">
                {message}
              </pre>
            </section>
          )}

          <section className="mt-6 rounded-xl border border-zinc-800 bg-zinc-950/60 p-5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">Publicar</p>
            {(checklist?.has_warnings || checklist?.has_errors) && (
              <label className="mt-3 flex items-start gap-2 text-sm text-amber-200">
                <input
                  type="checkbox"
                  checked={ackRisk}
                  onChange={(e) => setAckRisk(e.target.checked)}
                  className="mt-1"
                />
                <span>
                  Assumo o risco e publico mesmo com inconsistências / avisos (auditoria registrada).
                </span>
              </label>
            )}
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Motivo da publicação / republicação (opcional)"
              className="mt-3 w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm"
            />
            <button
              type="button"
              disabled={busy || !active || !(checklist?.ready || ackRisk)}
              onClick={() => void handlePublish()}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-emerald-600 bg-emerald-600 py-3 text-sm font-semibold text-white disabled:opacity-40 sm:w-auto sm:px-8"
            >
              <Rocket className="h-4 w-4" />
              PUBLICAR ESCALA
            </button>
          </section>
        </>
      )}
    </OperationalLayout>
  );
}
