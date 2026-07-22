import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError } from "@/services/api";
import * as dejemApi from "@/services/dejemApi";
import { listEfetivo } from "@/services/usersApi";
import {
  DEJEM_OFFER_EVENT_TYPE_LABELS,
  isDejemRedistributionPending,
  type DejemIncrementalPreview,
  type DejemOfferEvent,
  type DejemOfferEventType,
} from "@/types/dejem";

type ModalKind = "add" | "remove" | "history" | "redistribute" | "afterAdd" | null;

type Props = {
  token: string;
  campaignId: number;
  canRedistribute: boolean;
  preview: DejemIncrementalPreview | null;
  totalSlots: number;
  distributedSlots: number;
  availableBalance: number;
  busy: boolean;
  onBusy: (v: boolean) => void;
  onError: (msg: string | null) => void;
  onMsg: (msg: string | null) => void;
  /** Recarrega preview, alocações, mês e indicadores no pai. */
  onRefresh: () => Promise<void>;
};

export function DejemVacancyManagement({
  token,
  campaignId,
  canRedistribute,
  preview,
  totalSlots,
  distributedSlots,
  availableBalance,
  busy,
  onBusy,
  onError,
  onMsg,
  onRefresh,
}: Props) {
  const [modal, setModal] = useState<ModalKind>(null);
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState("");
  const [history, setHistory] = useState<DejemOfferEvent[]>([]);
  const [userLabels, setUserLabels] = useState<Record<number, string>>({});
  const [pendingAddedQty, setPendingAddedQty] = useState(0);

  const redistributionPending = isDejemRedistributionPending(preview);
  const showRedistributeBtn = canRedistribute && redistributionPending;

  const loadUserLabels = useCallback(async () => {
    try {
      const users = await listEfetivo(token);
      const map: Record<number, string> = {};
      for (const u of users) {
        map[u.id] = [u.patente, u.nome_guerra].filter(Boolean).join(" ") || `Usuário #${u.id}`;
      }
      setUserLabels(map);
    } catch {
      /* histórico ainda funciona com id */
    }
  }, [token]);

  useEffect(() => {
    void loadUserLabels();
  }, [loadUserLabels]);

  const openOfferModal = (kind: "add" | "remove") => {
    setQuantity(1);
    setReason("");
    setModal(kind);
  };

  const openHistory = async () => {
    onBusy(true);
    onError(null);
    try {
      const rows = await dejemApi.listDejemOfferHistory(token, campaignId);
      setHistory(rows);
      setModal("history");
    } catch (e) {
      onError(e instanceof ApiError ? e.detail : "Erro ao carregar histórico de vagas");
    } finally {
      onBusy(false);
    }
  };

  const openRedistribute = () => {
    setReason("");
    setModal("redistribute");
  };

  const submitOffer = async (eventType: DejemOfferEventType) => {
    if (quantity <= 0) {
      onError("Informe uma quantidade maior que zero.");
      return;
    }
    onBusy(true);
    onError(null);
    onMsg(null);
    try {
      await dejemApi.createDejemOfferEvent(token, {
        campaign_id: campaignId,
        event_type: eventType,
        quantity,
        reason: reason.trim() || null,
      });
      await onRefresh();
      if (eventType === "INCREASE" && canRedistribute) {
        setPendingAddedQty(quantity);
        setModal("afterAdd");
      } else {
        setModal(null);
        onMsg(
          eventType === "INCREASE"
            ? `${quantity} vaga(s) adicionada(s) via OfferEvent.`
            : `${quantity} vaga(s) removida(s) via OfferEvent.`,
        );
      }
    } catch (e) {
      onError(e instanceof ApiError ? e.detail : "Erro ao registrar evento de vagas");
    } finally {
      onBusy(false);
    }
  };

  const confirmRedistribute = async () => {
    onBusy(true);
    onError(null);
    onMsg(null);
    try {
      const useRemainingOnly =
        preview != null &&
        preview.unaccounted_slots <= 0 &&
        preview.undistributed_slots > 0 &&
        preview.interested_without_allocation <= 0;

      const result = useRemainingOnly
        ? await dejemApi.redistributeDejemRemaining(token, {
            campaign_id: campaignId,
            reason: reason.trim() || null,
          })
        : await dejemApi.runDejemIncremental(token, {
            campaign_id: campaignId,
            reason: reason.trim() || null,
          });

      await onRefresh();
      setModal(null);
      setPendingAddedQty(0);
      onMsg(
        result.message ||
          (result.noop
            ? "Nada a redistribuir (estado já consistente)."
            : `Redistribuição concluída: ${result.slots_processed} vaga(s) processada(s), ${result.credits_created} crédito(s) criado(s).`),
      );
    } catch (e) {
      onError(e instanceof ApiError ? e.detail : "Erro ao redistribuir vagas");
    } finally {
      onBusy(false);
    }
  };

  const eventTypeLabel = (t: DejemOfferEventType) => DEJEM_OFFER_EVENT_TYPE_LABELS[t] ?? t;

  const redistributeSummary = useMemo(() => {
    if (!preview) {
      return {
        novas: 0,
        interessados: 0,
        saldo: availableBalance,
        quantidade: 0,
      };
    }
    return {
      novas: Math.max(0, preview.unaccounted_slots),
      interessados: preview.interested_without_allocation,
      saldo: Math.max(0, preview.available_slots - preview.distributed_slots),
      quantidade: preview.would_distribute,
    };
  }, [preview, availableBalance]);

  return (
    <>
      <section className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-zinc-300">
            Gestão de Vagas
          </h2>
          {canRedistribute && (
            <span
              className={[
                "rounded-md px-2.5 py-1 text-xs font-medium ring-1",
                redistributionPending
                  ? "bg-amber-950/50 text-amber-200 ring-amber-800/60"
                  : "bg-emerald-950/40 text-emerald-200 ring-emerald-800/50",
              ].join(" ")}
            >
              {redistributionPending ? "Redistribuição pendente" : "Distribuição atualizada"}
            </span>
          )}
        </div>

        <dl className="mt-4 grid gap-3 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-zinc-500">Total de vagas</dt>
            <dd className="mt-0.5 text-lg tabular-nums text-zinc-100">{totalSlots}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Vagas distribuídas</dt>
            <dd className="mt-0.5 text-lg tabular-nums text-zinc-100">{distributedSlots}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Saldo disponível</dt>
            <dd className="mt-0.5 text-lg tabular-nums text-zinc-100">{availableBalance}</dd>
          </div>
        </dl>

        <div className="mt-5 flex flex-wrap gap-2 border-t border-zinc-800 pt-4">
          <button
            type="button"
            disabled={busy}
            onClick={() => openOfferModal("add")}
            className="rounded-md border border-emerald-800/70 px-3 py-1.5 text-xs text-emerald-200 hover:bg-emerald-950/40 disabled:opacity-50"
          >
            + Adicionar vagas
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => openOfferModal("remove")}
            className="rounded-md border border-red-900/60 px-3 py-1.5 text-xs text-red-200 hover:bg-red-950/30 disabled:opacity-50"
          >
            − Remover vagas
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void openHistory()}
            className="rounded-md border border-zinc-600 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
          >
            Histórico
          </button>
          {showRedistributeBtn && (
            <button
              type="button"
              disabled={busy}
              onClick={openRedistribute}
              className="rounded-md border border-sky-800/70 px-3 py-1.5 text-xs text-sky-200 hover:bg-sky-950/40 disabled:opacity-50"
            >
              Redistribuir vagas
            </button>
          )}
        </div>
      </section>

      {(modal === "add" || modal === "remove") && (
        <ModalShell
          title={modal === "add" ? "Adicionar vagas" : "Remover vagas"}
          onClose={() => !busy && setModal(null)}
        >
          <label className="block text-sm">
            <span className="mb-1 block text-zinc-500">Quantidade</span>
            <input
              type="number"
              min={1}
              value={quantity}
              onChange={(e) => setQuantity(Math.max(1, Number(e.target.value) || 1))}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <label className="mt-3 block text-sm">
            <span className="mb-1 block text-zinc-500">Motivo</span>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
              placeholder="Opcional"
            />
          </label>
          <p className="mt-3 text-xs text-zinc-500">
            A alteração é registrada como OfferEvent (
            {modal === "add" ? "INCREASE" : "DECREASE"}). A quantidade da campanha não é editada
            diretamente.
          </p>
          <ModalActions
            busy={busy}
            cancelLabel="Cancelar"
            confirmLabel="Confirmar"
            onCancel={() => setModal(null)}
            onConfirm={() => void submitOffer(modal === "add" ? "INCREASE" : "DECREASE")}
          />
        </ModalShell>
      )}

      {modal === "history" && (
        <ModalShell title="Histórico de vagas" onClose={() => !busy && setModal(null)} wide>
          {history.length === 0 ? (
            <p className="text-sm text-zinc-500">Nenhum OfferEvent registrado.</p>
          ) : (
            <div className="max-h-[60vh] overflow-auto rounded-lg border border-zinc-800">
              <table className="min-w-full text-left text-sm">
                <thead className="sticky top-0 border-b border-zinc-800 bg-zinc-900 text-xs uppercase tracking-wider text-zinc-500">
                  <tr>
                    <th className="px-3 py-2 font-medium">Data</th>
                    <th className="px-3 py-2 font-medium">Usuário</th>
                    <th className="px-3 py-2 font-medium">Tipo</th>
                    <th className="px-3 py-2 font-medium">Qtd.</th>
                    <th className="px-3 py-2 font-medium">Motivo</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((ev) => (
                    <tr key={ev.id} className="border-b border-zinc-900/80">
                      <td className="px-3 py-2 whitespace-nowrap text-zinc-400">
                        {new Date(ev.created_at).toLocaleString("pt-BR")}
                      </td>
                      <td className="px-3 py-2 text-zinc-200">
                        {userLabels[ev.created_by] ?? `Usuário #${ev.created_by}`}
                      </td>
                      <td className="px-3 py-2 text-zinc-300">{eventTypeLabel(ev.event_type)}</td>
                      <td className="px-3 py-2 tabular-nums text-zinc-100">{ev.quantity}</td>
                      <td className="px-3 py-2 text-zinc-400">{ev.reason || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={() => setModal(null)}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900"
            >
              Fechar
            </button>
          </div>
        </ModalShell>
      )}

      {modal === "redistribute" && (
        <ModalShell title="Redistribuir vagas" onClose={() => !busy && setModal(null)}>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-400">Novas vagas</dt>
              <dd className="tabular-nums text-zinc-100">{redistributeSummary.novas}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-400">Interessados sem alocação</dt>
              <dd className="tabular-nums text-zinc-100">{redistributeSummary.interessados}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-zinc-400">Saldo atual</dt>
              <dd className="tabular-nums text-zinc-100">{redistributeSummary.saldo}</dd>
            </div>
            <div className="flex justify-between gap-4 border-t border-zinc-800 pt-2">
              <dt className="text-zinc-400">Quantidade a redistribuir</dt>
              <dd className="tabular-nums text-zinc-100">{redistributeSummary.quantidade}</dd>
            </div>
          </dl>
          <label className="mt-4 block text-sm">
            <span className="mb-1 block text-zinc-500">Motivo (opcional)</span>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-100"
            />
          </label>
          <ModalActions
            busy={busy}
            cancelLabel="Cancelar"
            confirmLabel={busy ? "Redistribuindo…" : "Confirmar redistribuição"}
            onCancel={() => setModal(null)}
            onConfirm={() => void confirmRedistribute()}
          />
        </ModalShell>
      )}

      {modal === "afterAdd" && (
        <ModalShell title="Vagas adicionadas" onClose={() => !busy && setModal(null)}>
          <p className="text-sm text-zinc-300">
            Foram adicionadas {pendingAddedQty} vaga{pendingAddedQty === 1 ? "" : "s"}.
          </p>
          <p className="mt-2 text-sm text-zinc-400">Deseja redistribuí-las agora?</p>
          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setModal(null);
                onMsg(
                  `${pendingAddedQty} vaga(s) adicionada(s). Redistribuição pendente.`,
                );
              }}
              className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
            >
              Depois
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setReason("");
                setModal("redistribute");
              }}
              className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
            >
              Redistribuir
            </button>
          </div>
        </ModalShell>
      )}
    </>
  );
}

function ModalShell({
  title,
  onClose,
  children,
  wide,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div
        className={[
          "w-full rounded-xl border border-zinc-700 bg-zinc-950 p-6 shadow-xl",
          wide ? "max-w-3xl" : "max-w-md",
        ].join(" ")}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-lg font-semibold text-zinc-50">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-zinc-500 hover:text-zinc-300"
            aria-label="Fechar"
          >
            ×
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}

function ModalActions({
  busy,
  cancelLabel,
  confirmLabel,
  onCancel,
  onConfirm,
}: {
  busy: boolean;
  cancelLabel: string;
  confirmLabel: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div className="mt-6 flex justify-end gap-3">
      <button
        type="button"
        disabled={busy}
        onClick={onCancel}
        className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 hover:bg-zinc-900 disabled:opacity-50"
      >
        {cancelLabel}
      </button>
      <button
        type="button"
        disabled={busy}
        onClick={onConfirm}
        className="rounded-lg bg-zinc-100 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-white disabled:opacity-50"
      >
        {confirmLabel}
      </button>
    </div>
  );
}
